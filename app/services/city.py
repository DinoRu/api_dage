"""City service."""


from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException
from app.core.pagination import PaginationParams, PageResponse
from app.models.city import City
from app.schema.city import CityCreate, CityUpdate
from app.services.base import BaseService


class CityService(BaseService[City, CityCreate, CityUpdate]):
    """City service with business logic."""
    
    def __init__(self):
        super().__init__(City)
    
    async def get_by_name(
        self,
        db: AsyncSession,
        name: str
    ) -> Optional[City]:
        """Get city by name."""
        result = await db.execute(
            select(City).where(City.name == name)
        )
        return result.scalar_one_or_none()
    
    async def create(
        self,
        db: AsyncSession,
        obj_in: CityCreate,
        **kwargs
    ) -> City:
        """Create a new city."""
        # Check if city with same name exists
        existing = await self.get_by_name(db, obj_in.name)
        if existing:
            raise ConflictException(f"City with name '{obj_in.name}' already exists")
        
        return await super().create(db, obj_in, **kwargs)
    
    async def get_with_stats(
        self,
        db: AsyncSession,
        id: UUID
    ) -> dict:
        """Get city with statistics."""
        city = await self.get_or_404(db, id)
        
        # Count meters
        meters_count = await db.scalar(
            select(func.count()).where(City.id == id).select_from(City).join(City.meters)
        ) or 0
        
        # Count controllers
        controllers_count = await db.scalar(
            select(func.count()).where(City.id == id).select_from(City).join(City.controllers)
        ) or 0
        
        return {
            **city.__dict__,
            "meters_count": meters_count,
            "controllers_count": controllers_count
        }
    
    async def get_with_relations(
        self,
        db: AsyncSession,
        id: UUID
    ) -> City:
        """Get city with all relations loaded."""
        result = await db.execute(
            select(City)
            .where(City.id == id)
            .options(
                selectinload(City.meters),
                selectinload(City.controllers)
            )
        )
        city = result.scalar_one_or_none()
        
        if not city:
            raise NotFoundException(f"City with id {id} not found")
        
        return city
    
    async def search(
        self,
        db: AsyncSession,
        query: str,
        pagination: PaginationParams
    ) -> PageResponse[City]:
        """Search cities by name."""
        stmt = select(City).where(
            City.name.ilike(f"%{query}%")
        ).order_by(City.name)
        
        # Count total
        count_query = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_query)
        
        # Apply pagination
        stmt = stmt.offset(pagination.skip).limit(pagination.limit)
        
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        return PageResponse.create(items, total or 0, pagination)


city_service = CityService()