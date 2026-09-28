from datetime import date, time
from uuid import UUID
from pydantic import BaseModel, Field


class DeviceRegisterRequest(BaseModel):
    device_uuid: str = Field(min_length=8, max_length=100)
    name: str | None = Field(default=None, max_length=100)


class DeviceStatusRequest(BaseModel):
    device_uuid: str
    device_secret: str


class DeviceApproveRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class AttendanceCheckRequest(BaseModel):
    device_token: str = Field(min_length=20)
    qr_token: str = Field(min_length=10, max_length=80)
    pin: str = Field(min_length=4, max_length=12)


class UserCreateAdmin(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: str
    password: str = Field(min_length=6, max_length=128)
    role_id: UUID
    active: bool = True
    attendance_enabled: bool = True
    attendance_pin: str | None = Field(default=None, min_length=4, max_length=12)


class UserUpdateAdmin(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: str | None = None
    role_id: UUID | None = None
    active: bool | None = None
    attendance_enabled: bool | None = None
    attendance_pin: str | None = Field(default=None, min_length=4, max_length=12)


class ScheduleItem(BaseModel):
    weekday: int = Field(ge=0, le=6)
    enabled: bool = False
    start_time: time | None = None
    end_time: time | None = None
    tolerance_minutes: int = Field(default=5, ge=0, le=120)


class ScheduleUpdate(BaseModel):
    schedules: list[ScheduleItem]


class AttendanceAdjustment(BaseModel):
    user_id: UUID
    work_date: date
    adjustment_minutes: int = Field(ge=-1440, le=1440)
    reason: str = Field(min_length=3, max_length=500)
