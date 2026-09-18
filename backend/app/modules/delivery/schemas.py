from pydantic import BaseModel, Field
from uuid import UUID

class LocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy: float | None = Field(default=None, ge=0)

class DeliveryMessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    order_id: UUID | None = None
    recipient_id: UUID | None = None

class CancelDelivery(BaseModel):
    reason: str = Field(min_length=1, max_length=300)

class DeliveryConfirm(BaseModel):
    code: str = Field(min_length=4, max_length=12)

class PaymentClose(BaseModel):
    payment_method: str
