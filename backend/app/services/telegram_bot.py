"""Lógica de atendimento de pedidos via Telegram (HortiReg / @HortRegBot) com máquina de estados."""

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import SessionLocal
from app.models import Cliente, ItemPedido, MensagemRecebida, Pedido, StatusMensagem, StatusPedido
from app.schemas.pedido import AcaoPedido, PedidoExtraido
from app.services import audio, catalogo, estados, expiracao, llm, telegram
from app.services.estados import EstadoConversa

log = logging.getLogger("sgv.telegram")

# Resposta ao resumo do pedido (US-08): 1-Confirmar, 2-Editar/Corrigir, 3-Cancelar
OPCOES = {
    **dict.fromkeys(("1", "sim", "s", "confirmo", "confirmar", "ok", "isso"), "confirmar"),
    **dict.fromkeys(("2", "corrigir", "editar"), "corrigir"),
    **dict.fromkeys(("3", "nao", "não", "n", "cancelar", "cancela"), "cancelar"),
}
TECLADO_MENU = {
    "inline_keyboard": [
        [{"text": "🛒 Fazer pedido", "callback_data": "novo_pedido"}],
    ]
}
TECLADO_OPCOES = {
    "inline_keyboard": [
        [
            {"text": "✅ Confirmar", "callback_data": "confirmar"},
            {"text": "✏️ Editar", "callback_data": "corrigir"},
            {"text": "❌ Cancelar", "callback_data": "cancelar"},
        ]
    ]
}
TECLADO_CONFIRMADO = {
    "inline_keyboard": [
        [
            {"text": "✏️ Editar pedido", "callback_data": "editar_pedido"},
            {"text": "❌ Cancelar pedido", "callback_data": "cancelar_pedido"},
        ],
        [{"text": "🛒 Novo pedido", "callback_data": "novo_pedido"}],
    ]
}
TECLADO_EDITANDO = {
    "inline_keyboard": [
        [{"text": "↩️ Cancelar edição", "callback_data": "cancelar_edicao"}],
    ]
}

