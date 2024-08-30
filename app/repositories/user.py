from typing import Type, List, Optional
from uuid import UUID

from passlib.context import CryptContext
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User as UserModel
from app.schema.user import UserCreate, UserUpdate

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user: UserCreate) -> UserModel:
        hashed_password = pwd_context.hash(user.password)
        db_user = UserModel(
            username=user.username,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            department=user.department,
            password=hashed_password
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def get_user_by_username(self, username: str) -> Optional[UserModel]:
        query = select(UserModel).filter(UserModel.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_users_by_department(self, department: str) -> List[UserModel]:
        query = select(UserModel).filter(UserModel.department == department)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_user(self, user_id: UUID) -> Optional[UserModel]:
        query = select(UserModel).filter(UserModel.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def findall(self) -> List[UserModel]:
        query = select(UserModel)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_user(self, user_id: UUID, user: UserUpdate) -> Optional[UserModel]:
        db_user = await self.get_user(user_id)
        if db_user:
            db_user.username = user.username
            db_user.first_name = user.first_name
            db_user.middle_name = user.middle_name
            db_user.last_name = user.last_name
            db_user.department = user.department
            if user.password:
                db_user.password = pwd_context.hash(user.password)
            await self.db.commit()
            await self.db.refresh(db_user)
            return db_user
        return None

    async def delete_user(self, user_id: UUID) -> bool:
        db_user = await self.get_user(user_id)
        if db_user:
            await self.db.delete(db_user)
            await self.db.commit()
            return True
        return False

    async def delete_all_users(self) -> bool:
        await self.db.execute(delete(UserModel))
        await self.db.commit()
        return True

    def verify_pswd(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)