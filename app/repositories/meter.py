from typing import List, Tuple, Optional
from fastapi import HTTPException, status
import requests
from sqlalchemy import asc, desc, func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid6 import uuid7
from app.models.meter import Meter
from app.schema.meter import MeterCreate, MeterUpdate
from app.schema.user import UserInDB
from app.utils.metadata import PhotoMetadata
from app.value_objects.status import StatusState, Status


class MeterRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def read_all_meters(self, offset: int, limit: int, order: str) -> Tuple[List[Meter], int]:
        order_by_clause = asc(Meter.completion_date) if order.lower() == 'asc' else desc(Meter.completion_date)
        query = select(Meter).order_by(order_by_clause)
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        meters = await self.db.scalars(query.offset(offset).limit(limit))
        return meters.all(), total

    async def findall(self, status_filter: StatusState) -> List[Meter]:
        query = select(Meter).filter(Meter.status == status_filter)
        result = await self.db.scalars(query)
        return result.all()

    async def create_meter(self, meter: MeterCreate) -> Meter:
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
        await self.db.commit()
        await self.db.refresh(db_meter)
        return db_meter

    async def update_meter(self, meter_id: str, update_meter: MeterUpdate, user: UserInDB) -> Optional[Meter]:
        result = await self.db.execute(select(Meter).filter(Meter.meter_id == meter_id))
        db_meter = result.scalar_one_or_none()
        if not db_meter:
            return None
        for key, value in update_meter.dict(exclude_unset=True).items():
            setattr(db_meter, key, value)
        response = requests.get(db_meter.photo1_url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Échec du téléchargement de la photo depuis l'URL")
        photo_metadata = PhotoMetadata()
        coordinates = photo_metadata.get_coordinates(response.content)
        if not coordinates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucune coordonnée GPS trouvée dans la photo1"
            )
        db_meter.latitude = coordinates.latitude
        db_meter.longitude = coordinates.longitude
        db_meter.status = StatusState.CHECKING
        db_meter.supervisor = user.username
        await self.db.commit()
        await self.db.refresh(db_meter)
        return db_meter

    async def delete_meters(self):
        await self.db.execute(delete(Meter))
        await self.db.commit()

    async def find_meter(self, meter_id: str) -> Optional[Meter]:
        result = await self.db.execute(select(Meter).filter(Meter.meter_id == meter_id))
        meter = result.scalar_one_or_none()
        return meter

    async def get_meters_by_user_department(self, department: str, status: StatusState = StatusState.EXECUTING, supervisor: str = None) -> List[Meter]:
        query = select(Meter).filter(Meter.code.like(f"{department}%")).filter(Meter.status == status)
        if status == StatusState.CHECKING and supervisor:
            query = query.filter(Meter.supervisor == supervisor)
        result = await self.db.scalars(query)
        return result.all()

    async def find_completed_meters(self) -> List[Meter]:
        status_filter = StatusState.CHECKING
        result = await self.db.scalars(select(Meter).filter(Meter.status == status_filter))
        return result.all()

    async def get_completed_meters(self) -> List[Meter]:
        status: StatusState = StatusState.CHECKING
        result = await self.db.scalars(select(Meter).filter(Meter.status == status).order_by(desc(Meter.completion_date)))
        return result.all()
    
    async def get_completed_meters_by_supervisor(self, supervisor: str) -> List[Meter]:
        results = await self.db.scalars(select(Meter).filter(Meter.supervisor == supervisor))
        return results