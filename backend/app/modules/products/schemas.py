from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class ProductCreate(BaseModel):

    name: str

    code: str | None = None

    description: str | None = None

    price: Decimal

    preparation_time: int = 10

    stock: int = 0

    category_id: UUID

    station: str