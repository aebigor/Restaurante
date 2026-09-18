from uuid import UUID
from pydantic import BaseModel
from datetime import datetime


class OrderCreate(BaseModel):

    session_id: UUID


class OrderResponse(BaseModel):

    id: UUID

    session_id: UUID

    status: str

    created_at: datetime

    closed_at: datetime | None

    class Config:

        from_attributes = True

class CustomerOrderItem(BaseModel):
    dish_id: UUID
    quantity: int = 1
    notes: str | None = None


class CustomerOrderCreate(BaseModel):
    items: list[CustomerOrderItem]
    order_type: str = "ONLINE"
    notes: str | None = None
    delivery_address: str | None = None
    delivery_phone: str | None = None
