from pydantic import BaseModel, Field


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
