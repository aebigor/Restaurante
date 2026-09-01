from uuid import UUID
from pydantic import BaseModel, Field

class WaiterSessionCreate(BaseModel):
    table_number: int
    people: int = Field(default=1, ge=1, le=50)

class WaiterOrderItem(BaseModel):
    dish_id: UUID
    quantity: int = Field(default=1, ge=1, le=99)
    notes: str | None = None

class WaiterOrderCreate(BaseModel):
    # El mesero puede enviar el pedido usando una sesión existente
    # o directamente con la mesa. Si no existe sesión, el backend
    # la crea automáticamente.
    session_id: UUID | None = None
    table_id: int | None = None
    people: int = Field(default=1, ge=1, le=50)
    items: list[WaiterOrderItem] = Field(min_length=1)
