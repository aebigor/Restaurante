from uuid import UUID
from pydantic import BaseModel, Field

class PromotionCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    description: str | None = None
    promo_type: str = Field(default="PROMO", pattern="^(PROMO|COMBO)$")
    price: float | None = Field(default=None, ge=0)
    image_url: str | None = Field(default=None, max_length=500)
    display_order: int = Field(default=1, ge=1)
    active: bool = True

class PromotionUpdate(PromotionCreate):
    pass

class PromotionResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    promo_type: str
    price: float | None
    image_url: str | None
    display_order: int
    active: bool
    class Config:
        from_attributes = True
