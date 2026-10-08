from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class ProductInventoryRecipeInput(BaseModel):
    inventory_item_id: UUID
    quantity_per_sale: Decimal = Field(gt=0)

class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    code: str | None = None
    description: str | None = None
    price: Decimal = Field(gt=0)
    preparation_time: int = Field(default=0, ge=0)
    stock: int = Field(default=0, ge=0)
    active: bool = True
    category_id: UUID
    station_id: UUID
    inventory_recipe: list[ProductInventoryRecipeInput] = Field(default_factory=list)

class ProductResponse(BaseModel):
    id: UUID
    name: str
    code: str | None = None
    description: str | None = None
    price: Decimal
    preparation_time: int
    stock: int
    active: bool
    category_id: UUID
    station_id: UUID
    category: str | None = None
    station: str | None = None
    inventory_recipe: list[dict] = Field(default_factory=list)
    inventory_controlled: bool = False
    model_config = ConfigDict(from_attributes=True)
