import uuid

from sqlalchemy import (
    String,
    Numeric,
    Boolean,
    Integer,
    ForeignKey,
    Text
)

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.core.database import Base


class Dish(Base):

    __tablename__ = "dishes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=False
    )

    station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stations.id"),
        nullable=False
    )

    preparation_time: Mapped[int] = mapped_column(
        Integer,
        default=10
    )

    portion: Mapped[str] = mapped_column(
        String(100),
        default="1 porción",
        nullable=True
    )

    calories: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    image: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )

    model_3d: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )

    video: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )

    ingredients: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    allergens: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )

    spicy_level: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    available: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    category = relationship("Category")

    station = relationship("Station")
    