from __future__ import annotations

import uuid

from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    Integer,
    DateTime
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.core.database import Base


class Menu(Base):

    __tablename__ = "menus"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    title: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        unique=True
    )

    slug: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True
    )

    description: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True
    )

    cover_image: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    items = relationship(
        "MenuItem",
        back_populates="menu",
        cascade="all, delete-orphan"
    )