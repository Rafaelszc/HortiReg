from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _limpar(v: str) -> str:
    v = " ".join(v.split())
    if not v:
        raise ValueError("Informe um valor.")
    return v


class ProdutoIn(BaseModel):
    nome: str = Field(max_length=120)
    unidade: str = Field(default="kg", max_length=20)
    preco: Decimal = Field(ge=0, max_digits=10, decimal_places=2)

    _nome = field_validator("nome", "unidade")(_limpar)


class ProdutoPatch(BaseModel):
    """Alteração parcial: preço e/ou ativo (US-04)."""

    preco: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    ativo: bool | None = None


class ProdutoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    unidade: str
    preco: Decimal
    ativo: bool
