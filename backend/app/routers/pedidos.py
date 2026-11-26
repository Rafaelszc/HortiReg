from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models import ItemPedido, Pedido, StatusPedido
from app.routers.auth import get_current_admin
from app.services import pedidos_dia

# Pedidos e dados de clientes só para o administrador autenticado (US-02).
router = APIRouter(prefix="/pedidos", tags=["pedidos"], dependencies=[Depends(get_current_admin)])


@router.get("")
async def listar(session: AsyncSession = Depends(get_session)):
    result = await session.scalars(select(Pedido).order_by(Pedido.id.desc()).limit(50))
    return [
        {
            "id": p.id,
            "status": p.status,
            "itens": [{"nome": i.nome, "quantidade": float(i.quantidade), "unidade": i.unidade} for i in p.itens],
        }
        for p in result
    ]


@router.get("/dia")
async def pedidos_do_dia(session: AsyncSession = Depends(get_session)):
    """Pedidos CONFIRMADOS feitos hoje, no fuso da feira (US-12)."""
    inicio, fim = pedidos_dia.intervalo_de_hoje()
    result = await session.scalars(
        select(Pedido)
        .options(selectinload(Pedido.cliente))
        .where(Pedido.status == StatusPedido.CONFIRMADO, Pedido.criado_em >= inicio, Pedido.criado_em < fim)
        .order_by(Pedido.criado_em)
    )
    return [pedidos_dia.resumo(p) for p in result]


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
