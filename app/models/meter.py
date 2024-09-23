
from uuid import UUID
from datetime import datetime
from uuid6 import uuid7
from sqlalchemy import DateTime, Float, String, Text, sql, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from app.value_objects.status import StatusState



class TimedBaseModel(Base):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=sql.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=sql.func.now(),
        onupdate=sql.func.now())


class Meter(TimedBaseModel):
    __tablename__ = "meters"

    meter_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7())
    code: Mapped[str] = mapped_column(String, nullable=False)
    owner_name: Mapped[str] = mapped_column(String, nullable=False, default=None)
    address: Mapped[str] = mapped_column(String, nullable=False, default=None)
    meter_number: Mapped[str] = mapped_column(String(255))
    supervisor: Mapped[str | None] = mapped_column(String(255), default=None)
    current_reading: Mapped[float | None] = mapped_column(Float, default=None)
    previous_reading: Mapped[float | None] = mapped_column(Float, default=None)
    latitude: Mapped[float | None] = mapped_column(Float, default=None)
    longitude: Mapped[float | None] = mapped_column(Float, default=None)
    comment: Mapped[Text | None] = mapped_column(Text, default=None)
    photo1_url: Mapped[str | None] = mapped_column(String, default=None)
    photo2_url: Mapped[str | None] = mapped_column(String, default=None)
    status: Mapped[StatusState] = mapped_column(Enum(StatusState), default=StatusState.EXECUTING)
    completion_date: Mapped[datetime | None] = mapped_column(DateTime, default=None)
