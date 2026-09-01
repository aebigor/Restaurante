import uuid

from sqlalchemy import String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    color: Mapped[str] = mapped_column(String(20), nullable=False, default="#3498db")
    printer_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    auto_print: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sound_notification: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    accepts_delivery: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    supports_queue: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    products = relationship("Product", back_populates="station")
