from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Boolean

from app.core.database import Base


class Table(Base):

    __tablename__ = "tables"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    number = Column(
        Integer,
        unique=True,
        nullable=False
    )

    name = Column(
        String(100),
        nullable=False
    )

    capacity = Column(
        Integer,
        default=4
    )

    zone = Column(
        String(50),
        default="Salón"
    )

    active = Column(
        Boolean,
        default=True
    )