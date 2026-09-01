from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ==========================================================
# CREAR PLATO
# ==========================================================

class DishCreate(BaseModel):

    name: str

    price: Decimal

    category_id: UUID

    station_id: UUID

    preparation_time: int = 10

    portion: str | None = "1 porción"

    image: str | None = None

    featured: bool = False

    available: bool = True


# ==========================================================
# RESPUESTA
# ==========================================================

class DishResponse(BaseModel):

    id: UUID

    name: str

    price: Decimal

    category_id: UUID

    station_id: UUID

    preparation_time: int

    portion: str | None

    image: str | None

    featured: bool

    available: bool

    active: bool

    # ------------------------------------------------------
    # INFORMACIÓN PARA MOSTRAR EN EL DASHBOARD
    # ------------------------------------------------------

    category_name: str | None = None

    station_name: str | None = None

    model_config = ConfigDict(
        from_attributes=True
    )