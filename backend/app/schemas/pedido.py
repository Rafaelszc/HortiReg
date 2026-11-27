from enum import Enum
import math

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class EnderecoExtraido(BaseModel):
    """Endereço de entrega dito pelo cliente; só o que ele informou."""

    model_config = ConfigDict(hide_input_in_errors=True)  # LGPD: erro de validação não repete o endereço

    rua: str | None = Field(default=None, description="Nome da rua, avenida ou travessa. Bairro não é rua")
    numero: str | None = Field(default=None, description="Número da casa, ou 's/n' se o cliente disser que não tem")
    bairro: str | None = None
    cidade: str | None = None


class PedidoExtraido(BaseModel):
    """Resultado estruturado da interpretação de um áudio ou texto de pedido."""

    model_config = ConfigDict(hide_input_in_errors=True)

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
    endereco: EnderecoExtraido | None = Field(default=None, description="Endereço de entrega, se a mensagem trouxer")

    @field_validator("itens")
    @classmethod
    def _so_quantidade_positiva(cls, itens: list[ItemExtraido]) -> list[ItemExtraido]:
        """Descarta item com quantidade zero, negativa ou não finita vinda da IA (valor negativo no pedido)."""
        return [i for i in itens if math.isfinite(i.quantidade) and i.quantidade > 0]

    @field_validator("itens_remover")
    @classmethod
    def _normalizar_remocoes(cls, nomes: list[str]) -> list[str]:
        return [n.strip().lower() for n in nomes if n and n.strip()]
