from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.produto import Produto
from app.models.precificacao import Precificacao
from app.schemas.produto import (
    ProdutoCreate,
    ProdutoResponse,
    ProdutoUpdate,
    PrecificacaoCreate,
    PrecificacaoResponse,
    PrecificacaoUpdate,
)

router = APIRouter(prefix="/api", tags=["produtos"])


@router.post(
    "/produtos",
    response_model=ProdutoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def criar_produto(
    dados: ProdutoCreate,
    session: AsyncSession = Depends(get_session),
):
    produto = Produto(
        nome=dados.nome,
        descricao=dados.descricao,
        precificacoes=[
            Precificacao(unidade=p.unidade, preco=p.preco)
            for p in dados.precificacoes
        ],
    )

    session.add(produto)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflito ao cadastrar produto ou precificação.",
        )

    resultado = await session.scalar(
        select(Produto)
        .options(selectinload(Produto.precificacoes))
        .where(Produto.id == produto.id)
    )

    return resultado


@router.get("/produtos", response_model=list[ProdutoResponse])
async def listar_produtos(
    ativo: bool | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    consulta = select(Produto).options(
        selectinload(Produto.precificacoes)
    )

    if ativo is not None:
        consulta = consulta.where(Produto.ativo == ativo)

    resultado = await session.scalars(consulta.order_by(Produto.nome))

    return list(resultado.all())


@router.get("/produtos/{produto_id}", response_model=ProdutoResponse)
async def consultar_produto(
    produto_id: int,
    session: AsyncSession = Depends(get_session),
):
    consulta = (
        select(Produto)
        .options(selectinload(Produto.precificacoes))
        .where(Produto.id == produto_id)
    )

    produto = await session.scalar(consulta)

    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    return produto


@router.patch("/produtos/{produto_id}", response_model=ProdutoResponse)
async def atualizar_produto(
    produto_id: int,
    dados: ProdutoUpdate,
    session: AsyncSession = Depends(get_session),
):
    produto = await session.get(Produto, produto_id)

    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    alteracoes = dados.model_dump(exclude_unset=True)

    for campo, valor in alteracoes.items():
        setattr(produto, campo, valor)

    await session.commit()

    resultado = await session.scalar(
        select(Produto)
        .options(selectinload(Produto.precificacoes))
        .where(Produto.id == produto_id)
    )

    return resultado


@router.patch(
    "/produtos/{produto_id}/status",
    response_model=ProdutoResponse,
)
async def alterar_status_produto(
    produto_id: int,
    ativo: bool,
    session: AsyncSession = Depends(get_session),
):
    produto = await session.get(Produto, produto_id)

    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    produto.ativo = ativo
    await session.commit()

    resultado = await session.scalar(
        select(Produto)
        .options(selectinload(Produto.precificacoes))
        .where(Produto.id == produto_id)
    )

    return resultado


@router.post(
    "/produtos/{produto_id}/precificacoes",
    response_model=PrecificacaoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def criar_precificacao(
    produto_id: int,
    dados: PrecificacaoCreate,
    session: AsyncSession = Depends(get_session),
):
    produto = await session.get(Produto, produto_id)

    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    if not produto.ativo:
        raise HTTPException(
            status_code=409,
            detail="Não é possível adicionar precificações a um produto inativo.",
        )

    precificacao = Precificacao(
        produto_id=produto_id,
        unidade=dados.unidade,
        preco=dados.preco,
    )

    session.add(precificacao)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Já existe uma precificação para essa unidade ou o preço é inválido.",
        )

    await session.refresh(precificacao)
    return precificacao


@router.get(
    "/produtos/{produto_id}/precificacoes",
    response_model=list[PrecificacaoResponse],
)
async def listar_precificacoes(
    produto_id: int,
    session: AsyncSession = Depends(get_session),
):
    produto = await session.get(Produto, produto_id)

    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    resultado = await session.scalars(
        select(Precificacao)
        .where(Precificacao.produto_id == produto_id)
        .order_by(Precificacao.id)
    )

    return list(resultado.all())


@router.patch(
    "/precificacoes/{precificacao_id}",
    response_model=PrecificacaoResponse,
)
async def atualizar_precificacao(
    precificacao_id: int,
    dados: PrecificacaoUpdate,
    session: AsyncSession = Depends(get_session),
):
    precificacao = await session.get(Precificacao, precificacao_id)

    if precificacao is None:
        raise HTTPException(
            status_code=404,
            detail="Precificação não encontrada.",
        )

    alteracoes = dados.model_dump(exclude_unset=True)

    if any(valor is None for valor in alteracoes.values()):
        raise HTTPException(
            status_code=422,
            detail="Os campos informados não podem ser nulos.",
        )

    for campo, valor in alteracoes.items():
        setattr(precificacao, campo, valor)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflito ao atualizar a precificação.",
        )

    await session.refresh(precificacao)
    return precificacao