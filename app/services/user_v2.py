"""User service."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.user import User
from app.schema.user import UserCreate, UserUpdate
from app.services.base import BaseService


class UserService(BaseService[User, UserCreate, UserUpdate]):
    """User service with business logic."""
    
    def __init__(self):
        super().__init__(User)
    
    async def get_by_username(
        self,
        db: AsyncSession,
        username: str
    ) -> Optional[User]:
        """Get user by username."""
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_with_stats(
        self,
        db: AsyncSession,
        id: UUID
    ) -> dict:
        """Get user with statistics."""
        user = await self.get_or_404(db, id)
        
        # Count readings
        from app.models.readings import Reading
        
        readings_count = await db.scalar(
            select(func.count()).where(Reading.controller_id == id)
        ) or 0
        
        # Get last reading date
        last_reading = await db.execute(
            select(Reading.reading_date)
            .where(Reading.controller_id == id)
            .order_by(Reading.reading_date.desc())
            .limit(1)
        )
        last_reading_date = last_reading.scalar_one_or_none()
        
        return {
            **user.__dict__,
            "readings_count": readings_count,
            "last_reading_date": last_reading_date.isoformat() if last_reading_date else None
        }
    
    async def set_active_status(
        self,
        db: AsyncSession,
        id: UUID,
        is_active: bool
    ) -> User:
        """Set user active status."""
        user = await self.get_or_404(db, id)
        user.is_active = is_active
        
        await db.commit()
        await db.refresh(user)
        
        return user


user_service = UserService()