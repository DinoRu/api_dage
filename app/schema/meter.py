from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel

from app.value_objects.status import StatusState


class MeterCreate(BaseModel):
    meter_id: UUID
    code: str
    owner_name: str
    meter_number: str
    address: str
    previous_reading: Optional[float | None]
    current_reading: Optional[float | None]
    latitude: float | None
    longitude: float | None
    comment: str | None
    supervisor: Optional[str | None]
    photo1_url: Optional[str]
    photo2_url: Optional[str]
    status: StatusState = StatusState.EXECUTING
    completion_date: Optional[datetime | None]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class MeterUpdate(BaseModel):
    current_reading: float
    photo1_url: str
    photo2_url: str
    comment: str | None


class Meter(BaseModel):
    meter_id: UUID
    code: str
    owner_name: str
    meter_number: str
    address: str
    previous_reading: float | None
    current_reading: float | None
    latitude: float | None
    longitude: float | None
    supervisor: str | None
    photo1_url: str | None
    photo2_url: str | None
    comment: str | None
    status: StatusState = StatusState.EXECUTING
    created_at: Optional[datetime | None]
    completion_date: datetime | None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        

class Pagination(BaseModel):
    offset: int
    limit: int
    total: int
    order: str


class Result(BaseModel):
    data: List[dict]
    pagination: Pagination


class ResponseModel(BaseModel):
    status: int
    result: Result
