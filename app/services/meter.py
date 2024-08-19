from uuid import UUID
from sqlalchemy.orm import Session

from app.repositories.meter import MeterRepository
from app.schema.meter import MeterCreate, MeterUpdate
from app.schema.user import UserInDB
from app.utils.excel.excel import get_file_from_database
from app.value_objects.status import StatusState, Status


class MeterService:
    def __init__(self, db: Session):
        self.repository = MeterRepository(db)

    def create(self, meter: MeterCreate):
        return self.repository.create_meter(meter)

    def update(self, meter_id: UUID, meter: MeterUpdate, user: UserInDB):
        return self.repository.update_meter(meter_id, meter, user)

    def read_meters(self, offset: int, limit: int, order: str):
        return self.repository.read_all_meters(offset, limit, order)

    def get_meters(self, status_filter: StatusState):
        meters = self.repository.findall(status_filter=status_filter)
        return meters

    def get_meter(self, meter_id: UUID):
        meter = self.repository.find_meter(meter_id)
        return meter

    def delete_all_meters(self):
        self.repository.delete_meters()

    def get_meters_by_user_department(self, department: str, status: StatusState = StatusState.EXECUTING):
        meters = self.repository.get_meters_by_user_department(department, status)
        return meters

    def find_completed_meters(self):
        meters = self.repository.find_completed_meters()
        return meters

    def get_completed_meters(self):
        meters = self.repository.get_completed_meters()
        file = get_file_from_database(meters)
        return file



