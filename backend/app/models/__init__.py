import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StatusPedido(str, enum.Enum):
    AGUARDANDO_CONFIRMACAO = "AGUARDANDO_CONFIRMACAO"
    CONFIRMADO = "CONFIRMADO"
    CANCELADO = "CANCELADO"
    ENTREGUE = "ENTREGUE"


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String(80), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    tentativas_falhas: Mapped[int] = mapped_column(default=0)
    bloqueado_ate: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    telefone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nome: Mapped[str | None] = mapped_column(String(120))
    endereco: Mapped[str | None] = mapped_column(String(255))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pedidos: Mapped[list["Pedido"]] = relationship(back_populates="cliente")


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True)
    unidade: Mapped[str] = mapped_column(String(20), default="kg")  # kg, un, maço, caixa...
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    ativo: Mapped[bool] = mapped_column(default=True)


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"))
    status: Mapped[StatusPedido] = mapped_column(
        Enum(StatusPedido), default=StatusPedido.AGUARDANDO_CONFIRMACAO
    )
    observacao: Mapped[str | None] = mapped_column(String(500))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cliente: Mapped[Cliente] = relationship(back_populates="pedidos")
    itens: Mapped[list["ItemPedido"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan", lazy="selectin"
    )


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"))
    produto_id: Mapped[int | None] = mapped_column(ForeignKey("produtos.id"))
    nome: Mapped[str] = mapped_column(String(120))  # como o cliente falou / normalizado pela LLM
    quantidade: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    unidade: Mapped[str] = mapped_column(String(20), default="un")
    # Preço do catálogo no momento do pedido; None quando o item não casou com um produto.
    preco_unitario: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    pedido: Mapped[Pedido] = relationship(back_populates="itens")


class MensagemProcessada(Base):
    """Ids de mensagem do WhatsApp já tratados; a Evolution pode reenviar o mesmo evento."""

    __tablename__ = "mensagens_processadas"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
