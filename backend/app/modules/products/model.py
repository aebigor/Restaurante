import uuid

from sqlalchemy import (
    String,
    Numeric,
    Boolean,
    ForeignKey,
    Integer
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.core.database import Base


class Product(Base):

    __tablename__ = "products"


    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )


    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )


    code: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        unique=True
    )


    description: Mapped[str] = mapped_column(
        String(300),
        nullable=True
    )


    price: Mapped[float] = mapped_column(
        Numeric(10,2),
        nullable=False
    )


    preparation_time: Mapped[int] = mapped_column(
        Integer,
        default=10
    )


    stock: Mapped[int] = mapped_column(
        Integer,
        default=0
    )


    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
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


    category = relationship(
        "Category",
        back_populates="products"
    )


    station = relationship(
        "Station",
        back_populates="products"
    )