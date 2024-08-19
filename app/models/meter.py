from enum import Enum

from uuid6 import uuid7
from sqlalchemy import Column, String, DateTime, Float, Text, UUID, Enum

from app.db.session import Base
from app.value_objects.status import StatusState


class Meter(Base):
    __tablename__ ="meter"

    meter_id = Column(UUID, primary_key=True, default=uuid7)
    code = Column(String, nullable=False)
    owner_name = Column(String, nullable=False)
    meter_number = Column(String, nullable=False)
    address = Column(String, nullable=False)
    supervisor = Column(String, nullable=True)
    current_reading = Column(Float, nullable=True)
    previous_reading = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    photo1_url = Column(String, nullable=True)
    photo2_url = Column(String, nullable=True)
    comment = Column(Text, nullable=True)
    status: Column[str | Enum] = Column(Enum(StatusState), default=StatusState.EXECUTING)
    completion_date = Column(DateTime, nullable=True)

