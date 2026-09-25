import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    String,
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


class Order(Base):

    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id"),
        nullable=True
    )

    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    order_type: Mapped[str] = mapped_column(
        String(30),
        default="TABLE"
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="OPEN"
    )

    # Código de seguridad de la comanda para mesas con pago anticipado.
    # Caja debe introducirlo para autorizar el paso de la comida a cocina.
    confirmation_code: Mapped[str | None] = mapped_column(
        String(6),
        nullable=True,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    closed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Momento en que el pedido fue entregado físicamente al cliente.
    served_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # ==========================================================
    # PEDIDOS ONLINE / DOMICILIO
    # ==========================================================

    notes: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True
    )

    delivery_address: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True
    )

    delivery_phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )

    cashier_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    dispatched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    delivery_fee: Mapped[float] = mapped_column(default=0, nullable=False)
    delivery_code: Mapped[str | None] = mapped_column(String(12), nullable=True)
    courier_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    courier_assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    courier_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    courier_delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(30), nullable=True)
    payment_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    courier = relationship("User", foreign_keys=[courier_id])

    session = relationship("Session")
    customer = relationship(
        "User",
        foreign_keys=[customer_id]
    )