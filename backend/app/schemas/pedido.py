from enum import Enum
import math

from pydantic import BaseModel, Field, field_validator


class AcaoPedido(str, Enum):
    """Intenção identificada pela LLM na mensagem do cliente."""

    ADICIONAR = "adicionar"
    SUBSTITUIR = "substituir"
    REMOVER = "remover"
    CONFIRMAR = "confirmar"
    CANCELAR = "cancelar"


class ItemExtraido(BaseModel):
    """Um item do pedido, no formato que a LLM deve devolver."""

    nome: str = Field(description="Nome do produto no singular, minúsculo. Ex: 'tomate', 'coentro'")
    quantidade: float = Field(description="Quantidade numérica. Ex: 2, 0.5")
    unidade: str = Field(description="Uma de: kg, g, un, maço, caixa, dúzia, saco")


class PedidoExtraido(BaseModel):
    """Resultado estruturado da interpretação de um áudio ou texto de pedido."""

    acao: AcaoPedido = Field(
        default=AcaoPedido.ADICIONAR,
        description=(
            "Comando identificado: 'adicionar' (novo pedido ou acrescentar itens), "
            "'substituir' (cancelar o pedido anterior e fazer outro no lugar), "
            "'remover' (tirar itens do pedido atual), 'confirmar' (confirmar pedido) "
            "ou 'cancelar' (cancelar pedido sem novos itens)."
        ),
    )
    itens: list[ItemExtraido] = Field(default_factory=list)
    itens_remover: list[str] = Field(
        default_factory=list,
        description="Nomes (singular, minúsculo) dos produtos que o cliente pediu para remover. Ex: ['banana']",
    )
    observacao: str | None = Field(
        default=None, description="Observações do cliente (horário, ponto de referência etc.)"
    )

    @field_validator("itens")
    @classmethod
    def _so_quantidade_positiva(cls, itens: list[ItemExtraido]) -> list[ItemExtraido]:
        """Descarta item com quantidade zero, negativa ou não finita vinda da IA (valor negativo no pedido)."""
        return [i for i in itens if math.isfinite(i.quantidade) and i.quantidade > 0]

    @field_validator("itens_remover")
    @classmethod
    def _normalizar_remocoes(cls, nomes: list[str]) -> list[str]:
        return [n.strip().lower() for n in nomes if n and n.strip()]
