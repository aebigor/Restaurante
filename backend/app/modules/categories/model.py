from __future__ import annotations

import uuid

from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.core.database import Base


class Category(Base):

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )

    color: Mapped[str] = mapped_column(
        String(20),
        default="#b40000"
    )

    icon: Mapped[str] = mapped_column(
        String(30),
        default="🍔"
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    station_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stations.id"), nullable=True
    )

    station = relationship("Station")

    @property
    def station_name(self):
        return self.station.name if self.station else None

    products = relationship(
        "Product",
        back_populates="category"
    )