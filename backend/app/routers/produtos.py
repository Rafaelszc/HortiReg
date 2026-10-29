from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.routers.auth import get_current_admin
from app.schemas.produto import ProdutoIn, ProdutoOut, ProdutoPatch
from app.services import produtos

# Catálogo só para o administrador autenticado (US-03, US-04).
router = APIRouter(prefix="/produtos", tags=["produtos"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=list[ProdutoOut])
async def listar(session: AsyncSession = Depends(get_session)):
    return await produtos.listar(session)


@router.post("", response_model=ProdutoOut, status_code=status.HTTP_201_CREATED)
async def criar(dados: ProdutoIn, session: AsyncSession = Depends(get_session)):
    try:
        return await produtos.criar(session, dados)
    except produtos.ProdutoDuplicado:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um produto com esse nome.") from None


@router.patch("/{produto_id}", response_model=ProdutoOut)
async def atualizar(produto_id: int, dados: ProdutoPatch, session: AsyncSession = Depends(get_session)):
    produto = await produtos.atualizar(session, produto_id, dados)
    if produto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produto não encontrado.")
    return produto
