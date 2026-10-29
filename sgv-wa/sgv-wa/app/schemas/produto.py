from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing import Annotated


NomeProduto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
UnidadeVenda = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]


class PrecificacaoCreate(BaseModel):
    unidade: UnidadeVenda
    preco: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class PrecificacaoUpdate(BaseModel):
    unidade: UnidadeVenda | None = None
    preco: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    ativo: bool | None = None


class PrecificacaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produto_id: int
    unidade: str
    preco: Decimal
    ativo: bool


class ProdutoCreate(BaseModel):
    nome: NomeProduto
    descricao: str | None = None
    precificacoes: list[PrecificacaoCreate] = Field(min_length=1)


class ProdutoUpdate(BaseModel):
    nome: NomeProduto | None = None
    descricao: str | None = None
    ativo: bool | None = None


class ProdutoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None
    ativo: bool
    precificacoes: list[PrecificacaoResponse]