from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class MeterEntity:
    meter_id: UUID
    code: str
    owner_name: str
    meter_number: str
    address: str
    coordinates: Optional[tuple]
    photo_url: Optional[str]
    comment: Optional[str]
    completion_date: Optional[datetime]

