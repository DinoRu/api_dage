"""Meter service."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException, ForbiddenException
from app.core.pagination import PaginationParams, PageResponse
from app.models.meter import Meter, MeterStatus
from app.models.user import User
from app.schema.meter import MeterCreate, MeterUpdate
from app.services.base import BaseService


class MeterService(BaseService[Meter, MeterCreate, MeterUpdate]):
    """Meter service with business logic."""
    
    def __init__(self):
        super().__init__(Meter)
    
    async def get_by_code(
        self,
        db: AsyncSession,
        code: str
    ) -> Optional[Meter]:
        """Get meter by code."""
        result = await db.execute(
            select(Meter).where(Meter.code == code)
        )
        return result.scalar_one_or_none()
    
    async def get_by_meter_number(
        self,
        db: AsyncSession,
        meter_number: str
    ) -> Optional[Meter]:
        """Get meter by meter number."""
        result = await db.execute(
            select(Meter).where(Meter.meter_number == meter_number)
        )
        return result.scalar_one_or_none()
    
    async def create(
        self,
        db: AsyncSession,
        obj_in: MeterCreate,
        **kwargs
    ) -> Meter:
        """Create a new meter."""
        # Check if code exists
        existing_code = await self.get_by_code(db, obj_in.code)
        if existing_code:
            raise ConflictException(f"Meter with code '{obj_in.code}' already exists")
        
        # Check if meter number exists
        existing_number = await self.get_by_meter_number(db, obj_in.meter_number)
        if existing_number:
            raise ConflictException(
                f"Meter with number '{obj_in.meter_number}' already exists"
            )
        
        return await super().create(db, obj_in, **kwargs)
    
    async def get_by_city(
        self,
        db: AsyncSession,
        city_id: UUID,
        pagination: PaginationParams,
        status: Optional[MeterStatus] = None
    ) -> PageResponse[Meter]:
        """Get meters by city."""
        filters = {"city_id": city_id}
        if status:
            filters["status"] = status.value
        
        return await self.get_multi(db, pagination, filters, order_by="code")
    
    async def get_with_stats(
        self,
        db: AsyncSession,
        id: UUID
    ) -> dict:
        """Get meter with statistics."""
        meter = await self.get_or_404(db, id)
        
        # Count readings
        from app.models.readings import Reading
        
        readings_count = await db.scalar(
            select(func.count()).where(Reading.meter_id == id)
        ) or 0
        
        # Get last reading
        last_reading = await db.execute(
            select(Reading)
            .where(Reading.meter_id == id)
            .order_by(Reading.reading_date.desc())
            .limit(1)
        )
        last_reading_obj = last_reading.scalar_one_or_none()
        
        # Calculate average consumption
        avg_consumption = await db.scalar(
            select(func.avg(Reading.reading_value)).where(Reading.meter_id == id)
        )
        
        return {
            **meter.__dict__,
            "readings_count": readings_count,
            "last_reading_value": last_reading_obj.reading_value if last_reading_obj else None,
            "last_reading_date": last_reading_obj.reading_date.isoformat() if last_reading_obj else None,
            "average_consumption": float(avg_consumption) if avg_consumption else None
        }
    
    async def update_status(
        self,
        db: AsyncSession,
        id: UUID,
        status: MeterStatus,
        user: User
    ) -> Meter:
        """Update meter status."""
        # Only admins and supervisors can change status
        if not (user.is_admin() or user.is_supervisor()):
            raise ForbiddenException("Only admins and supervisors can change meter status")
        
        meter = await self.get_or_404(db, id)
        meter.status = status.value
        
        await db.commit()
        await db.refresh(meter)
        
        return meter
    
    async def search(
        self,
        db: AsyncSession,
        query: str,
        city_id: Optional[UUID],
        pagination: PaginationParams
    ) -> PageResponse[Meter]:
        """Search meters by code, owner name, or address."""
        stmt = select(Meter).where(
            and_(
                (
                    Meter.code.ilike(f"%{query}%") |
                    Meter.owner_name.ilike(f"%{query}%") |
                    Meter.address.ilike(f"%{query}%") |
                    Meter.meter_number.ilike(f"%{query}%")
                ),
                Meter.city_id == city_id if city_id else True
            )
        ).order_by(Meter.code)
        
        # Count total
        count_query = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_query)
        
        # Apply pagination
        stmt = stmt.offset(pagination.skip).limit(pagination.limit)
        
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        return PageResponse.create(items, total or 0, pagination)
    
    async def check_city_access(
        self,
        db: AsyncSession,
        meter_id: UUID,
        user: User
    ) -> bool:
        """Check if user has access to meter's city."""
        meter = await self.get_or_404(db, meter_id)
        
        # Admins have access to all
        if user.is_admin():
            return True
        
        # Check if user's city matches meter's city
        if user.city_id == meter.city_id:
            return True
        
        return False


meter_service = MeterService()