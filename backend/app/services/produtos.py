"""Regras do catálogo de produtos (cadastro, preço e inativação)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Produto
from app.schemas.produto import ProdutoIn, ProdutoPatch
from app.services.catalogo import normalizar


class ProdutoDuplicado(Exception):
    pass


async def listar(session: AsyncSession) -> list[Produto]:
    return list(await session.scalars(select(Produto).order_by(Produto.nome)))


async def criar(session: AsyncSession, dados: ProdutoIn) -> Produto:
    """Recusa nome repetido ignorando maiúsculas e acentos ("Tomate" = "tomate")."""
    existentes = {normalizar(n) for n in await session.scalars(select(Produto.nome))}
    if normalizar(dados.nome) in existentes:
        raise ProdutoDuplicado
    produto = Produto(nome=dados.nome, unidade=dados.unidade, preco=dados.preco)
    session.add(produto)
    await session.commit()
    return produto


async def atualizar(session: AsyncSession, produto_id: int, dados: ProdutoPatch) -> Produto | None:
    """Pedidos já feitos guardam o preço em ItemPedido, então a mudança só vale para os próximos."""
    produto = await session.get(Produto, produto_id)
    if produto is None:
        return None
    if dados.preco is not None:
        produto.preco = dados.preco
    if dados.ativo is not None:
        produto.ativo = dados.ativo
    await session.commit()
    return produto
