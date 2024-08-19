from uuid import UUID

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.repositories.user import UserRepository
from app.schema.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def create(self, user: UserCreate):
        user = self.repository.create_user(user)
        return user

    def get_user_by_username(self, username: str):
        user = self.repository.get_user_by_username(username)
        return user

    def get_user(self, user_id: UUID):
        user = self.repository.get_user(user_id)
        return user

    def get_users(self):
        users = self.repository.findall()
        return users

    def find_users_by_department(self, department: str):
        users = self.repository.get_users_by_department(department)
        return users

    def update_user(self, user_id: UUID, user: UserUpdate):
        user_updated = self.repository.update_user(user_id, user)
        return user_updated

    def delete_user(self, user_id: UUID):
        return self.repository.delete_user(user_id)

    def delete_users(self):
        self.repository.delete_all_user()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.repository.verify_pswd(plain_password, hashed_password)


