from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.user import UserService


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)
