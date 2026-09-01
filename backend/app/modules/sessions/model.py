import uuid

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Session(Base):

    __tablename__ = "sessions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    table_id = Column(
        Integer,
        ForeignKey("tables.id"),
        nullable=False
    )

    waiter_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    people = Column(Integer)

    status = Column(
        String,
        default="OPEN"
    )

    opened_at = Column(DateTime)

    closed_at = Column(DateTime)

    # Relaciones
    table = relationship("Table")
    waiter = relationship("User")