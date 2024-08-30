from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.meter import MeterRepository
from app.schema.meter import MeterCreate, MeterUpdate
from app.schema.user import UserInDB
from app.utils.excel.excel import get_file_from_database
from app.value_objects.status import StatusState


class MeterService:
    def __init__(self, db: AsyncSession):
        self.repository = MeterRepository(db)

    async def create(self, meter: MeterCreate):
        return await self.repository.create_meter(meter)

    async def update(self, meter_id: UUID, meter: MeterUpdate, user: UserInDB):
        return await self.repository.update_meter(meter_id, meter, user)

    async def read_meters(self, offset: int, limit: int, order: str):
        return await self.repository.read_all_meters(offset, limit, order)

    async def get_meters(self, status_filter: StatusState):
        meters = await self.repository.findall(status_filter=status_filter)
        return meters

    async def get_meter(self, meter_id: UUID):
        meter = await self.repository.find_meter(meter_id)
        return meter

    async def delete_all_meters(self):
        await self.repository.delete_meters()

    async def get_meters_by_user_department(self, department: str, status: StatusState = StatusState.EXECUTING, supervisor: str = None):
        meters = await self.repository.get_meters_by_user_department(department, status, supervisor)
        return meters

    async def find_completed_meters(self):
        meters = await self.repository.find_completed_meters()
        return meters

    async def get_completed_meters(self):
        meters = await self.repository.get_completed_meters()
        file = get_file_from_database(meters)
        return file
    
    async def get_completed_meters_by_supervisor(self, supervisor: str):
        meters = await self.repository.get_completed_meters_by_supervisor(supervisor)
        return meters