from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class KitchenQueueCreate(BaseModel):

    station_id: UUID

    order_item_id: UUID


class KitchenQueueResponse(BaseModel):

    id: UUID

    station_id: UUID

    order_item_id: UUID

    status: str

    created_at: datetime

    started_at: datetime | None

    finished_at: datetime | None

    class Config:

        from_attributes = True