import uuid

from sqlalchemy import (
    Integer,
    ForeignKey,
    Numeric,
    String
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class OrderItem(Base):

    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=False
    )

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=True
    )

    dish_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dishes.id"),
        nullable=True
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    unit_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    total: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    notes: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING"
    )

    # ======================================================
    # RELACIONES
    # ======================================================

    product = relationship(
        "Product"
    )

    dish = relationship(
        "Dish"
    )