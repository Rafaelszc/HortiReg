"""Lógica de atendimento de pedidos via Telegram (HortiReg / @HortRegBot)."""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import SessionLocal
from app.models import Cliente, ItemPedido, MensagemProcessada, Pedido, StatusPedido
from app.schemas.pedido import PedidoExtraido
from app.services import audio, catalogo, expiracao, llm, telegram

log = logging.getLogger("sgv.telegram")

# Resposta ao resumo do pedido (US-08): 1-Confirmar, 2-Corrigir, 3-Cancelar
OPCOES = {
    **dict.fromkeys(("1", "sim", "s", "confirmo", "confirmar", "ok", "isso"), "confirmar"),
    **dict.fromkeys(("2", "corrigir"), "corrigir"),
    **dict.fromkeys(("3", "nao", "não", "n", "cancelar", "cancela"), "cancelar"),
}
TECLADO_OPCOES = {
    "inline_keyboard": [
        [
            {"text": "✅ Confirmar", "callback_data": "confirmar"},
            {"text": "✏️ Corrigir", "callback_data": "corrigir"},
            {"text": "❌ Cancelar", "callback_data": "cancelar"},
        ]
    ]
}
MSG_OPCOES = "Responda 1 para confirmar, 2 para corrigir ou 3 para cancelar (ou use os botões abaixo)."
EXEMPLO = 'Exemplo: "quero 2 kg de tomate e 1 caixa de banana".'
MSG_BOAS_VINDAS = (
    "Olá! Bem-vindo ao {nome} (@{username}) 🥬🍅\n"
    "Envie seu pedido por texto ou áudio que eu monto o resumo para você confirmar.\n"
    + EXEMPLO
)
MSG_JA_EXPIROU = (
    "O pedido #{id} expirou e não pode mais ser confirmado. "
    "Quer refazer? É só mandar o pedido de novo, por texto ou áudio."
)
MSG_SEM_ITENS = f"Não consegui entender os itens do pedido. Pode repetir? 🙏\n{EXEMPLO}"
MSG_AUDIO_LONGO = (
    "Seu áudio ficou longo demais (o limite é de {limite} segundos). "
    "Pode mandar um áudio mais curto ou escrever o pedido em texto? 🙏\n" + EXEMPLO
)
MSG_AUDIO_FORMATO = (
    "Não consegui abrir esse tipo de áudio. "
    "Pode gravar uma mensagem de voz pelo Telegram ou escrever o pedido em texto? 🙏\n" + EXEMPLO
)
MSG_AUDIO_INCOMPREENDIDO = (
    "Não consegui entender seu áudio. "
    "Pode gravar de novo, mais curto e perto do celular, ou escrever o pedido em texto? 🙏\n" + EXEMPLO
)
MSG_IA_FALHA = f"Não consegui processar seu pedido agora. Pode mandar de novo daqui a pouco? 🙏\n{EXEMPLO}"
MSG_AUDIO_FALHA = (
    "Não consegui ouvir seu áudio agora. Pode mandar de novo daqui a pouco ou escrever o pedido em texto? 🙏\n"
    + EXEMPLO
)


async def processar_update(update: dict) -> None:
    """Processa um update recebido pelo webhook do Telegram."""
    try:
        update_id = update.get("update_id")
        if "callback_query" in update:
            await _processar_callback(update["callback_query"], update_id)
            return

        message = update.get("message")
        if not isinstance(message, dict):
            return
        await _processar_mensagem(message, update_id)
    except Exception:
        log.exception("Erro ao processar update do Telegram")


async def rodar_polling() -> None:
    """Loop de long polling (getUpdates) para receber mensagens do Telegram sem webhook público."""
    try:
        await telegram.remover_webhook()
    except Exception:
        log.warning("Não foi possível remover webhook anterior antes do polling", exc_info=True)

    log.info("Iniciando long polling do Telegram (@%s)", settings.telegram_bot_username)
    offset: int | None = None
    while True:
        try:
            updates = await telegram.buscar_updates(offset=offset)
            for update in updates:
                if "update_id" in update:
                    offset = update["update_id"] + 1
                await processar_update(update)
        except asyncio.CancelledError:
            log.info("Long polling do Telegram encerrado")
            raise
        except Exception:
            log.exception("Erro no long polling do Telegram; tentando novamente em 5s")
            await asyncio.sleep(5)


