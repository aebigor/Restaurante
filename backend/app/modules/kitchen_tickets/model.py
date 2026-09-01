import uuid

from sqlalchemy import (
    String,
    ForeignKey
)

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.core.database import Base


class KitchenTicket(Base):

    __tablename__ = "kitchen_tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("order_batches.id"),
        nullable=False
    )

    station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stations.id"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="WAITING"
    )

    batch = relationship("OrderBatch")

    station = relationship("Station")