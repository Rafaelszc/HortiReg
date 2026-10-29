from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Precificacao(Base):
    __tablename__ = "precificacoes"

    __table_args__ = (
        CheckConstraint("preco > 0", name="ck_precificacao_preco_positivo"),
        UniqueConstraint(
            "produto_id",
            "unidade",
            name="uq_precificacao_produto_unidade",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"),
        nullable=False,
        index=True,
    )

    unidade: Mapped[str] = mapped_column(String(40), nullable=False)

    preco: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    produto: Mapped["Produto"] = relationship(
        back_populates="precificacoes",
    )