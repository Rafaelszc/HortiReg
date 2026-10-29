from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"))
    produto_id: Mapped[int | None] = mapped_column(ForeignKey("produtos.id"))
    nome: Mapped[str] = mapped_column(String(120))
    quantidade: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    unidade: Mapped[str] = mapped_column(String(20), default="un")

    pedido: Mapped["Pedido"] = relationship(back_populates="itens")
