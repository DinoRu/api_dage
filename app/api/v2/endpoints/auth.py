"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DatabaseSession, CurrentUser, AdminUser
from app.core.exceptions import UnauthorizedException
from app.schema.user import (
    UserCreate,
    UserRead,
    UserToken,
    PasswordChange
)
from app.services.auth import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: DatabaseSession
):
    """
    Register a new user.
    
    **Role-based requirements**:
    - **Admin**: No city required (manages all cities)
    - **Supervisor**: Must have city_id
    - **Controller**: Must have city_id
    
    **Fields**:
    - **username**: Unique username (3-255 characters, alphanumeric, _ and -)
    - **password**: Strong password (min 8 chars, 1 uppercase, 1 lowercase, 1 digit)
    - **full_name**: User's full name
    - **role**: User role (admin, controller, supervisor)
    - **city_id**: City assignment (required for non-admin roles)
    - **is_active**: User status (default: true)
    
    **Examples**:
    
    Admin user (no city needed):
    ```json
        {
        "username": "admin_user",
        "password": "SecurePass123",
        "full_name": "Admin User",
        "role": "admin"
        }
    ```
        
        Controller user (city required):
    ```json
        {
        "username": "controller_paris",
        "password": "SecurePass123",
        "full_name": "Marie Dupont",
        "role": "controller",
        "city_id": "uuid-here"
        }
    ```
    """
    return await auth_service.register(db, user_in)


@router.post("/login", response_model=UserToken)
async def login(
    db: DatabaseSession,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    """
    OAuth2 compatible token login.
    
    Get an access token for future requests.
    
    **Returns**:
    - Access token (30 min validity)
    - Refresh token (7 days validity)
    - User information
    """
    user = await auth_service.authenticate(
        db,
        username=form_data.username,
        password=form_data.password
    )
    
    if not user:
        raise UnauthorizedException("Nom d'utilisateur ou mot de passe incorrect")
    
    tokens = await auth_service.create_user_tokens(user)
    
    return UserToken(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user=user
    )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Change current user's password.
    
    - **old_password**: Current password
    - **new_password**: New password (min 8 chars, 1 uppercase, 1 lowercase, 1 digit)
    """
    await auth_service.change_password(
        db,
        current_user,
        password_data.old_password,
        password_data.new_password
    )
    
    return {"message": "Mot de passe modifié avec succès"}


@router.post("/reset-password/{username}")
async def reset_user_password(
    username: str,
    new_password: str,
    db: DatabaseSession,
    current_user: AdminUser
):
    """
    Reset a user's password.
    
    **Admin only**
    
    - **username**: Username of the user
    - **new_password**: New password to set
    """
    user = await auth_service.reset_password(
        db,
        username,
        new_password,
        current_user
    )
    
    return {
        "message": f"Mot de passe réinitialisé pour l'utilisateur '{user.username}'",
        "user_id": user.id
    }


@router.get("/me", response_model=UserRead)
async def get_current_user_info(current_user: CurrentUser):
    """Get current user information."""
    return current_user


@router.post("/refresh", response_model=UserToken)
async def refresh_token(
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Refresh access token.
    
    Get a new access token using the current valid token.
    """
    tokens = await auth_service.create_user_tokens(current_user)
    
    return UserToken(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user=current_user
    )