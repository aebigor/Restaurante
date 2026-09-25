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

    # Si esta mesa exige pago antes de enviar la comanda a cocina.
    prepayment_required = Column(
        Boolean,
        default=False,
        nullable=False
    )

    # 1 = comanda primero, 2 = normal, 3 = comanda última.
    comanda_print_priority = Column(
        Integer,
        default=2,
        nullable=False
    )