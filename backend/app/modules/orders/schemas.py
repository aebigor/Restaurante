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