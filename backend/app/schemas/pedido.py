import math

from pydantic import BaseModel, Field, field_validator


class ItemExtraido(BaseModel):
    """Um item do pedido, no formato que a LLM deve devolver."""

    nome: str = Field(description="Nome do produto no singular, minúsculo. Ex: 'tomate', 'coentro'")
    quantidade: float = Field(description="Quantidade numérica. Ex: 2, 0.5")
    unidade: str = Field(description="Uma de: kg, g, un, maço, caixa, dúzia, saco")


class PedidoExtraido(BaseModel):
    """Resultado estruturado da interpretação de um áudio ou texto de pedido."""

    itens: list[ItemExtraido] = Field(default_factory=list)
    observacao: str | None = Field(
        default=None, description="Observações do cliente (horário, ponto de referência etc.)"
    )

    @field_validator("itens")
    @classmethod
    def _so_quantidade_positiva(cls, itens: list[ItemExtraido]) -> list[ItemExtraido]:
        """Descarta item com quantidade zero, negativa ou não finita vinda da IA (valor negativo no pedido)."""
        return [i for i in itens if math.isfinite(i.quantidade) and i.quantidade > 0]
