"""User schemas."""

from uuid import UUID
from typing import Optional

from pydantic import Field, field_validator, EmailStr, model_validator

from app.core.exceptions import BadRequestException
from app.models.user import UserRole
from app.schema.base import BaseSchema, TimestampSchema


class UserBase(BaseSchema):
    """Base user schema with common fields."""
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=255,
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="Nom d'utilisateur (lettres, chiffres, _ et - uniquement)",
        examples=["john_doe", "marie-dupont"]
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nom complet",
        examples=["Jean Dupont", "Marie Martin"]
    )
    role: UserRole = Field(
        default=UserRole.CONTROLLER,
        description="Rôle de l'utilisateur"
    )
    city_id: Optional[UUID] = Field(
        None,
        description="Identifiant de la ville assignée (non requis pour les admins)"
    )
    is_active: bool = Field(
        default=True,
        description="Statut actif/inactif"
    )


class UserCreate(UserBase):
    """Schema for creating a user."""
    
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Mot de passe (min 8 caractères)",
        examples=["SecureP@ssw0rd"]
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Adresse email (optionnel)"
    )
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        if not any(c.isupper() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not any(c.islower() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins une minuscule")
        if not any(c.isdigit() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate and lowercase username."""
        return v.lower().strip()
    
    @model_validator(mode='after')
    def validate_city_requirement(self):
        """Validate city_id based on role."""
        # Admins don't need a city
        if self.role == UserRole.ADMIN:
            # Si une ville est fournie pour un admin, on l'ignore silencieusement
            self.city_id = None
        else:
            # Controllers and Supervisors must have a city
            if not self.city_id:
                raise ValueError(
                    f"Le champ 'city_id' est requis pour le rôle {self.role.value}"
                )
        return self


class UserUpdate(BaseSchema):
    """Schema for updating a user."""
    
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    city_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    email: Optional[EmailStr] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate password strength if provided."""
        if v is not None:
            if len(v) < 8:
                raise BadRequestException("Le mot de passe doit contenir au moins 8 caractères")
            if not any(c.isupper() for c in v):
                raise BadRequestException("Le mot de passe doit contenir au moins une majuscule")
            if not any(c.islower() for c in v):
                raise BadRequestException("Le mot de passe doit contenir au moins une minuscule")
            if not any(c.isdigit() for c in v):
                raise BadRequestException("Le mot de passe doit contenir au moins un chiffre")
        return v
    
    @model_validator(mode='after')
    def validate_role_city_consistency(self):
        """Validate that role and city_id are consistent."""
        # If role is being changed to admin, clear city_id
        if self.role == UserRole.ADMIN:
            self.city_id = None
        
        return self


class UserRead(UserBase, TimestampSchema):
    """Schema for reading a user."""
    
    pass


class UserInDB(UserBase):
    user_id: UUID


class UserReadSimple(BaseSchema):
    """Simplified user schema for nested relations."""
    
    id: UUID
    username: str
    full_name: str
    role: UserRole


class UserReadWithCity(UserRead):
    """Schema for reading a user with city."""
    
    
    city: Optional["CityRead"] = None


class UserReadWithStats(UserRead):
    """Schema for reading a user with statistics."""
    
    readings_count: int = Field(default=0, description="Nombre de lectures effectuées")
    last_reading_date: Optional[str] = None


class UserLogin(BaseSchema):
    """Schema for user login."""
    
    username: str = Field(..., description="Nom d'utilisateur")
    password: str = Field(..., description="Mot de passe")


class UserToken(BaseSchema):
    """Schema for user token response."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Type de token")
    user: UserRead = Field(..., description="Informations utilisateur")


class PasswordChange(BaseSchema):
    """Schema for changing password."""
    
    old_password: str = Field(..., description="Ancien mot de passe")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Nouveau mot de passe"
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise BadRequestException("Le mot de passe doit contenir au moins 8 caractères")
        if not any(c.isupper() for c in v):
            raise BadRequestException("Le mot de passe doit contenir au moins une majuscule")
        if not any(c.islower() for c in v):
            raise BadRequestException("Le mot de passe doit contenir au moins une minuscule")
        if not any(c.isdigit() for c in v):
            raise BadRequestException("Le mot de passe doit contenir au moins un chiffre")
        return v
    
from app.schema.city import CityRead