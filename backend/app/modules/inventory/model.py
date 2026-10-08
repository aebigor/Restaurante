import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    sku: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, default="General")
    item_type: Mapped[str] = mapped_column(String(40), nullable=False, default="INGREDIENTE")
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    presentation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="unidad")
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    min_quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    max_quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    reorder_quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    unit_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    storage: Mapped[str | None] = mapped_column(String(80), nullable=True)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    opened_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    storage_temperature: Mapped[str | None] = mapped_column(String(80), nullable=True)
    supplier: Mapped[str | None] = mapped_column(String(160), nullable=True)
    allergen: Mapped[str | None] = mapped_column(String(160), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    movements = relationship("InventoryMovement", back_populates="item", cascade="all, delete-orphan")


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True)
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    item = relationship("InventoryItem", back_populates="movements")
