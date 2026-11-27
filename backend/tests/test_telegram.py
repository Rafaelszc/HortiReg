"""Testes do bot do Telegram (webhook, fluxo de pedido texto/áudio, callbacks e rotas admin)."""

import itertools

import pytest
from sqlalchemy import func, select

from app.config import settings
from app.models import Pedido, StatusPedido
from app.services import telegram
from tests.conftest import rodar

_update_ids = itertools.count(1000)
CHAT_ID = 123456789


def _update_texto(texto: str, chat_id: int = CHAT_ID, update_id: int | None = None, chat_type: str = "private") -> dict:
    return {
        "update_id": update_id if update_id is not None else next(_update_ids),
        "message": {
            "message_id": 1,
            "from": {"id": chat_id, "is_bot": False, "first_name": "Maria", "last_name": "Silva"},
            "chat": {"id": chat_id, "type": chat_type},
            "text": texto,
        },
    }


def _update_voz(
    duracao: int = 20,
    mime_type: str = "audio/ogg",
    file_id: str = "file-voz-1",
    chat_id: int = CHAT_ID,
) -> dict:
    return {
        "update_id": next(_update_ids),
        "message": {
            "message_id": 2,
            "from": {"id": chat_id, "is_bot": False, "first_name": "Maria"},
            "chat": {"id": chat_id, "type": "private"},
            "voice": {"file_id": file_id, "duration": duracao, "mime_type": mime_type},
        },
    }


def _update_callback(data: str, chat_id: int = CHAT_ID, callback_id: str = "cb-1") -> dict:
    return {
        "update_id": next(_update_ids),
        "callback_query": {
            "id": callback_id,
            "from": {"id": chat_id, "is_bot": False, "first_name": "Maria"},
            "message": {"message_id": 10, "chat": {"id": chat_id, "type": "private"}},
            "data": data,
        },
    }


def _ultimo_pedido() -> Pedido | None:
    return rodar(lambda s: s.scalar(select(Pedido).order_by(Pedido.id.desc())))


def _total_pedidos() -> int:
    return rodar(lambda s: s.scalar(select(func.count()).select_from(Pedido)))


def test_webhook_secret_exigido(client, catalogo, telegram_fake, llm_fake, monkeypatch):
    monkeypatch.setattr(settings, "telegram_webhook_secret", "segredo-tg")
    llm_fake["responder"](("tomate", 2, "kg"))

    r_sem = client.post("/webhook/telegram", json=_update_texto("quero 2 kg de tomate"))
    assert r_sem.status_code == 401
    assert _total_pedidos() == 0

    r_errado = client.post(
        "/webhook/telegram",
        json=_update_texto("quero 2 kg de tomate"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "errado"},
    )
    assert r_errado.status_code == 401

    r_ok = client.post(
        "/webhook/telegram",
        json=_update_texto("quero 2 kg de tomate"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "segredo-tg"},
    )
    assert r_ok.status_code == 200
    assert _total_pedidos() == 1


def test_webhook_ignora_update_sem_mensagem_e_grupo(client, telegram_fake, llm_fake):
    r_vazio = client.post("/webhook/telegram", json={"update_id": 1})
    assert r_vazio.status_code == 200
    assert r_vazio.json() == {"ignored": True}

    r_grupo = client.post("/webhook/telegram", json=_update_texto("oi", chat_type="group"))
    assert r_grupo.status_code == 200
    assert telegram_fake["enviadas"] == []
    assert llm_fake["chamadas"] == 0


def test_comando_start_boas_vindas(client, telegram_fake):
    r = client.post("/webhook/telegram", json=_update_texto("/start"))
    assert r.status_code == 200
    assert len(telegram_fake["enviadas"]) == 1
    chat_id, texto, _ = telegram_fake["enviadas"][0]
    assert chat_id == CHAT_ID
    assert "HortiReg" in texto
    assert "@HortRegBot" in texto


