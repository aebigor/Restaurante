import uuid

from datetime import datetime

from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Integer,
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

    # Corrección administrativa del efectivo contado.
    # El servidor permite como máximo UNA corrección y solamente
    # durante el mismo día calendario del cierre.
    closing_amount_edit_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    closing_amount_edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    closing_amount_edited_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )

    closing_amount_edit_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    opened_by_user = relationship(
        "User",
        foreign_keys=[opened_by]
    )

    closing_amount_edited_by_user = relationship(
        "User",
        foreign_keys=[closing_amount_edited_by]
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

    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id"),
        nullable=True
    )

    # Pedido online/domicilio asociado al cobro. Permite que las ventas
    # de domicilio también entren al arqueo de Caja sin inventar una sesión.
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=True,
        unique=True
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

    order = relationship(
        "Order"
    )

    cashier = relationship(
        "User"
    )

# ==========================================================
# MOVIMIENTOS DE EFECTIVO DE LA CAJA
# ==========================================================

class CashRegisterMovement(Base):
    __tablename__ = "cash_register_movements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    cash_register_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cash_registers.id"), nullable=False, index=True
    )

    cashier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    movement_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="WITHDRAWAL"
    )

    amount: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    recipient_name: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    recipient_document: Mapped[str] = mapped_column(
        String(50), nullable=False
    )

    reason: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    cash_register = relationship("CashRegister")
    cashier = relationship("User")
