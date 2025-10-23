"""Meter model."""

import uuid
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.city import City
    from app.models.readings import Reading


class MeterStatus(str, Enum):
    """Meter status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"


class Meter(BaseModel):
    """
        Meter model representing water/electricity/gas meters.
    """
    
    __tablename__ = "meters"
    
    # Champs obligatoires
    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Code unique du compteur"
    )
    
    owner_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nom du propriétaire"
    )
    
    address: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Adresse du compteur"
    )
    
    meter_number: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Numéro de série du compteur"
    )
    
    meter_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Type de compteur"
    )
    
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=MeterStatus.ACTIVE.value,
        index=True,
        comment="Statut actuel du compteur"
    )
    
    # Champs optionnels
    previous_reading: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        default=None,
        comment="Dernière lecture enregistrée"
    )
    
    # Clé étrangère
    city_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Référence à la ville"
    )
    
    # Relations
    city: Mapped["City"] = relationship(
        "City",
        back_populates="meters"
    )
    
    readings: Mapped[list["Reading"]] = relationship(
        "Reading",
        back_populates="meter",
        cascade="all, delete-orphan",
        order_by="Reading.reading_date.desc()",
        lazy="selectin"
    )
    
    # Index composites
    __table_args__ = (
        Index("idx_meter_city_status", "city_id", "status"),
        Index("idx_meter_code_city", "code", "city_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Meter(code={self.code}, owner={self.owner_name}, status={self.status})>"
    
    def __str__(self) -> str:
        return f"Meter {self.code} - {self.owner_name}"