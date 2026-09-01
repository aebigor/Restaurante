from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class WaiterCallCreate(BaseModel):
    table_id: int
    session_id: UUID | None = None

class WaiterCallUpdate(BaseModel):
    status: str
    waiter_id: UUID | None = None

class WaiterCallResponse(BaseModel):
    id: UUID
    table_id: int
    session_id: UUID | None
    waiter_id: UUID | None
    status: str
    requested_at: datetime
    acknowledged_at: datetime | None
    attended_at: datetime | None
    class Config:
        from_attributes = True
