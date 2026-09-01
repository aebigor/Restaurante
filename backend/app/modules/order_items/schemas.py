from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class OrderItemCreate(BaseModel):

    order_id: UUID

    product_id: UUID | None = None

    dish_id: UUID | None = None

    quantity: int = 1

    notes: str | None = None


class OrderItemResponse(BaseModel):

    id: UUID

    order_id: UUID

    product_id: UUID | None

    dish_id: UUID | None

    quantity: int

    unit_price: Decimal

    total: Decimal

    notes: str | None

    status: str

    class Config:

        from_attributes = True