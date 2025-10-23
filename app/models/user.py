"""User model."""

import uuid
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.city import City
    from app.models.readings import Reading


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    CONTROLLER = "controller"
    SUPERVISOR = "supervisor"


class User(BaseModel):
    """User model representing system users."""
    
    __tablename__ = "users"
    
    # Champs obligatoires
    username: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Nom d'utilisateur unique"
    )
    
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nom complet de l'utilisateur"
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Mot de passe hashé"
    )
    
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=UserRole.CONTROLLER.value,
        index=True,
        comment="Rôle de l'utilisateur"
    )
    
    # Champs optionnels
    city_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Référence à la ville"
    )
    
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        index=True,
        comment="Statut actif/inactif"
    )
    
    # Relations
    city: Mapped[Optional["City"]] = relationship(
        "City",
        back_populates="controllers"
    )
    
    readings: Mapped[list["Reading"]] = relationship(
        "Reading",
        back_populates="controller",
        lazy="selectin"
    )
    
    # Index composites
    __table_args__ = (
        Index("idx_user_role_city", "role", "city_id"),
        Index("idx_user_active_role", "is_active", "role"),
    )
    
    # Méthodes utilitaires
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN.value
    
    def is_controller(self) -> bool:
        """Check if user is controller."""
        return self.role == UserRole.CONTROLLER.value
    
    def is_supervisor(self) -> bool:
        """Check if user is supervisor."""
        return self.role == UserRole.SUPERVISOR.value
    
    def can_manage_city(self, city_id: uuid.UUID) -> bool:
        """Check if user can manage a specific city."""
        if self.is_admin():
            return True
        return self.city_id == city_id
    
    def __repr__(self) -> str:
        return f"<User(username={self.username}, role={self.role})>"
    
    def __str__(self) -> str:
        return f"{self.full_name} ({self.username})"