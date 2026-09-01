from typing import Optional

from pydantic import BaseModel
from pydantic import Field


# ==========================================
# BASE
# ==========================================

class TableBase(BaseModel):

    number: int = Field(..., gt=0)

    name: str

    capacity: int = Field(default=4, gt=0)

    zone: str = "Salón"

    active: bool = True


# ==========================================
# CREAR
# ==========================================

class TableCreate(TableBase):
    pass


# ==========================================
# ACTUALIZAR
# ==========================================

class TableUpdate(BaseModel):

    number: Optional[int] = Field(default=None, gt=0)

    name: Optional[str] = None

    capacity: Optional[int] = Field(default=None, gt=0)

    zone: Optional[str] = None

    active: Optional[bool] = None


# ==========================================
# RESPUESTA
# ==========================================

class TableResponse(TableBase):

    id: int

    class Config:

        from_attributes = True