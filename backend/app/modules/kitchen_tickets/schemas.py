from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class KitchenTicketCreate(BaseModel):

    order_item_id: UUID

    station_id: UUID


class KitchenTicketResponse(BaseModel):

    id: UUID

    order_item_id: UUID

    station_id: UUID

    status: str

    priority: int

    display_order: int

    created_at: datetime

    started_at: datetime | None

    finished_at: datetime | None

    class Config:

        from_attributes = True