def test_pedido_texto_confirmar_por_callback_e_idempotencia(client, catalogo, telegram_fake, llm_fake):
    llm_fake["responder"](("tomate", 2, "kg"), ("banana", 1, "caixa"))
    uid = 999001

    r1 = client.post("/webhook/telegram", json=_update_texto("2 kg de tomate e 1 caixa de banana", update_id=uid))
    r2 = client.post("/webhook/telegram", json=_update_texto("2 kg de tomate e 1 caixa de banana", update_id=uid))
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert _total_pedidos() == 1

    pedido = _ultimo_pedido()
    assert pedido is not None
    assert pedido.status == StatusPedido.AGUARDANDO_CONFIRMACAO
    _, texto_resumo, markup = telegram_fake["enviadas"][0]
    assert "tomate" in texto_resumo
    assert "R$ 45,00" in texto_resumo
    assert markup is not None and "inline_keyboard" in markup

    r_cb = client.post("/webhook/telegram", json=_update_callback("confirmar"))
    assert r_cb.status_code == 200
    assert telegram_fake["callbacks"] == [("cb-1", None)]
    assert _ultimo_pedido().status == StatusPedido.CONFIRMADO


def test_pedido_pendente_resposta_invalida_e_cancelamento(client, catalogo, telegram_fake, llm_fake):
    llm_fake["responder"](("tomate", 1, "kg"))
    client.post("/webhook/telegram", json=_update_texto("1 kg de tomate"))

    llm_fake["responder"]()
    client.post("/webhook/telegram", json=_update_texto("qualquer coisa"))
    assert "Não entendi" in telegram_fake["enviadas"][-1][1]
    assert _ultimo_pedido().status == StatusPedido.AGUARDANDO_CONFIRMACAO

    client.post("/webhook/telegram", json=_update_texto("3"))
    assert _ultimo_pedido().status == StatusPedido.CANCELADO
    assert "cancelado" in telegram_fake["enviadas"][-1][1].lower()


def test_pedido_pendente_adiciona_itens_por_texto_e_audio(client, catalogo, telegram_fake, llm_fake):
    llm_fake["responder"](("tomate", 2, "kg"))
    client.post("/webhook/telegram", json=_update_texto("quero 2 kg de tomate"))
    pedido_id = _ultimo_pedido().id

    # Envia mais itens por texto no estado AGUARDANDO_CONFIRMACAO (um novo + soma no existente)
    llm_fake["responder"](("tomate", 1, "kg"), ("banana", 1, "caixa"))
    client.post("/webhook/telegram", json=_update_texto("esqueci, bota mais 1 kg de tomate e 1 caixa de banana"))

    assert _total_pedidos() == 1
    pedido = _ultimo_pedido()
    assert pedido.id == pedido_id
    assert pedido.status == StatusPedido.AGUARDANDO_CONFIRMACAO
    itens_map = {i.nome: float(i.quantidade) for i in pedido.itens}
    assert itens_map == {"tomate": 3.0, "banana": 1.0}
    assert "Adicionei ao seu pedido" in telegram_fake["enviadas"][-1][1]

    # Envia mais itens por áudio no estado AGUARDANDO_CONFIRMACAO
    llm_fake["responder"](("coentro", 2, "maço"))
    client.post("/webhook/telegram", json=_update_voz(duracao=10, mime_type="audio/ogg"))

    assert _total_pedidos() == 1
    itens_map = {i.nome: float(i.quantidade) for i in _ultimo_pedido().itens}
    assert itens_map == {"tomate": 3.0, "banana": 1.0, "coentro": 2.0}


def test_comandos_gemini_substituir_mantendo_id_remover_e_confirmar(client, catalogo, telegram_fake, llm_fake):
    from app.schemas.pedido import AcaoPedido, ItemExtraido, PedidoExtraido

    llm_fake["responder"](("tomate", 2, "kg"), ("banana", 1, "caixa"))
    client.post("/webhook/telegram", json=_update_texto("2 kg de tomate e 1 caixa de banana"))
    pedido_id = _ultimo_pedido().id

    # Comando SUBSTITUIR (ex.: áudio dizendo "cancela esse e faz outro com 3 kg de batata") mantém o mesmo pedido_id
    llm_fake["resposta"] = PedidoExtraido(
        acao=AcaoPedido.SUBSTITUIR,
        itens=[ItemExtraido(nome="batata", quantidade=3, unidade="kg")],
    )
    client.post("/webhook/telegram", json=_update_voz(duracao=12, mime_type="audio/ogg"))
    assert _total_pedidos() == 1
    pedido = _ultimo_pedido()
    assert pedido.id == pedido_id
    assert [(i.nome, float(i.quantidade)) for i in pedido.itens] == [("batata", 3.0)]
    assert "Substituí os itens" in telegram_fake["enviadas"][-1][1]

    # Comando misto: remove batata e adiciona 2 kg de tomate
    llm_fake["resposta"] = PedidoExtraido(
        acao=AcaoPedido.ADICIONAR,
        itens=[ItemExtraido(nome="tomate", quantidade=2, unidade="kg")],
        itens_remover=["batata"],
    )
    client.post("/webhook/telegram", json=_update_texto("tira a batata e bota 2 kg de tomate"))
    assert _ultimo_pedido().id == pedido_id
    assert [(i.nome, float(i.quantidade)) for i in _ultimo_pedido().itens] == [("tomate", 2.0)]

    # Comando CONFIRMAR via áudio
    llm_fake["resposta"] = PedidoExtraido(acao=AcaoPedido.CONFIRMAR)
    client.post("/webhook/telegram", json=_update_voz(duracao=5, mime_type="audio/ogg"))
    assert _ultimo_pedido().id == pedido_id
    assert _ultimo_pedido().status == StatusPedido.CONFIRMADO