async def _processar_callback(callback: dict, update_id: int | None) -> None:
    msg = callback.get("message") or {}
    chat = msg.get("chat") or {}
    if chat.get("type") != "private" or chat.get("id") is None:
        return

    chat_id = chat["id"]
    callback_id = callback.get("id")
    if callback_id:
        await telegram.responder_callback(callback_id)

    opcao = OPCOES.get((callback.get("data") or "").strip().lower())
    if not opcao:
        return

    async with SessionLocal() as session:
        if await _repetida(session, update_id):
            log.info("Update %s do Telegram já processado; ignorado", update_id)
            return
        cliente = await _obter_cliente(session, chat_id, _nome_usuario(callback.get("from")))
        await expiracao.expirar_pendentes(session)
        pendente = await _pedido_pendente(session, cliente)
        await _tratar_resposta(session, cliente, chat_id, pendente, opcao)


async def _processar_mensagem(message: dict, update_id: int | None) -> None:
    remetente = message.get("from") or {}
    if remetente.get("is_bot"):
        return

    chat = message.get("chat") or {}
    if chat.get("type") != "private" or chat.get("id") is None:
        return

    chat_id = chat["id"]
    texto = (message.get("text") or "").strip()
    midia = message.get("voice") or message.get("audio")

    async with SessionLocal() as session:
        if await _repetida(session, update_id):
            log.info("Update %s do Telegram já processado; ignorado", update_id)
            return

        if texto and texto.split()[0].lower().split("@")[0] in ("/start", "/ajuda", "/help"):
            await telegram.enviar_texto(
                chat_id,
                MSG_BOAS_VINDAS.format(nome=settings.telegram_bot_name, username=settings.telegram_bot_username),
            )
            return

        cliente = await _obter_cliente(session, chat_id, _nome_usuario(remetente))

        # Etapa 2: com pedido pendente, só 1, 2 ou 3 valem; nada vira pedido novo
        await expiracao.expirar_pendentes(session)
        opcao = OPCOES.get(texto.lower()) if texto else None
        pendente = await _pedido_pendente(session, cliente)
        if opcao or pendente:
            await _tratar_resposta(session, cliente, chat_id, pendente, opcao)
            return

        # Etapa 1: interpretar o pedido
        msg_sem_itens = MSG_SEM_ITENS
        if midia:
            pedido_extraido = await _extrair_do_audio(chat_id, update_id, midia)
            if pedido_extraido is None:
                return
            msg_sem_itens = MSG_AUDIO_INCOMPREENDIDO
        elif texto:
            pedido_extraido = await _extrair_do_texto(chat_id, update_id, texto)
            if pedido_extraido is None:
                return
        else:
            return

        if not pedido_extraido.itens:
            await telegram.enviar_texto(chat_id, msg_sem_itens)
            return

        pedido = Pedido(
            cliente_id=cliente.id,
            observacao=pedido_extraido.observacao,
            itens=await catalogo.montar_itens(session, pedido_extraido.itens),
        )
        session.add(pedido)
        await session.commit()

        await telegram.enviar_texto(
            chat_id,
            f"Entendi seu pedido #{pedido.id}:\n{_resumo(pedido.itens)}\n\n{MSG_OPCOES}",
            reply_markup=TECLADO_OPCOES,
        )


async def _extrair_do_texto(chat_id: int, update_id: int | None, texto: str) -> PedidoExtraido | None:
    """Interpreta o texto. Se a IA falhar ou demorar, avisa o cliente e devolve None."""
    try:
        return await asyncio.wait_for(
            llm.extrair_pedido(texto=texto),
            timeout=settings.ia_texto_timeout_segundos,
        )
    except Exception:
        log.exception("Falha ao interpretar o texto do update %s do Telegram", update_id)
        await telegram.enviar_texto(chat_id, MSG_IA_FALHA)
        return None


