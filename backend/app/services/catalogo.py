"""Casa os itens extraídos pela LLM com o catálogo. O preço vem sempre daqui, nunca da LLM."""

import unicodedata
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ItemPedido, Produto
from app.schemas.pedido import ItemExtraido

CENTAVO = Decimal("0.01")


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


async def montar_itens(session: AsyncSession, extraidos: list[ItemExtraido]) -> list[ItemPedido]:
    """Cria os ItemPedido; com produto ativo de mesma unidade, grava produto_id e preço do catálogo."""
    produtos = {normalizar(p.nome): p for p in await session.scalars(select(Produto).where(Produto.ativo.is_(True)))}
    itens = []
    for e in extraidos:
        produto = produtos.get(normalizar(e.nome))
        casou = produto is not None and normalizar(produto.unidade) == normalizar(e.unidade)
        itens.append(
            ItemPedido(
                nome=e.nome,
                quantidade=e.quantidade,
                unidade=e.unidade,
                produto_id=produto.id if casou else None,
                preco_unitario=produto.preco if casou else None,
            )
        )
    return itens


def subtotal(item: ItemPedido) -> Decimal | None:
    if item.preco_unitario is None:
        return None
    return (Decimal(str(item.quantidade)) * item.preco_unitario).quantize(CENTAVO)


def total_estimado(itens: list[ItemPedido]) -> Decimal:
    return sum((s for i in itens if (s := subtotal(i)) is not None), Decimal(0))


def brl(valor: Decimal) -> str:
    inteiro, centavos = f"{valor:.2f}".split(".")
    return f"R$ {int(inteiro):,}".replace(",", ".") + f",{centavos}"
