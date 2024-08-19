from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    department: str


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDB(UserBase):
    user_id: UUID


class UserOutDB(UserBase):
    user_id: UUID


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[UUID] = None
    username: Optional[str] = None
    department: Optional[str] = None
