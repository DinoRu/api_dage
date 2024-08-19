from typing import Type, List
from uuid import UUID

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.user import User as UserModel, User
from app.schema.user import UserCreate, UserUpdate

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user: UserCreate) -> UserModel:
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
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_user_by_username(self, username: str) -> Type[UserModel]:
        user = self.db.query(UserModel).filter(UserModel.username == username).first()
        return user

    def get_users_by_department(self, department: str) -> Type[List[UserModel]]:
        users = self.db.query(UserModel).filter(UserModel.department == department)
        return users

    def get_user(self, user_id: UUID) -> Type[UserModel]:
        user = self.db.query(UserModel).filter(UserModel.user_id == user_id).first()
        return user

    def findall(self):
        users = self.db.query(UserModel).all()
        return users

    def update_user(self, user_id: UUID, user: UserUpdate) -> Type[UserModel] | None:
        db_user = self.get_user(user_id)
        if db_user:
            db_user.username = user.username
            db_user.first_name = user.first_name
            db_user.middle_name = user.middle_name
            db_user.last_name = user.last_name
            db_user.department = user.department
            if user.password:
                db_user.password = pwd_context.hash(user.password)
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        return None

    def delete_user(self, user_id: UUID) -> bool:
        user = self.get_user(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False

    def delete_all_user(self) -> bool:
        self.db.query(UserModel).delete()
        self.db.commit()
        return True

    def verify_pswd(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
