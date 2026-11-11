"""Recebe os eventos da Evolution API (mensagens do WhatsApp)."""

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import SessionLocal
from app.models import Cliente, ItemPedido, MensagemProcessada, Pedido, StatusPedido
from app.schemas.pedido import PedidoExtraido
from app.services import audio, catalogo, llm, whatsapp

router = APIRouter(prefix="/webhook", tags=["webhook"])
log = logging.getLogger("sgv.webhook")

SIM = {"sim", "s", "confirmo", "confirmar", "ok", "isso"}
NAO = {"nao", "não", "n", "cancelar", "cancela"}
EXEMPLO = 'Exemplo: "quero 2 kg de tomate e 1 caixa de banana".'
MSG_SEM_ITENS = f"Não consegui entender os itens do pedido. Pode repetir? 🙏\n{EXEMPLO}"
MSG_AUDIO_LONGO = (
    "Seu áudio ficou longo demais (o limite é de {limite} segundos). "
    "Pode mandar um áudio mais curto ou escrever o pedido em texto? 🙏\n" + EXEMPLO
)
MSG_AUDIO_FORMATO = (
    "Não consegui abrir esse tipo de áudio. "
    "Pode gravar uma mensagem de voz pelo WhatsApp ou escrever o pedido em texto? 🙏\n" + EXEMPLO
)
MSG_AUDIO_INCOMPREENDIDO = (
    "Não consegui entender seu áudio. "
    "Pode gravar de novo, mais curto e perto do celular, ou escrever o pedido em texto? 🙏\n" + EXEMPLO
)
MSG_AUDIO_FALHA = (
    "Não consegui ouvir seu áudio agora. Pode mandar de novo daqui a pouco ou escrever o pedido em texto? 🙏\n"
    + EXEMPLO
)


@router.post("/whatsapp")
async def receber(payload: dict, background: BackgroundTasks):
    """Responde 200 imediatamente e processa a mensagem em segundo plano."""
    if payload.get("event", "").lower().replace("_", ".") != "messages.upsert":
        return {"ignored": True}
    background.add_task(processar_mensagem, payload.get("data", {}))
    return {"received": True}


async def processar_mensagem(data: dict) -> None:
    try:
        key = data.get("key", {})
        if key.get("fromMe"):
            return  # ignora mensagens enviadas pelo próprio bot

        jid = key.get("remoteJid", "")
        if not jid.endswith("@s.whatsapp.net"):
            return  # ignora grupos e status
        telefone = jid.split("@")[0]

        msg = data.get("message", {}) or {}
        texto = msg.get("conversation") or msg.get("extendedTextMessage", {}).get("text")
        eh_audio = "audioMessage" in msg

        async with SessionLocal() as session:
            if await _repetida(session, key.get("id")):
                log.info("Mensagem %s já processada; ignorada", key.get("id"))
                return

            cliente = await _obter_cliente(session, telefone, data.get("pushName"))

            # Etapa 2: o cliente está respondendo SIM/NÃO a um pedido pendente
            if texto and texto.strip().lower() in (SIM | NAO):
                await _tratar_confirmacao(session, cliente, texto.strip().lower() in SIM)
                return

            # Etapa 1: interpretar o pedido
            msg_sem_itens = MSG_SEM_ITENS
            if eh_audio:
                pedido_extraido = await _extrair_do_audio(telefone, key, msg["audioMessage"])
                if pedido_extraido is None:
                    return  # o cliente já foi avisado
                msg_sem_itens = MSG_AUDIO_INCOMPREENDIDO
            elif texto:
                pedido_extraido = await llm.extrair_pedido(texto=texto)
            else:
                return

            if not pedido_extraido.itens:
                await whatsapp.enviar_texto(telefone, msg_sem_itens)
                return

            pedido = Pedido(
                cliente_id=cliente.id,
                observacao=pedido_extraido.observacao,
                itens=await catalogo.montar_itens(session, pedido_extraido.itens),
            )
            session.add(pedido)
            await session.commit()

            await whatsapp.enviar_texto(
                telefone,
                f"Entendi seu pedido #{pedido.id}:\n{_resumo(pedido.itens)}\n\n"
                "Responda *SIM* para confirmar ou *NÃO* para cancelar.",
            )
    except Exception:
        log.exception("Erro ao processar mensagem do WhatsApp")


async def _extrair_do_audio(telefone: str, key: dict, msg_audio: dict) -> PedidoExtraido | None:
    """Valida, baixa e interpreta o áudio. Se não der, avisa o cliente e devolve None (nenhum pedido é criado)."""
    rejeicao = audio.validar(msg_audio)
    if rejeicao is audio.Rejeicao.FORMATO:
        await whatsapp.enviar_texto(telefone, MSG_AUDIO_FORMATO)
        return None
    if rejeicao is audio.Rejeicao.LONGO:
        await whatsapp.enviar_texto(telefone, MSG_AUDIO_LONGO.format(limite=settings.audio_max_segundos))
        return None

    try:
        dados = await whatsapp.baixar_audio(key)
        if audio.tamanho_valido(dados):
            return await asyncio.wait_for(
                llm.extrair_pedido(audio=dados, audio_mime=audio.mime_gemini(msg_audio.get("mimetype"))),
                timeout=settings.audio_timeout_segundos,
            )
    except Exception:
        log.exception("Falha ao interpretar o áudio da mensagem %s", key.get("id"))
        await whatsapp.enviar_texto(telefone, MSG_AUDIO_FALHA)
        return None

    await whatsapp.enviar_texto(telefone, MSG_AUDIO_LONGO.format(limite=settings.audio_max_segundos))
    return None


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


async def _repetida(session: AsyncSession, mensagem_id: str | None) -> bool:
    """Registra o id da mensagem; True se ele já existia (reenvio do webhook)."""
    if not mensagem_id:
        return False
    session.add(MensagemProcessada(id=mensagem_id))
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return True
    return False


async def _obter_cliente(session: AsyncSession, telefone: str, nome: str | None) -> Cliente:
    cliente = await session.scalar(select(Cliente).where(Cliente.telefone == telefone))
    if cliente is None:
        cliente = Cliente(telefone=telefone, nome=nome)
        session.add(cliente)
        await session.commit()
    return cliente


async def _tratar_confirmacao(session: AsyncSession, cliente: Cliente, confirmou: bool) -> None:
    pedido = await session.scalar(
        select(Pedido)
        .where(
            Pedido.cliente_id == cliente.id,
            Pedido.status == StatusPedido.AGUARDANDO_CONFIRMACAO,
        )
        .order_by(Pedido.id.desc())
    )
    if pedido is None:
        await whatsapp.enviar_texto(cliente.telefone, "Você não tem nenhum pedido aguardando confirmação.")
        return

    pedido.status = StatusPedido.CONFIRMADO if confirmou else StatusPedido.CANCELADO
    await session.commit()
    resposta = (
        f"✅ Pedido #{pedido.id} confirmado! Avisaremos quando sair para entrega."
        if confirmou
        else f"❌ Pedido #{pedido.id} cancelado."
    )
    await whatsapp.enviar_texto(cliente.telefone, resposta)
