"""Authentication service."""

from datetime import timedelta
from typing import Optional
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    UnauthorizedException,
    BadRequestException,
    ConflictException,
    NotFoundException
)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token
)
from app.models.user import User, UserRole
from app.models.city import City
from app.schema.user import UserCreate


logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service."""
    
    async def authenticate(
        self,
        db: AsyncSession,
        username: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate user with username and password.
        
        Args:
            db: Database session
            username: Username
            password: Plain password
            
        Returns:
            User if authentication successful, None otherwise
            
        Raises:
            BadRequestException: If user is inactive
        """
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"Authentication failed: user '{username}' not found")
            return None
        
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: invalid password for user '{username}'")
            return None
        
        if not user.is_active:
            logger.warning(f"Authentication failed: user '{username}' is inactive")
            raise BadRequestException("Compte utilisateur désactivé")
        
        logger.info(f"User '{username}' authenticated successfully")
        return user
    
    async def create_user_tokens(
        self,
        user: User
    ) -> dict[str, str]:
        """
        Create access and refresh tokens for user.
        
        Args:
            user: User object
            
        Returns:
            dict with access_token, refresh_token, and token_type
        """
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        refresh_token_expires = timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            subject=str(user.id),
            expires_delta=refresh_token_expires
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    async def register(
        self,
        db: AsyncSession,
        user_in: UserCreate
    ) -> User:
        """
        Register a new user.
        
        Validation:
        - Admins don't need city_id (managed globally)
        - Controllers and Supervisors must have city_id
        - Username must be unique
        - City must exist if provided
        
        Args:
            db: Database session
            user_in: User creation data
            
        Returns:
            Created user
            
        Raises:
            ConflictException: If username already exists
            BadRequestException: If validation fails
        """
        # Check if username exists
        result = await db.execute(
            select(User).where(User.username == user_in.username)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.warning(f"Registration failed: username '{user_in.username}' already exists")
            raise ConflictException(
                f"Le nom d'utilisateur '{user_in.username}' est déjà utilisé"
            )
        
        # Validate city for non-admin roles
        if user_in.role != UserRole.ADMIN and user_in.city_id:
        
            city_result = await db.execute(
                select(City).where(City.id == user_in.city_id)
            )
            city = city_result.scalar_one_or_none()
            
            if not city:
                raise BadRequestException(
                    f"La ville avec l'ID {user_in.city_id} n'existe pas"
                )
        
        # Log registration attempt
        logger.info(
            f"Creating new user: username='{user_in.username}', "
            f"role={user_in.role.value}, "
            f"city_id={user_in.city_id if user_in.city_id else 'N/A (admin)'}"
        )
        
        # Create user
        user = User(
            username=user_in.username,
            full_name=user_in.full_name,
            hashed_password=get_password_hash(user_in.password),
            role=user_in.role.value,
            city_id=user_in.city_id,  # Will be None for admins
            is_active=user_in.is_active
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"User '{user.username}' created successfully with ID: {user.id}")
        
        return user
    
    async def change_password(
        self,
        db: AsyncSession,
        user: User,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password.
        
        Args:
            db: Database session
            user: Current user
            old_password: Current password
            new_password: New password
            
        Returns:
            True if successful
            
        Raises:
            UnauthorizedException: If old password is incorrect
            BadRequestException: If new password is same as old
        """
        # Verify old password
        if not verify_password(old_password, user.hashed_password):
            logger.warning(f"Password change failed for user '{user.username}': incorrect old password")
            raise UnauthorizedException("Mot de passe actuel incorrect")
        
        # Check if new password is different
        if verify_password(new_password, user.hashed_password):
            raise BadRequestException(
                "Le nouveau mot de passe doit être différent de l'ancien"
            )
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        await db.commit()
        
        logger.info(f"Password changed successfully for user '{user.username}'")
        
        return True
    
    async def reset_password(
        self,
        db: AsyncSession,
        username: str,
        new_password: str,
        admin_user: User
    ) -> User:
        """
        Reset user password (admin only).
        
        Args:
            db: Database session
            username: Username of user to reset
            new_password: New password
            admin_user: Admin performing the reset
            
        Returns:
            Updated user
            
        Raises:
            NotFoundException: If user not found
            UnauthorizedException: If not admin
        """
        # Verify admin
        if not admin_user.is_admin():
            raise UnauthorizedException("Seuls les administrateurs peuvent réinitialiser les mots de passe")
        
        # Find user
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundException(f"Utilisateur '{username}' non trouvé")
        
        # Reset password
        user.hashed_password = get_password_hash(new_password)
        await db.commit()
        await db.refresh(user)
        
        logger.info(
            f"Password reset by admin '{admin_user.username}' "
            f"for user '{user.username}'"
        )
        
        return user
    
    async def create_superuser(
        self,
        db: AsyncSession,
        username: str,
        password: str,
        full_name: str
    ) -> User:
        """
        Create initial superuser/admin.
        Used for first-time setup or via CLI.
        
        Args:
            db: Database session
            username: Admin username
            password: Admin password
            full_name: Admin full name
            
        Returns:
            Created admin user
            
        Raises:
            ConflictException: If username already exists
        """
        # Check if user exists
        result = await db.execute(
            select(User).where(User.username == username)
        )
        if result.scalar_one_or_none():
            raise ConflictException(f"L'utilisateur '{username}' existe déjà")
        
        # Create admin
        admin = User(
            username=username,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN.value,
            city_id=None,  # Admins don't have a city
            is_active=True
        )
        
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        
        logger.info(f"Superuser '{username}' created successfully")
        
        return admin
    
    async def ensure_superuser_exists(
        self,
        db: AsyncSession
    ) -> Optional[User]:
        """
        Ensure at least one superuser exists.
        Creates default superuser from settings if none exist.
        
        Args:
            db: Database session
            
        Returns:
            Existing or created superuser, None if settings incomplete
        """
        # Check if any admin exists
        result = await db.execute(
            select(User).where(User.role == UserRole.ADMIN.value).limit(1)
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            logger.info(f"Admin user already exists: '{existing_admin.username}'")
            return existing_admin
        
        # Check if settings are configured
        if not all([
            settings.FIRST_SUPERUSER_USERNAME,
            settings.FIRST_SUPERUSER_PASSWORD,
            settings.FIRST_SUPERUSER_FULL_NAME
        ]):
            logger.warning(
                "No admin exists and FIRST_SUPERUSER settings are not configured. "
                "Please create an admin user manually."
            )
            return None
        
        # Create default superuser
        logger.info(f"Creating default superuser: '{settings.FIRST_SUPERUSER_USERNAME}'")
        
        try:
            admin = await self.create_superuser(
                db,
                username=settings.FIRST_SUPERUSER_USERNAME,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                full_name=settings.FIRST_SUPERUSER_FULL_NAME
            )
            
            logger.info(
                f"✅ Default superuser created: '{admin.username}'. "
                "Please change the password immediately!"
            )
            
            return admin
            
        except ConflictException:
            # Race condition - another process created the admin
            result = await db.execute(
                select(User).where(
                    User.username == settings.FIRST_SUPERUSER_USERNAME
                )
            )
            return result.scalar_one_or_none()


auth_service = AuthService()