MSG_OPCOES = (
    "Responda 1 para confirmar, 2 para editar ou 3 para cancelar "
    "(ou envie mais itens por texto ou áudio para adicionar ao pedido)."
)
EXEMPLO = 'Exemplo: "quero 2 kg de tomate e 1 caixa de banana".'
MSG_BOAS_VINDAS = (
    "Olá! Bem-vindo ao {nome} (@{username}) 🥬🍅\n"
    "Envie seu pedido por texto ou áudio que eu monto o resumo para você confirmar.\n"
    + EXEMPLO
)
MSG_PEDIR_ITENS = f"Pode enviar os itens do seu pedido por texto ou áudio! 🛒\n{EXEMPLO}"
MSG_PEDIR_EDICAO = (
    "✏️ Editando o pedido #{id}. Envie os itens corretos (por texto ou áudio) para atualizar o resumo.\n" + EXEMPLO
)
MSG_JA_EXPIROU = (
    "O pedido #{id} expirou e não pode mais ser confirmado. "
    "Quer refazer? É só mandar o pedido de novo, por texto ou áudio."
)
MSG_TEMPO_ESGOTADO = (
    "⏰ O tempo para responder ao pedido #{id} expirou (5 minutos sem resposta). "
    "Voltei para o início — quando quiser, é só fazer um novo pedido!"
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

_tarefas_ativas: set[asyncio.Task] = set()


async def processar_update(update: dict) -> None:
    """Processa um update recebido pelo webhook ou long polling do Telegram."""
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
    """Loop de long polling (getUpdates) com despacho concorrente de updates."""
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
                tarefa = asyncio.create_task(processar_update(update))
                _tarefas_ativas.add(tarefa)
                tarefa.add_done_callback(_tarefas_ativas.discard)
        except asyncio.CancelledError:
            log.info("Long polling do Telegram encerrado")
            raise
        except Exception:
            log.exception("Erro no long polling do Telegram; tentando novamente em 5s")
            await asyncio.sleep(5)


async def _ao_expirar_sessao(chat_id: int, pedido_id: int | None) -> None:
    """Callback disparado após 5 min de inatividade em AGUARDANDO_CONFIRMACAO ou EDITANDO."""
    if pedido_id is not None:
        async with SessionLocal() as session:
            pedido = await session.get(Pedido, pedido_id)
            if pedido is not None and pedido.status == StatusPedido.AGUARDANDO_CONFIRMACAO:
                pedido.status = StatusPedido.EXPIRADO
                await session.commit()
        await telegram.enviar_texto(
            chat_id,
            MSG_TEMPO_ESGOTADO.format(id=pedido_id),
            reply_markup=TECLADO_MENU,
        )
    else:
        await telegram.enviar_texto(
            chat_id,
            "⏰ Tempo esgotado por inatividade. Voltei para o início!",
            reply_markup=TECLADO_MENU,
        )


async def _processar_callback(callback: dict, update_id: int | None) -> None:
    msg = callback.get("message") or {}
    chat = msg.get("chat") or {}
    if chat.get("type") != "private" or chat.get("id") is None:
        return

    chat_id = chat["id"]
    callback_id = callback.get("id")
    if callback_id:
        await telegram.responder_callback(callback_id)

    acao = (callback.get("data") or "").strip().lower()
    if not acao:
        return

    async with SessionLocal() as session:
        if await _repetida(session, update_id):
            log.info("Update %s do Telegram já processado; ignorado", update_id)
            return

        cliente = await _obter_cliente(session, chat_id, _nome_usuario(callback.get("from")))
        await expiracao.expirar_pendentes(session)

        if acao == "novo_pedido":
            estados.definir(chat_id, EstadoConversa.FAZENDO_PEDIDO)
            await telegram.enviar_texto(chat_id, MSG_PEDIR_ITENS)
            return

        if acao == "cancelar_edicao":
            await _cancelar_edicao(session, chat_id)
            return

        if acao in ("editar_pedido", "cancelar_pedido"):
            await _gerenciar_confirmado(session, cliente, chat_id, acao)
            return

        opcao = OPCOES.get(acao)
        if not opcao:
            return
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

        comando = texto.split()[0].lower().split("@")[0] if texto else ""
        if comando in ("/start", "/ajuda", "/help"):
            estados.resetar(chat_id)
            await telegram.enviar_texto(
                chat_id,
                MSG_BOAS_VINDAS.format(nome=settings.telegram_bot_name, username=settings.telegram_bot_username),
                reply_markup=TECLADO_MENU,
            )
            return

        if comando == "/pedido":
            estados.definir(chat_id, EstadoConversa.FAZENDO_PEDIDO)
            await telegram.enviar_texto(chat_id, MSG_PEDIR_ITENS)
            return

        cliente = await _obter_cliente(session, chat_id, _nome_usuario(remetente))
        await expiracao.expirar_pendentes(session)
        sessao = estados.obter(chat_id)

        # Estado EDITANDO: cliente envia os novos itens para atualizar o pedido em edição
        if sessao.estado == EstadoConversa.EDITANDO:
            await _processar_edicao(session, cliente, chat_id, update_id, texto, midia, sessao.pedido_id)
            return

        # Estado PEDIDO_CONFIRMADO: aceita editar/cancelar por texto ou iniciar novo pedido
        if sessao.estado == EstadoConversa.PEDIDO_CONFIRMADO and texto:
            escolha = OPCOES.get(texto.lower())
            if escolha == "corrigir":
                await _gerenciar_confirmado(session, cliente, chat_id, "editar_pedido")
                return
            if escolha == "cancelar":
                await _gerenciar_confirmado(session, cliente, chat_id, "cancelar_pedido")
                return

        # Etapa 2 (AGUARDANDO_CONFIRMACAO ou pedido pendente no banco):
        # 1/2/3 confirmam/editam/cancelam; outro texto ou áudio é interpretado como comando/edição pela IA.
        opcao = OPCOES.get(texto.lower()) if texto else None
        pendente = await _pedido_pendente(session, cliente)
        if pendente is not None:
            if opcao is not None:
                await _tratar_resposta(session, cliente, chat_id, pendente, opcao)
            else:
                await _processar_comando_pendente(session, cliente, chat_id, update_id, pendente, texto, midia)
            return
        if opcao is not None:
            await _tratar_resposta(session, cliente, chat_id, None, opcao)
            return

        # Etapa 1 (ESPERANDO ou FAZENDO_PEDIDO): interpretar novo pedido
        await _criar_novo_pedido(session, cliente, chat_id, update_id, texto, midia)


async def _criar_novo_pedido(
    session: AsyncSession,
    cliente: Cliente,
    chat_id: int,
    update_id: int | None,
    texto: str,
    midia: dict | None,
) -> None:
    estados.definir(chat_id, EstadoConversa.FAZENDO_PEDIDO)
    pedido_extraido, msg_sem_itens = await _extrair_itens(chat_id, update_id, texto, midia)
    if pedido_extraido is None:
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

    estados.definir(
        chat_id,
        EstadoConversa.AGUARDANDO_CONFIRMACAO,
        pedido_id=pedido.id,
        on_timeout=_ao_expirar_sessao,
    )
    await telegram.enviar_texto(
        chat_id,
        f"Entendi seu pedido #{pedido.id}:\n{_resumo(pedido.itens)}\n\n{MSG_OPCOES}",
        reply_markup=TECLADO_OPCOES,
    )


def _mesclar_itens(atuais: list[ItemPedido], novos: list[ItemPedido]) -> None:
    """Adiciona novos itens ao pedido; se nome e unidade já existirem, soma a quantidade."""
    por_chave = {(i.nome.strip().lower(), i.unidade.strip().lower()): i for i in atuais}
    for novo in novos:
        chave = (novo.nome.strip().lower(), novo.unidade.strip().lower())
        existente = por_chave.get(chave)
        if existente is not None:
            existente.quantidade += novo.quantidade
        else:
            atuais.append(novo)
            por_chave[chave] = novo


def _remover_itens(atuais: list[ItemPedido], nomes_remover: list[str]) -> tuple[list[str], list[str]]:
    """Remove itens pelo nome (singular, minúsculo). Retorna (removidos, nao_encontrados)."""
    removidos: list[str] = []
    nao_encontrados: list[str] = []
    for alvo in nomes_remover:
        alvo_norm = alvo.strip().lower()
        antes = len(atuais)
        atuais[:] = [i for i in atuais if i.nome.strip().lower() != alvo_norm]
        if len(atuais) < antes:
            removidos.append(alvo_norm)
        else:
            nao_encontrados.append(alvo_norm)
    return removidos, nao_encontrados


async def _processar_comando_pendente(
    session: AsyncSession,
    cliente: Cliente,
    chat_id: int,
    update_id: int | None,
    pedido: Pedido,
    texto: str,
    midia: dict | None,
) -> None:
    """Interpreta texto/áudio durante AGUARDANDO_CONFIRMACAO: adicionar, substituir, remover, confirmar ou cancelar."""
    pedido_extraido, _ = await _extrair_itens(chat_id, update_id, texto, midia)
    if pedido_extraido is None:
        estados.definir(
            chat_id,
            EstadoConversa.AGUARDANDO_CONFIRMACAO,
            pedido_id=pedido.id,
            on_timeout=_ao_expirar_sessao,
        )
        return

    acao = pedido_extraido.acao

    if acao == AcaoPedido.CONFIRMAR:
        await _tratar_resposta(session, cliente, chat_id, pedido, "confirmar")
        return

    if acao == AcaoPedido.CANCELAR:
        await _tratar_resposta(session, cliente, chat_id, pedido, "cancelar")
        return

    if acao == AcaoPedido.SUBSTITUIR:
        if not pedido_extraido.itens:
            await _tratar_resposta(session, cliente, chat_id, pedido, "cancelar")
            return
        pedido.observacao = pedido_extraido.observacao
        pedido.itens = await catalogo.montar_itens(session, pedido_extraido.itens)
        await session.commit()
        estados.definir(
            chat_id,
            EstadoConversa.AGUARDANDO_CONFIRMACAO,
            pedido_id=pedido.id,
            on_timeout=_ao_expirar_sessao,
        )
        await telegram.enviar_texto(
            chat_id,
            f"🔄 Substituí os itens do seu pedido #{pedido.id}:\n{_resumo(pedido.itens)}\n\n{MSG_OPCOES}",
            reply_markup=TECLADO_OPCOES,
        )
        return

    # ADICIONAR ou REMOVER (suporta inclusive remoção + adição na mesma frase)
    if not pedido_extraido.itens and not pedido_extraido.itens_remover:
        estados.definir(
            chat_id,
            EstadoConversa.AGUARDANDO_CONFIRMACAO,
            pedido_id=pedido.id,
            on_timeout=_ao_expirar_sessao,
        )
        await telegram.enviar_texto(
            chat_id,
            f"Não entendi sua resposta sobre o pedido #{pedido.id}. {MSG_OPCOES}",
            reply_markup=TECLADO_OPCOES,
        )
        return

    avisos: list[str] = []
    if pedido_extraido.itens_remover:
        _, nao_encontrados = _remover_itens(pedido.itens, pedido_extraido.itens_remover)
        for nome in nao_encontrados:
            avisos.append(f"⚠️ '{nome}' não está no seu pedido #{pedido.id}.")

    if pedido_extraido.itens:
        novos_itens = await catalogo.montar_itens(session, pedido_extraido.itens)
        _mesclar_itens(pedido.itens, novos_itens)

    if pedido_extraido.observacao:
        if pedido.observacao:
            pedido.observacao = f"{pedido.observacao}; {pedido_extraido.observacao}"[:500]
        else:
            pedido.observacao = pedido_extraido.observacao

    if not pedido.itens:
        pedido.status = StatusPedido.CANCELADO
        await session.commit()
        estados.resetar(chat_id)
        await telegram.enviar_texto(
            chat_id,
            f"❌ Todos os itens foram removidos e o pedido #{pedido.id} foi cancelado.",
            reply_markup=TECLADO_MENU,
        )
        return

    await session.commit()
    estados.definir(
        chat_id,
        EstadoConversa.AGUARDANDO_CONFIRMACAO,
        pedido_id=pedido.id,
        on_timeout=_ao_expirar_sessao,
    )
    prefixo = "\n".join(avisos) + "\n" if avisos else ""
    cabecalho = (
        f"Adicionei ao seu pedido #{pedido.id}:"
        if pedido_extraido.itens and not pedido_extraido.itens_remover
        else f"Atualizei seu pedido #{pedido.id}:"
    )
    await telegram.enviar_texto(
        chat_id,
        f"{prefixo}{cabecalho}\n{_resumo(pedido.itens)}\n\n{MSG_OPCOES}",
        reply_markup=TECLADO_OPCOES,
    )


async def _processar_edicao(
    session: AsyncSession,
    cliente: Cliente,
    chat_id: int,
    update_id: int | None,
    texto: str,
    midia: dict | None,
    pedido_id: int | None,
) -> None:
    pedido = await session.get(Pedido, pedido_id) if pedido_id is not None else None
    if pedido is None or pedido.cliente_id != cliente.id or pedido.status not in (
        StatusPedido.AGUARDANDO_CONFIRMACAO,
        StatusPedido.CONFIRMADO,
    ):
        estados.resetar(chat_id)
        await telegram.enviar_texto(
            chat_id,
            "Esse pedido não está mais disponível para edição.",
            reply_markup=TECLADO_MENU,
        )
        return

    pedido_extraido, msg_sem_itens = await _extrair_itens(chat_id, update_id, texto, midia)
    if pedido_extraido is None:
        return

    if not pedido_extraido.itens:
        estados.definir(chat_id, EstadoConversa.EDITANDO, pedido_id=pedido.id, on_timeout=_ao_expirar_sessao)
        await telegram.enviar_texto(chat_id, msg_sem_itens, reply_markup=TECLADO_EDITANDO)
        return

    pedido.observacao = pedido_extraido.observacao
    pedido.itens = await catalogo.montar_itens(session, pedido_extraido.itens)
    pedido.status = StatusPedido.AGUARDANDO_CONFIRMACAO
    await session.commit()

    estados.definir(
        chat_id,
        EstadoConversa.AGUARDANDO_CONFIRMACAO,
        pedido_id=pedido.id,
        on_timeout=_ao_expirar_sessao,
    )
    await telegram.enviar_texto(
        chat_id,
        f"Atualizei seu pedido #{pedido.id}:\n{_resumo(pedido.itens)}\n\n{MSG_OPCOES}",
        reply_markup=TECLADO_OPCOES,
    )


async def _cancelar_edicao(session: AsyncSession, chat_id: int) -> None:
    sessao = estados.obter(chat_id)
    pedido = await session.get(Pedido, sessao.pedido_id) if sessao.pedido_id is not None else None
    if pedido is not None and pedido.status == StatusPedido.AGUARDANDO_CONFIRMACAO:
        estados.definir(
            chat_id,
            EstadoConversa.AGUARDANDO_CONFIRMACAO,
            pedido_id=pedido.id,
            on_timeout=_ao_expirar_sessao,
        )
        await telegram.enviar_texto(
            chat_id,
            f"Edição cancelada. Seu pedido #{pedido.id} continua assim:\n{_resumo(pedido.itens)}\n\n{MSG_OPCOES}",
            reply_markup=TECLADO_OPCOES,
        )
        return

    if pedido is not None and pedido.status == StatusPedido.CONFIRMADO:
        estados.definir(chat_id, EstadoConversa.PEDIDO_CONFIRMADO, pedido_id=pedido.id)
        await telegram.enviar_texto(
            chat_id,
            f"Edição cancelada. Seu pedido #{pedido.id} continua confirmado.",
            reply_markup=TECLADO_CONFIRMADO,
        )
        return

    estados.resetar(chat_id)
    await telegram.enviar_texto(chat_id, "Edição cancelada.", reply_markup=TECLADO_MENU)


async def _gerenciar_confirmado(
    session: AsyncSession,
    cliente: Cliente,
    chat_id: int,
    acao: str,
) -> None:
    sessao = estados.obter(chat_id)
    pedido = await session.get(Pedido, sessao.pedido_id) if sessao.pedido_id is not None else None
    if pedido is None or pedido.cliente_id != cliente.id or pedido.status != StatusPedido.CONFIRMADO:
        pedido = await session.scalar(
            select(Pedido)
            .where(Pedido.cliente_id == cliente.id, Pedido.status == StatusPedido.CONFIRMADO)
            .order_by(Pedido.id.desc())
        )

    if pedido is None:
        estados.resetar(chat_id)
        await telegram.enviar_texto(
            chat_id,
            "Você não tem nenhum pedido confirmado ativo para alterar.",
            reply_markup=TECLADO_MENU,
        )
        return

    if acao == "editar_pedido":
        estados.definir(chat_id, EstadoConversa.EDITANDO, pedido_id=pedido.id, on_timeout=_ao_expirar_sessao)
        await telegram.enviar_texto(
            chat_id,
            MSG_PEDIR_EDICAO.format(id=pedido.id),
            reply_markup=TECLADO_EDITANDO,
        )
        return

    pedido.status = StatusPedido.CANCELADO
    await session.commit()
    estados.resetar(chat_id)
    await telegram.enviar_texto(
        chat_id,
        f"❌ Pedido #{pedido.id} cancelado.",
        reply_markup=TECLADO_MENU,
    )


async def _extrair_itens(
    chat_id: int,
    update_id: int | None,
    texto: str,
    midia: dict | None,
) -> tuple[PedidoExtraido | None, str]:
    if midia:
        return await _extrair_do_audio(chat_id, update_id, midia), MSG_AUDIO_INCOMPREENDIDO
    if texto:
        return await _extrair_do_texto(chat_id, update_id, texto), MSG_SEM_ITENS
    return None, MSG_SEM_ITENS


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
    agora = datetime.now(UTC)
    # Já nasce PROCESSADA: a fila de retentativa (WhatsApp) só pega PENDENTE.
    session.add(
        MensagemRecebida(
            id=f"tg:{update_id}",
            telefone="telegram",
            payload={},
            status=StatusMensagem.PROCESSADA,
            proxima_tentativa_em=agora,
            criado_em=agora,
        )
    )
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
    chat_id: int,
    pedido: Pedido | None,
    opcao: str | None,
) -> None:
    if pedido is None:
        ultimo = await session.scalar(
            select(Pedido).where(Pedido.cliente_id == cliente.id).order_by(Pedido.id.desc())
        )
        estados.resetar(chat_id)
        if opcao == "confirmar" and ultimo is not None and ultimo.status == StatusPedido.EXPIRADO:
            await telegram.enviar_texto(chat_id, MSG_JA_EXPIROU.format(id=ultimo.id), reply_markup=TECLADO_MENU)
            return
        log.warning("Cliente %s respondeu '%s' sem pedido aguardando confirmação", cliente.id, opcao)
        await telegram.enviar_texto(
            chat_id,
            "Você não tem nenhum pedido aguardando confirmação.",
            reply_markup=TECLADO_MENU,
        )
        return

    if opcao is None:
        estados.definir(
            chat_id,
            EstadoConversa.AGUARDANDO_CONFIRMACAO,
            pedido_id=pedido.id,
            on_timeout=_ao_expirar_sessao,
        )
        await telegram.enviar_texto(
            chat_id,
            f"Não entendi sua resposta sobre o pedido #{pedido.id}. {MSG_OPCOES}",
            reply_markup=TECLADO_OPCOES,
        )
        return

    if opcao == "corrigir":
        estados.definir(chat_id, EstadoConversa.EDITANDO, pedido_id=pedido.id, on_timeout=_ao_expirar_sessao)
        await telegram.enviar_texto(
            chat_id,
            MSG_PEDIR_EDICAO.format(id=pedido.id),
            reply_markup=TECLADO_EDITANDO,
        )
        return

    if opcao == "confirmar":
        pedido.status = StatusPedido.CONFIRMADO
        await session.commit()
        estados.definir(chat_id, EstadoConversa.PEDIDO_CONFIRMADO, pedido_id=pedido.id)
        await telegram.enviar_texto(
            chat_id,
            f"✅ Pedido #{pedido.id} confirmado! Avisaremos quando sair para entrega.",
            reply_markup=TECLADO_CONFIRMADO,
        )
        return

    pedido.status = StatusPedido.CANCELADO
    await session.commit()
    estados.resetar(chat_id)
    await telegram.enviar_texto(
        chat_id,
        f"❌ Pedido #{pedido.id} cancelado.",
        reply_markup=TECLADO_MENU,
    )
