"""Reading service."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import logging

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, ForbiddenException
from app.core.pagination import PaginationParams, PageResponse
from app.models.readings import Reading
from app.models.user import User
from app.schema.reading import ReadingCreate, ReadingUpdate
from app.services.base import BaseService
from app.services.meter_v2 import meter_service
from app.services.upload_service import upload_service

logger = logging.getLogger(__name__)


class ReadingService(BaseService[Reading, ReadingCreate, ReadingUpdate]):
    """Reading service with business logic."""
    
    def __init__(self):
        super().__init__(Reading)
    
    async def create(
        self,
        db: AsyncSession,
        obj_in: ReadingCreate,
        current_user: User,
        **kwargs
    ) -> Reading:
        """
        Create a new reading.
        
        Validates:
        - Meter exists and user has access
        - Reading value is >= previous reading
        - At least 2 photos are provided
        - Photo URLs are valid
        """
        # Verify meter exists and user has access
        meter = await meter_service.get_or_404(db, obj_in.meter_id)
        
        # Check access
        if not current_user.is_admin() and meter.city_id != current_user.city_id:
            raise ForbiddenException("Vous n'avez pas accès à ce compteur")
        
        # Validate reading value against previous reading
        if meter.previous_reading is not None:
            if obj_in.reading_value < meter.previous_reading:
                raise BadRequestException(
                    f"La valeur de lecture ({obj_in.reading_value}) ne peut pas être "
                    f"inférieure à la lecture précédente ({meter.previous_reading})"
                )
        
        # Validate minimum 2 photos
        if not obj_in.photo_urls or len(obj_in.photo_urls) < 2:
            raise BadRequestException(
                "Au minimum 2 photos sont requises pour chaque lecture"
            )
        
        # Set controller_id if not provided
        if not obj_in.controller_id:
            kwargs["controller_id"] = current_user.id
        
        # Create reading
        reading = await super().create(db, obj_in, **kwargs)
        
        # Update meter's previous reading
        meter.previous_reading = reading.reading_value
        await db.commit()
        await db.refresh(reading)
        
        logger.info(
            f"Reading created: id={reading.id}, meter={meter.code}, "
            f"value={reading.reading_value}, photos={len(reading.photo_urls or [])}"
        )
        
        return reading
    
    async def get_by_meter(
        self,
        db: AsyncSession,
        meter_id: UUID,
        pagination: PaginationParams,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> PageResponse[Reading]:
        """Get readings by meter with optional date filtering."""
        stmt = select(Reading).where(Reading.meter_id == meter_id)
        
        # Apply date filters
        if start_date:
            stmt = stmt.where(Reading.reading_date >= start_date)
        if end_date:
            stmt = stmt.where(Reading.reading_date <= end_date)
        
        # Order by date descending
        stmt = stmt.order_by(desc(Reading.reading_date))
        
        # Count total
        count_query = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_query)
        
        # Apply pagination
        stmt = stmt.offset(pagination.skip).limit(pagination.limit)
        
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        return PageResponse.create(items, total or 0, pagination)
    
    async def get_by_controller(
        self,
        db: AsyncSession,
        controller_id: UUID,
        pagination: PaginationParams,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> PageResponse[Reading]:
        """Get readings by controller."""
        stmt = select(Reading).where(Reading.controller_id == controller_id)
        
        if start_date:
            stmt = stmt.where(Reading.reading_date >= start_date)
        if end_date:
            stmt = stmt.where(Reading.reading_date <= end_date)
        
        stmt = stmt.order_by(desc(Reading.reading_date))
        
        # Count total
        count_query = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_query)
        
        # Apply pagination
        stmt = stmt.offset(pagination.skip).limit(pagination.limit)
        
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        return PageResponse.create(items, total or 0, pagination)
    
    async def get_by_city(
        self,
        db: AsyncSession,
        city_id: UUID,
        pagination: PaginationParams,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> PageResponse[Reading]:
        """Get readings by city."""
        from app.models.meter import Meter
        
        stmt = (
            select(Reading)
            .join(Meter, Reading.meter_id == Meter.id)
            .where(Meter.city_id == city_id)
        )
        
        if start_date:
            stmt = stmt.where(Reading.reading_date >= start_date)
        if end_date:
            stmt = stmt.where(Reading.reading_date <= end_date)
        
        stmt = stmt.order_by(desc(Reading.reading_date))
        
        # Count total
        count_query = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_query)
        
        # Apply pagination
        stmt = stmt.offset(pagination.skip).limit(pagination.limit)
        
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        return PageResponse.create(items, total or 0, pagination)
    
    async def get_statistics(
        self,
        db: AsyncSession,
        meter_id: Optional[UUID] = None,
        city_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get reading statistics."""
        from app.models.meter import Meter
        
        stmt = select(Reading)
        
        # Apply filters
        if meter_id:
            stmt = stmt.where(Reading.meter_id == meter_id)
        
        if city_id:
            stmt = stmt.join(Meter).where(Meter.city_id == city_id)
        
        if start_date:
            stmt = stmt.where(Reading.reading_date >= start_date)
        if end_date:
            stmt = stmt.where(Reading.reading_date <= end_date)
        
        # Get statistics
        stats_query = select(
            func.count(Reading.id).label("total_readings"),
            func.avg(Reading.reading_value).label("average_value"),
            func.min(Reading.reading_value).label("min_value"),
            func.max(Reading.reading_value).label("max_value"),
            func.max(Reading.reading_date).label("last_reading_date")
        ).select_from(stmt.subquery())
        
        result = await db.execute(stats_query)
        stats = result.one()
        
        # Count total photos
        total_photos = 0
        if stats.total_readings > 0:
            photos_result = await db.execute(
                select(Reading.photo_urls).select_from(stmt.subquery())
            )
            for (photo_urls,) in photos_result:
                if photo_urls:
                    total_photos += len(photo_urls)
        
        return {
            "total_readings": stats.total_readings or 0,
            "average_value": float(stats.average_value) if stats.average_value else None,
            "min_value": float(stats.min_value) if stats.min_value else None,
            "max_value": float(stats.max_value) if stats.max_value else None,
            "last_reading_date": stats.last_reading_date,
            "total_photos": total_photos
        }
    
    async def check_access(
        self,
        db: AsyncSession,
        reading_id: UUID,
        user: User
    ) -> bool:
        """Check if user has access to reading."""
        reading = await self.get_or_404(db, reading_id)
        
        # Admins have access to all
        if user.is_admin():
            return True
        
        # Load meter to check city
        meter = await meter_service.get_or_404(db, reading.meter_id)
        
        # Check if user's city matches
        if user.city_id == meter.city_id:
            return True
        
        return False
    
    async def update(
        self,
        db: AsyncSession,
        id: UUID,
        obj_in: ReadingUpdate,
        user: User
    ) -> Reading:
        """Update a reading."""
        reading = await self.get_or_404(db, id)
        
        # Only admin or the controller who created it can update
        if not user.is_admin() and reading.controller_id != user.id:
            raise ForbiddenException("Vous ne pouvez modifier que vos propres lectures")
        
        # Check time restriction - can only edit within 24 hours
        if not user.is_admin():
            time_diff = datetime.utcnow() - reading.created_at.replace(tzinfo=None)
            if time_diff > timedelta(hours=24):
                raise ForbiddenException(
                    "Vous ne pouvez modifier les lectures que dans les 24 heures suivant leur création"
                )
        
        # Validate photos if being updated
        if obj_in.photo_urls is not None and len(obj_in.photo_urls) < 2:
            raise BadRequestException("Au minimum 2 photos sont requises")
        
        return await super().update(db, id, obj_in)
    
    async def delete(
        self,
        db: AsyncSession,
        id: UUID,
        user: User
    ) -> bool:
        """Delete a reading and its associated photos from S3."""
        reading = await self.get_or_404(db, id)
        
        # Only admin can delete
        if not user.is_admin():
            raise ForbiddenException("Seuls les administrateurs peuvent supprimer des lectures")
        
        # Delete photos from S3 if they exist
        if reading.photo_urls:
            deleted_count = await upload_service.delete_multiple_files(reading.photo_urls)
            logger.info(
                f"Deleted {deleted_count}/{len(reading.photo_urls)} photos "
                f"from S3 for reading {id}"
            )
        
        # Delete reading
        return await super().delete(db, id)


reading_service = ReadingService()