def test_pedido_sem_pendente_e_falha_ia(client, telegram_fake, llm_fake):
    client.post("/webhook/telegram", json=_update_texto("1"))
    assert "nenhum pedido" in telegram_fake["enviadas"][-1][1].lower()

    llm_fake["erro"] = RuntimeError("Gemini fora do ar")
    client.post("/webhook/telegram", json=_update_texto("quero 2 kg de tomate"))
    assert "Não consegui processar" in telegram_fake["enviadas"][-1][1]
    assert _total_pedidos() == 0


def test_pedido_por_audio_valido_e_rejeicoes(client, catalogo, telegram_fake, llm_fake):
    llm_fake["responder"](("tomate", 3, "kg"))

    # Formato inválido
    client.post("/webhook/telegram", json=_update_voz(duracao=10, mime_type="audio/flac"))
    assert telegram_fake["audio_baixados"] == 0
    assert "tipo de áudio" in telegram_fake["enviadas"][-1][1]

    # Áudio longo demais
    client.post("/webhook/telegram", json=_update_voz(duracao=120, mime_type="audio/ogg"))
    assert telegram_fake["audio_baixados"] == 0
    assert "longo demais" in telegram_fake["enviadas"][-1][1]

    # Áudio válido
    client.post("/webhook/telegram", json=_update_voz(duracao=15, mime_type="audio/ogg"))
    assert telegram_fake["audio_baixados"] == 1
    assert _total_pedidos() == 1


def test_rotas_admin_telegram(client, token, monkeypatch):
    r_unauth = client.get("/telegram/info")
    assert r_unauth.status_code == 401

    r_info = client.get("/telegram/info", headers=token)
    assert r_info.status_code == 200
    assert r_info.json()["nome"] == "HortiReg"
    assert r_info.json()["username"] == "HortRegBot"

    # Sem URL configurada -> 400
    monkeypatch.setattr(settings, "telegram_webhook_url", "")
    r_sem_url = client.post("/telegram/webhook", headers=token)
    assert r_sem_url.status_code == 400

    # Sem token -> RuntimeError vira 400
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    r_sem_token = client.get("/telegram/webhook", headers=token)
    assert r_sem_token.status_code == 400

    # Com serviço mockado -> 200
    async def _ok(*args, **kwargs):
        return {"ok": True}

    monkeypatch.setattr(telegram, "configurar_webhook", _ok)
    monkeypatch.setattr(telegram, "info_webhook", _ok)
    monkeypatch.setattr(telegram, "remover_webhook", _ok)

    r_set = client.post("/telegram/webhook", json={"url": "https://exemplo.com/webhook/telegram"}, headers=token)
    assert r_set.status_code == 200
    assert client.get("/telegram/webhook", headers=token).status_code == 200
    assert client.delete("/telegram/webhook", headers=token).status_code == 200


