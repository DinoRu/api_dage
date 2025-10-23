"""City model."""

from typing import TYPE_CHECKING

from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from models.meter import Meter
    from models.user import User


class City(BaseModel):
    """City model representing geographical locations."""
    
    __tablename__ = "cities"  # Explicite pour éviter toute ambiguïté
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Nom de la ville"
    )
    
    # Relations
    meters: Mapped[list["Meter"]] = relationship(
        "Meter",
        back_populates="city",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    controllers: Mapped[list["User"]] = relationship(
        "User",
        back_populates="city",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<City(id={self.id}, name={self.name})>"
    
    def __str__(self) -> str:
        return self.name