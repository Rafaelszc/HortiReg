"""Fila de mensagens do WhatsApp com retentativa (RK-03 / DA-CONF-I3-01).

Toda mensagem é gravada ao chegar. Se a IA (ou o download do áudio) falhar, a mensagem continua PENDENTE, o cliente
recebe um aviso único e um laço em segundo plano tenta de novo com espera crescente, até o prazo configurado.
"""

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.database import SessionLocal
from app.models import MensagemRecebida, StatusMensagem
from app.services import security, whatsapp

log = logging.getLogger("sgv.fila")

MSG_EM_PROCESSAMENTO = "Recebi seu pedido e estou processando. Te respondo em instantes. ⏳"

Processador = Callable[[dict], Awaitable[None]]


class FalhaTransitoria(Exception):
    """Falha que vale retentar (IA fora do ar, timeout, download do áudio). Carrega o aviso final ao cliente."""

    def __init__(self, mensagem_final: str):
        super().__init__(mensagem_final)
        self.mensagem_final = mensagem_final


def agora() -> datetime:
    return security.agora()


def espera(tentativas: int) -> timedelta:
    """Espera antes da próxima tentativa: dobra a cada falha, com teto."""
    segundos = settings.fila_espera_inicial_segundos * 2 ** (tentativas - 1)
    return timedelta(seconds=min(segundos, settings.fila_espera_maxima_segundos))


async def registrar(telefone: str, data: dict) -> str | None:
    """Grava a mensagem ao chegar. Devolve o id, ou None se o id já existia (reenvio do mesmo evento)."""
    mensagem_id = data.get("key", {}).get("id") or uuid.uuid4().hex
    async with SessionLocal() as session:
        session.add(
            MensagemRecebida(
                id=mensagem_id,
                telefone=telefone,
                payload=data,
                proxima_tentativa_em=agora(),
                criado_em=agora(),
            )
        )
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return None
    return mensagem_id


async def _reservar(session, mensagem_id: str) -> dict | None:
    """Reserva a mensagem para este processamento (UPDATE atômico) e devolve seu payload.

    Devolve None se outro processamento já a pegou, se ainda não é a hora ou se há mensagem mais antiga do mesmo
    número ainda PENDENTE (a ordem de chegada por cliente vale).
    """
    msg = await session.get(MensagemRecebida, mensagem_id)
    if msg is None:
        return None
    agora_ = agora()
    mais_antiga = (
        select(MensagemRecebida.id)
        .where(
            MensagemRecebida.telefone == msg.telefone,
            MensagemRecebida.status == StatusMensagem.PENDENTE,
            MensagemRecebida.criado_em < msg.criado_em,
        )
        .exists()
    )
    reservada = await session.scalar(
        update(MensagemRecebida)
        .where(
            MensagemRecebida.id == mensagem_id,
            MensagemRecebida.status == StatusMensagem.PENDENTE,
            MensagemRecebida.proxima_tentativa_em <= agora_,
            ~mais_antiga,
        )
        .values(proxima_tentativa_em=agora_ + timedelta(seconds=settings.fila_reserva_segundos))
        .returning(MensagemRecebida.id)
    )
    await session.commit()
    return msg.payload if reservada else None


async def processar(mensagem_id: str, processador: Processador) -> None:
    """Processa uma mensagem da fila: sucesso encerra; falha transitória agenda nova tentativa."""
    async with SessionLocal() as session:
        data = await _reservar(session, mensagem_id)
    if data is None:
        return
    try:
        await processador(data)
    except FalhaTransitoria as falha:
        await _registrar_falha(mensagem_id, falha)
    except Exception:
        log.exception("Erro inesperado ao processar a mensagem %s", mensagem_id)
        await _encerrar(mensagem_id, StatusMensagem.FALHOU)
    else:
        await _encerrar(mensagem_id, StatusMensagem.PROCESSADA)


async def _encerrar(mensagem_id: str, status: StatusMensagem) -> None:
    async with SessionLocal() as session:
        await session.execute(update(MensagemRecebida).where(MensagemRecebida.id == mensagem_id).values(status=status))
        await session.commit()


async def _registrar_falha(mensagem_id: str, falha: FalhaTransitoria) -> None:
    async with SessionLocal() as session:
        msg = await session.get(MensagemRecebida, mensagem_id)
        msg.tentativas += 1
        desistir = agora() - msg.criado_em >= timedelta(minutes=settings.fila_prazo_minutos)
        avisar = not desistir and not msg.avisado
        if desistir:
            msg.status = StatusMensagem.FALHOU
        else:
            msg.proxima_tentativa_em = agora() + espera(msg.tentativas)
        await session.commit()
        telefone, tentativas = msg.telefone, msg.tentativas

    log.warning("Mensagem %s falhou (tentativa %s)%s", mensagem_id, tentativas, "; desistindo" if desistir else "")
    texto = falha.mensagem_final if desistir else MSG_EM_PROCESSAMENTO if avisar else None
    if texto is None:
        return
    try:
        await whatsapp.enviar_texto(telefone, texto)
    except Exception:
        log.exception("Não consegui avisar o cliente da mensagem %s", mensagem_id)
        return
    if avisar:
        async with SessionLocal() as session:
            await session.execute(
                update(MensagemRecebida).where(MensagemRecebida.id == mensagem_id).values(avisado=True)
            )
            await session.commit()


async def reprocessar_pendentes(processador: Processador) -> None:
    """Tenta de novo, na ordem de chegada, as mensagens PENDENTES cuja hora chegou."""
    async with SessionLocal() as session:
        ids = (
            await session.scalars(
                select(MensagemRecebida.id)
                .where(
                    MensagemRecebida.status == StatusMensagem.PENDENTE,
                    MensagemRecebida.proxima_tentativa_em <= agora(),
                )
                .order_by(MensagemRecebida.criado_em)
            )
        ).all()
    for mensagem_id in ids:
        await processar(mensagem_id, processador)


async def rodar_periodicamente(processador: Processador) -> None:
    """Laço do lifespan: reprocessa a fila a cada `fila_intervalo_segundos`."""
    while True:
        await asyncio.sleep(settings.fila_intervalo_segundos)
        try:
            await reprocessar_pendentes(processador)
        except Exception:
            log.exception("Erro ao reprocessar a fila de mensagens")
