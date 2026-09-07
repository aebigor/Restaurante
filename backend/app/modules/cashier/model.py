import uuid

from datetime import datetime

from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
    func
)

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.core.database import Base


# ==========================================================
# CAJA
# ==========================================================

class CashRegister(Base):

    __tablename__ = "cash_registers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    opened_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    opening_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="OPEN",
        nullable=False
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    closing_amount: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

    expected_cash: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

    difference: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

    opened_by_user = relationship(
        "User"
    )


# ==========================================================
# PAGOS
# ==========================================================

class CashPayment(Base):

    __tablename__ = "cash_payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    cash_register_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cash_registers.id"),
        nullable=False
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id"),
        nullable=False
    )

    cashier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    method: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    received_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    change_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        nullable=False
    )

    reference: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    cash_register = relationship(
        "CashRegister"
    )

    session = relationship(
        "Session"
    )

    cashier = relationship(
        "User"
    )