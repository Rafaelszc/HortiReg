"""Expiração de pedidos não confirmados (US-10)."""

import asyncio
import logging
from datetime import timedelta

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import SessionLocal
from app.models import Cliente, Pedido, StatusPedido
from app.services import whatsapp

log = logging.getLogger("sgv.expiracao")

MSG_EXPIROU = (
    "⏰ Seu pedido #{id} expirou porque não foi confirmado em {minutos} minutos e não será separado. "
    "Para pedir de novo, é só mandar o pedido outra vez."
)


async def expirar_pendentes(session: AsyncSession) -> None:
    """Marca como EXPIRADO quem passou do prazo e avisa cada cliente uma vez."""
    # UPDATE ... RETURNING: duas execuções simultâneas nunca expiram (nem avisam) o mesmo pedido
    expirados = await session.execute(
        update(Pedido)
        .where(
            Pedido.cliente_id == Cliente.id,
            Pedido.status == StatusPedido.AGUARDANDO_CONFIRMACAO,
            Pedido.criado_em < func.now() - timedelta(minutes=settings.pedido_expira_minutos),
        )
        .values(status=StatusPedido.EXPIRADO)
        .returning(Pedido.id, Cliente.telefone)
    )
    avisos = expirados.all()
    await session.commit()
    for pedido_id, telefone in avisos:
        await whatsapp.enviar_texto(telefone, MSG_EXPIROU.format(id=pedido_id, minutos=settings.pedido_expira_minutos))


async def rodar_periodicamente(intervalo: float = 60) -> None:
    """Laço do lifespan: expira pendentes a cada `intervalo` segundos."""
    while True:
        await asyncio.sleep(intervalo)
        try:
            async with SessionLocal() as session:
                await expirar_pendentes(session)
        except Exception:
            log.exception("Erro ao expirar pedidos pendentes")
