from uuid import UUID
from pydantic import BaseModel, Field


class StationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str | None = None
    printer_name: str | None = None
    color: str = "#3498db"
    auto_print: bool = False
    sound_notification: bool = True
    accepts_delivery: bool = True
    supports_queue: bool = True


class StationResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    printer_name: str | None = None
    color: str
    priority: int
    auto_print: bool
    sound_notification: bool
    accepts_delivery: bool
    supports_queue: bool
    active: bool

    class Config:
        from_attributes = True
