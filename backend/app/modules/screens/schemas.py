from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
class ScreenCreate(BaseModel):
    station_id: UUID
    name: str
    code: str
class ScreenResponse(BaseModel):
    id: UUID
    station_id: UUID
    name: str
    code: str
    active: bool
    last_seen_at: datetime | None
    class Config:
        from_attributes = True