def test_service_telegram_sem_token_falha(monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        telegram._token()


def test_polling_processa_updates_e_avanca_offset(monkeypatch):
    import asyncio

    from app.services import telegram_bot

    offsets: list[int | None] = []
    processados: list[dict] = []

    async def _remover():
        return {"ok": True}

    async def _buscar(offset=None, timeout=25):
        offsets.append(offset)
        if offset is None:
            return [{"update_id": 50, "message": {"text": "/start"}}]
        await asyncio.sleep(0)
        raise asyncio.CancelledError

    async def _processar(update):
        processados.append(update)

    monkeypatch.setattr(telegram, "remover_webhook", _remover)
    monkeypatch.setattr(telegram, "buscar_updates", _buscar)
    monkeypatch.setattr(telegram_bot, "processar_update", _processar)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(telegram_bot.rodar_polling())

    assert offsets == [None, 51]
    assert len(processados) == 1
    assert processados[0]["update_id"] == 50


def test_fluxo_estados_editar_e_gerenciar_confirmado(client, catalogo, telegram_fake, llm_fake):
    from app.services import estados
    from app.services.estados import EstadoConversa

    assert estados.obter_estado(CHAT_ID) == EstadoConversa.ESPERANDO

    # Clica em "Fazer pedido" -> FAZENDO_PEDIDO
    client.post("/webhook/telegram", json=_update_callback("novo_pedido", callback_id="cb-novo"))
    assert estados.obter_estado(CHAT_ID) == EstadoConversa.FAZENDO_PEDIDO

    # Envia pedido -> AGUARDANDO_CONFIRMACAO
    llm_fake["responder"](("tomate", 2, "kg"))
    client.post("/webhook/telegram", json=_update_texto("quero 2 kg de tomate"))
    assert estados.obter_estado(CHAT_ID) == EstadoConversa.AGUARDANDO_CONFIRMACAO
    pedido_id = _ultimo_pedido().id

    # Clica em Editar -> EDITANDO
    client.post("/webhook/telegram", json=_update_callback("corrigir", callback_id="cb-edit"))
    assert estados.obter_estado(CHAT_ID) == EstadoConversa.EDITANDO

    # Envia itens atualizados -> atualiza o mesmo pedido e volta para AGUARDANDO_CONFIRMACAO
    llm_fake["responder"](("banana", 3, "caixa"))
    client.post("/webhook/telegram", json=_update_texto("na verdade quero 3 caixas de banana"))
    assert estados.obter_estado(CHAT_ID) == EstadoConversa.AGUARDANDO_CONFIRMACAO
    assert _total_pedidos() == 1
    atualizado = _ultimo_pedido()
    assert atualizado.id == pedido_id
    assert atualizado.itens[0].nome == "banana"

    # Confirma -> PEDIDO_CONFIRMADO
    client.post("/webhook/telegram", json=_update_callback("confirmar", callback_id="cb-conf"))
    assert estados.obter_estado(CHAT_ID) == EstadoConversa.PEDIDO_CONFIRMADO
    assert _ultimo_pedido().status == StatusPedido.CONFIRMADO

    # Edita pedido confirmado e cancela edição -> volta para PEDIDO_CONFIRMADO
    client.post("/webhook/telegram", json=_update_callback("editar_pedido", callback_id="cb-edit2"))
    assert estados.obter_estado(CHAT_ID) == EstadoConversa.EDITANDO
    client.post("/webhook/telegram", json=_update_callback("cancelar_edicao", callback_id="cb-cancel-edit"))
    assert estados.obter_estado(CHAT_ID) == EstadoConversa.PEDIDO_CONFIRMADO

    # Cancela pedido confirmado -> volta para ESPERANDO
    client.post("/webhook/telegram", json=_update_callback("cancelar_pedido", callback_id="cb-cancel-conf"))
    assert estados.obter_estado(CHAT_ID) == EstadoConversa.ESPERANDO
    assert _ultimo_pedido().status == StatusPedido.CANCELADO


def test_timer_inatividade_expira_sessao_e_volta_para_esperando():
    import asyncio

    from app.services import estados
    from app.services.estados import EstadoConversa

    expirados: list[tuple[int, int | None]] = []

    async def _on_timeout(chat_id: int, pedido_id: int | None) -> None:
        expirados.append((chat_id, pedido_id))

    async def _rodar():
        estados.definir(
            CHAT_ID,
            EstadoConversa.AGUARDANDO_CONFIRMACAO,
            pedido_id=42,
            on_timeout=_on_timeout,
            timeout_segundos=0.05,
        )
        assert estados.obter_estado(CHAT_ID) == EstadoConversa.AGUARDANDO_CONFIRMACAO
        await asyncio.sleep(0.12)
        assert estados.obter_estado(CHAT_ID) == EstadoConversa.ESPERANDO
        assert expirados == [(CHAT_ID, 42)]

    asyncio.run(_rodar())
