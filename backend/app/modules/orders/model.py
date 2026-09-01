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
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="OPEN"
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
    served_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    session = relationship("Session")