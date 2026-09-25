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

    prepayment_required: bool = False

    comanda_print_priority: int = Field(default=2, ge=1, le=3)


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

    prepayment_required: Optional[bool] = None

    comanda_print_priority: Optional[int] = Field(default=None, ge=1, le=3)


# ==========================================
# RESPUESTA
# ==========================================

class TableResponse(TableBase):

    id: int

    class Config:

        from_attributes = True