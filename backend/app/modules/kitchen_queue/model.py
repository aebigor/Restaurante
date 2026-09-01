import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    ForeignKey,
    DateTime
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    mapped_column,
    Mapped,
    relationship
)

from app.core.database import Base


class KitchenQueue(Base):

    __tablename__ = "kitchen_queue"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stations.id"),
        nullable=False
    )

    order_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("order_items.id"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="WAITING"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )

    finished_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )

    station = relationship("Station")

    order_item = relationship("OrderItem")