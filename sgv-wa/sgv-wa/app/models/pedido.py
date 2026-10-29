from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.status_pedido import StatusPedido


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"))
    status: Mapped[StatusPedido] = mapped_column(
        Enum(StatusPedido), default=StatusPedido.AGUARDANDO_CONFIRMACAO
    )
    observacao: Mapped[str | None] = mapped_column(String(500))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cliente: Mapped["Cliente"] = relationship(back_populates="pedidos")
    itens: Mapped[list["ItemPedido"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan", lazy="selectin"
    )
