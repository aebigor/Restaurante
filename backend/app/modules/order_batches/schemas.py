from uuid import UUID

from pydantic import BaseModel


class OrderBatchCreate(BaseModel):

    order_id: UUID

    station_id: UUID


class OrderBatchResponse(OrderBatchCreate):

    id: UUID

    status: str

    class Config:

        from_attributes = True