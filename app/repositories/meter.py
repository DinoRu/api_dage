import requests
from typing import List, Tuple

from fastapi import HTTPException
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session
from starlette import status
from uuid6 import uuid7
from app.models.meter import Meter
from app.schema.meter import MeterCreate, MeterUpdate
from app.schema.user import UserInDB
from app.utils.metadata import PhotoMetadata
from app.value_objects.status import StatusState, Status


class MeterRepository:
    def __init__(self, db: Session):
        self.db = db

    def read_all_meters(self, offset: int, limit: int, order: str) -> Tuple[List[Meter], int]:
        order_by_clause = asc(Meter.completion_date) if order.lower() == 'asc' else desc(Meter.completion_date)
        query = self.db.query(Meter).order_by(order_by_clause)
        total = query.count()
        meters = query.offset(offset).limit(limit).all()
        return meters, total

    def findall(self, status_filter: StatusState) ->List[Meter]:
        query = self.db.query(Meter)
        meters = query.filter(Meter.status == status_filter)
        return meters

    def create_meter(self, meter: MeterCreate) -> Meter:
        db_meter = Meter(
            meter_id=uuid7(),
            code=meter.code,
            address=meter.address,
            owner_name=meter.owner_name,
            supervisor=meter.supervisor,
            meter_number=meter.meter_number,
            comment=meter.comment,
            photo1_url=meter.photo1_url,
            photo2_url=meter.photo2_url,
            longitude=meter.longitude,
            latitude=meter.latitude,
            previous_reading=meter.previous_reading,
            current_reading=meter.current_reading,
            completion_date=meter.completion_date
        )
        self.db.add(db_meter)
        self.db.commit()
        self.db.refresh(db_meter)
        return db_meter

    def update_meter(self, meter_id, update_meter: MeterUpdate, user: UserInDB):
        db_meter = self.db.query(Meter).filter(Meter.meter_id == meter_id).first()
        if not db_meter:
            return None
        for key, value in update_meter.dict(exclude_unset=True).items():
            setattr(db_meter, key, value)
        response = requests.get(db_meter.photo1_url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download photo from URL")
        photo_metadata = PhotoMetadata()
        coordinates = photo_metadata.get_coordinates(response.content)
        if not coordinates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No GPS coordinates found in photo1"
            )
        db_meter.latitude = coordinates.latitude
        db_meter.longitude = coordinates.longitude
        db_meter.status = StatusState.CHECKING
        db_meter.supervisor = user.username
        self.db.commit()
        self.db.refresh(db_meter)
        return db_meter

    def delete_meters(self):
        self.db.query(Meter).delete()
        self.db.commit()

    def find_meter(self, meter_id):
        meter = self.db.query(Meter).filter(Meter.meter_id == meter_id).first()
        return meter

    def get_meters_by_user_department(self, department: str, status: StatusState = StatusState.EXECUTING):
        meters = self.db.query(Meter).filter(Meter.code.like(f"{department}%")).filter(Meter.status == status)
        return meters

    def find_completed_meters(self):
        status_filter = StatusState.CHECKING
        meters = self.db.query(Meter).filter(Meter.status == status_filter)
        return meters

    def get_completed_meters(self) -> List[Meter]:
        status: StatusState = StatusState.CHECKING
        meters = self.db.query(Meter).filter(Meter.status == status).order_by(desc(Meter.completion_date)).all()
        return meters



