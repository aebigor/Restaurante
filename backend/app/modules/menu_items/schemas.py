from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ==========================================================
# CREAR ELEMENTO DEL MENÚ
# ==========================================================

class MenuItemCreate(BaseModel):

    dish_id: UUID

    display_order: int = 1


# ==========================================================
# INFORMACIÓN DEL PLATO
# ==========================================================

class MenuItemDish(BaseModel):

    id: UUID

    name: str

    price: float

    image: str | None = None

    portion: str | None = None

    category_name: str | None = None

    model_config = ConfigDict(
        from_attributes=True
    )


# ==========================================================
# RESPUESTA
# ==========================================================

class MenuItemResponse(BaseModel):

    id: UUID

    menu_id: UUID

    dish_id: UUID

    display_order: int

    active: bool

    dish: MenuItemDish

    model_config = ConfigDict(
        from_attributes=True
    )