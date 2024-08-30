from uuid import UUID
from typing import List, Optional

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user import UserRepository
from app.schema.user import UserCreate, UserUpdate
from app.models.user import User as UserModel

class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def create(self, user: UserCreate) -> UserModel:
        user = await self.repository.create_user(user)
        return user

    async def get_user_by_username(self, username: str) -> Optional[UserModel]:
        user = await self.repository.get_user_by_username(username)
        return user

    async def get_user(self, user_id: UUID) -> Optional[UserModel]:
        user = await self.repository.get_user(user_id)
        return user

    async def get_users(self) -> List[UserModel]:
        users = await self.repository.findall()
        return users

    async def find_users_by_department(self, department: str) -> List[UserModel]:
        users = await self.repository.get_users_by_department(department)
        return users

    async def update_user(self, user_id: UUID, user: UserUpdate) -> Optional[UserModel]:
        user_updated = await self.repository.update_user(user_id, user)
        return user_updated

    async def delete_user(self, user_id: UUID) -> bool:
        return await self.repository.delete_user(user_id)

    async def delete_users(self) -> bool:
        return await self.repository.delete_all_users()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.repository.verify_pswd(plain_password, hashed_password)