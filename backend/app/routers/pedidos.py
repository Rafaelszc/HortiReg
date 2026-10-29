from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models import ItemPedido, Pedido, StatusPedido
from app.routers.auth import get_current_admin
from app.services import catalogo

# Pedidos e dados de clientes só para o administrador autenticado (US-02).
router = APIRouter(prefix="/pedidos", tags=["pedidos"], dependencies=[Depends(get_current_admin)])

FUSO = ZoneInfo("America/Fortaleza")


def _valor(v) -> float | None:
    return float(v) if v is not None else None


@router.get("")
async def listar(
    dia: date | None = None,
    status: StatusPedido | None = None,
    session: AsyncSession = Depends(get_session),
):
    """Últimos 50 pedidos; com `dia`, todos os pedidos daquele dia (fuso local)."""
    consulta = select(Pedido).options(selectinload(Pedido.cliente)).order_by(Pedido.id.desc())
    if dia is not None:
        inicio = datetime.combine(dia, time.min, FUSO)
        consulta = consulta.where(Pedido.criado_em >= inicio, Pedido.criado_em < inicio + timedelta(days=1))
    else:
        consulta = consulta.limit(50)
    if status is not None:
        consulta = consulta.where(Pedido.status == status)

    result = await session.scalars(consulta)
    return [
        {
            "id": p.id,
            "status": p.status,
            "criado_em": p.criado_em,
            "observacao": p.observacao,
            "cliente": {"telefone": p.cliente.telefone, "nome": p.cliente.nome},
            "total_estimado": float(catalogo.total_estimado(p.itens)),
            "itens": [
                {
                    "nome": i.nome,
                    "quantidade": float(i.quantidade),
                    "unidade": i.unidade,
                    "preco_unitario": _valor(i.preco_unitario),
                    "subtotal": _valor(catalogo.subtotal(i)),
                }
                for i in p.itens
            ],
        }
        for p in result
    ]


@router.get("/separacao")
async def relatorio_separacao(session: AsyncSession = Depends(get_session)):
    """Total de cada produto nos pedidos CONFIRMADOS (lista de separação do dia)."""
    from sqlalchemy import func

    linhas = await session.execute(
        select(ItemPedido.nome, ItemPedido.unidade, func.sum(ItemPedido.quantidade))
        .join(Pedido)
        .where(Pedido.status == StatusPedido.CONFIRMADO)
        .group_by(ItemPedido.nome, ItemPedido.unidade)
        .order_by(ItemPedido.nome)
    )
    return [{"produto": n, "unidade": u, "total": float(t)} for n, u, t in linhas]
