from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from app.auth.jwt_handler import create_access_token
from app.dependencies import get_user_service
from app.schema.user import UserOutDB, UserCreate, UserUpdate, Token, UserLogin
from app.services.user import UserService

user_router = APIRouter()


@user_router.post("/create_user", response_model=UserOutDB)
async def create_user(user: UserCreate, service: UserService = Depends(get_user_service)):
    db_user = service.create(user)
    return db_user


@user_router.get("/", response_model=List[UserOutDB])
async def get_users(service: UserService = Depends(get_user_service)):
    users = service.get_users()
    return users


@user_router.get("/user/{department}", response_model=List[UserOutDB])
async def get_users_by_department(department: str, service: UserService = Depends(get_user_service)):
    users = service.find_users_by_department(department)
    return users


@user_router.get("/user/{user_id}", response_model=UserOutDB)
async def get_user(user_id: UUID, service: UserService = Depends(get_user_service)):
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@user_router.get("/{username}", response_model=UserOutDB)
async def get_user_by_username(username: str, service: UserService = Depends(get_user_service)):
    user = service.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@user_router.put("/update_user/{user_id}", response_model=UserOutDB)
async def update_user(user_id: UUID, user: UserUpdate, service: UserService = Depends(get_user_service)):
    updated_user = service.update_user(user_id, user)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user


@user_router.delete("/remove/{user_id}", response_model=dict)
async def remove_user(user_id: UUID, service: UserService = Depends(get_user_service)):
    user = service.delete_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"detail": "User deleted successfully"}


@user_router.delete("/delete/all", response_model=dict)
async def delete_all(service: UserService = Depends(get_user_service)):
    service.delete_users()
    return {"detail": "All users deleted successfully"}


@user_router.post("/signin", response_model=Token, status_code=status.HTTP_201_CREATED)
async def sign_user_in(user: OAuth2PasswordRequestForm = Depends(),
                       service: UserService = Depends(get_user_service)) -> dict:
    user_exit = service.get_user_by_username(user.username)
    if not user_exit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not exits"
        )
    if service.verify_password(user.password, user_exit.password):
        access_token = create_access_token(
            user={
                "user_id": str(user_exit.user_id),
                "username": str(user_exit.username),
                "department": str(user_exit.department)
            }
        )
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
