from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ==========================================
# BASE
# ==========================================

class CategoryBase(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=120
    )

    description: Optional[str] = None

    color: str = "#b40000"

    icon: str = "🍔"

    display_order: int = 1

    active: bool = True

    station_id: UUID

    station_name: Optional[str] = None


# ==========================================
# CREAR
# ==========================================

class CategoryCreate(CategoryBase):
    pass


# ==========================================
# ACTUALIZAR
# ==========================================

class CategoryUpdate(BaseModel):

    name: Optional[str] = None

    description: Optional[str] = None

    color: Optional[str] = None

    icon: Optional[str] = None

    display_order: Optional[int] = None

    active: Optional[bool] = None

    station_id: Optional[UUID] = None


# ==========================================
# RESPUESTA
# ==========================================

class CategoryResponse(CategoryBase):

    id: UUID

    class Config:

        from_attributes = True