async def _extrair_do_audio(chat_id: int, update_id: int | None, midia: dict) -> PedidoExtraido | None:
    """Valida, baixa e interpreta o áudio/nota de voz enviado no Telegram."""
    metadados = {
        "seconds": midia.get("duration"),
        "mimetype": midia.get("mime_type"),
    }
    rejeicao = audio.validar(metadados)
    if rejeicao is audio.Rejeicao.FORMATO:
        await telegram.enviar_texto(chat_id, MSG_AUDIO_FORMATO)
        return None
    if rejeicao is audio.Rejeicao.LONGO:
        await telegram.enviar_texto(chat_id, MSG_AUDIO_LONGO.format(limite=settings.audio_max_segundos))
        return None

    try:
        dados = await telegram.baixar_audio(midia["file_id"])
        if audio.tamanho_valido(dados):
            return await asyncio.wait_for(
                llm.extrair_pedido(audio=dados, audio_mime=audio.mime_gemini(midia.get("mime_type"))),
                timeout=settings.audio_timeout_segundos,
            )
    except Exception:
        log.exception("Falha ao interpretar o áudio do update %s do Telegram", update_id)
        await telegram.enviar_texto(chat_id, MSG_AUDIO_FALHA)
        return None

    await telegram.enviar_texto(chat_id, MSG_AUDIO_LONGO.format(limite=settings.audio_max_segundos))
    return None


def _nome_usuario(usuario: dict | None) -> str | None:
    if not isinstance(usuario, dict):
        return None
    partes = [usuario.get("first_name"), usuario.get("last_name")]
    nome = " ".join(p.strip() for p in partes if p and p.strip())
    return nome or usuario.get("username")


def _identificador_cliente(chat_id: int | str) -> str:
    return f"tg:{chat_id}"


def _resumo(itens: list[ItemPedido]) -> str:
    """Itens com preço do catálogo e valor estimado; itens fora do catálogo ficam a confirmar."""
    linhas = []
    for i in itens:
        sub = catalogo.subtotal(i)
        preco = f" — {catalogo.brl(sub)}" if sub is not None else " — preço a confirmar"
        linhas.append(f"• {float(i.quantidade):g} {i.unidade} de {i.nome}{preco}")
    if any(i.preco_unitario is not None for i in itens):
        linhas.append(f"\nValor estimado: {catalogo.brl(catalogo.total_estimado(itens))}")
    return "\n".join(linhas)


async def _repetida(session: AsyncSession, update_id: int | None) -> bool:
    """Registra o update_id do Telegram; True se ele já existia (reenvio do webhook)."""
    if update_id is None:
        return False
    session.add(MensagemProcessada(id=f"tg:{update_id}"))
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return True
    return False


async def _obter_cliente(session: AsyncSession, chat_id: int | str, nome: str | None) -> Cliente:
    identificador = _identificador_cliente(chat_id)
    cliente = await session.scalar(select(Cliente).where(Cliente.telefone == identificador))
    if cliente is None:
        cliente = Cliente(telefone=identificador, nome=nome)
        session.add(cliente)
        await session.commit()
    return cliente


async def _pedido_pendente(session: AsyncSession, cliente: Cliente) -> Pedido | None:
    return await session.scalar(
        select(Pedido)
        .where(
            Pedido.cliente_id == cliente.id,
            Pedido.status == StatusPedido.AGUARDANDO_CONFIRMACAO,
        )
        .order_by(Pedido.id.desc())
    )


async def _tratar_resposta(
    session: AsyncSession,
    cliente: Cliente,
    chat_id: int | str,
    pedido: Pedido | None,
    opcao: str | None,
) -> None:
    if pedido is None:
        ultimo = await session.scalar(
            select(Pedido).where(Pedido.cliente_id == cliente.id).order_by(Pedido.id.desc())
        )
        if opcao == "confirmar" and ultimo is not None and ultimo.status == StatusPedido.EXPIRADO:
            await telegram.enviar_texto(chat_id, MSG_JA_EXPIROU.format(id=ultimo.id))
            return
        log.warning("Cliente %s respondeu '%s' sem pedido aguardando confirmação", cliente.id, opcao)
        await telegram.enviar_texto(chat_id, "Você não tem nenhum pedido aguardando confirmação.")
        return

    if opcao is None:
        await telegram.enviar_texto(
            chat_id,
            f"Não entendi sua resposta sobre o pedido #{pedido.id}. {MSG_OPCOES}",
            reply_markup=TECLADO_OPCOES,
        )
        return

    pedido.status = StatusPedido.CONFIRMADO if opcao == "confirmar" else StatusPedido.CANCELADO
    await session.commit()
    resposta = {
        "confirmar": f"✅ Pedido #{pedido.id} confirmado! Avisaremos quando sair para entrega.",
        "corrigir": f"✏️ Pedido #{pedido.id} cancelado para correção. Envie o pedido completo do jeito certo.",
        "cancelar": f"❌ Pedido #{pedido.id} cancelado.",
    }[opcao]
    await telegram.enviar_texto(chat_id, resposta)
