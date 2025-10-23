"""Reading model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, String, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from models.meter import Meter
    from models.user import User


class Reading(BaseModel):
    """Reading model representing meter readings."""
    
    __tablename__ = "readings"
    
    # Clés étrangères
    meter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Référence au compteur"
    )
    
    controller_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Référence au contrôleur"
    )
    
    # Champs obligatoires
    reading_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Valeur de la lecture"
    )
    
    reading_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Date et heure de la lecture"
    )
    
    # Champs optionnels
    comment: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        default=None,
        comment="Commentaire additionnel"
    )
    
    # Utilisation de JSON pour stocker la liste d'URLs
    photo_urls: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="URLs des photos (minimum 2, maximum 5)"
    )
    
    latitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Latitude GPS"
    )
    
    longitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Longitude GPS"
    )
    
    # Relations
    meter: Mapped["Meter"] = relationship(
        "Meter",
        back_populates="readings"
    )
    
    controller: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="readings"
    )
    
    # Index composites
    __table_args__ = (
        Index("idx_reading_meter_date", "meter_id", "reading_date"),
        Index("idx_reading_controller_date", "controller_id", "reading_date"),
        Index("idx_reading_date", "reading_date"),
    )
    
    @property
    def has_geolocation(self) -> bool:
        """Check if reading has geolocation data."""
        return self.latitude is not None and self.longitude is not None

    @property
    def photos_count(self) -> int:
        """Get number of photos."""
        return len(self.photo_urls) if self.photo_urls else 0
    
    def __repr__(self) -> str:
        return (
            f"<Reading(id={self.id}, meter_id={self.meter_id}, "
            f"value={self.reading_value}, date={self.reading_date})>"
        )
    
    def __str__(self) -> str:
        return (
            f"Reading {self.reading_value} for Meter {self.meter_id} "
            f"on {self.reading_date.strftime('%Y-%m-%d %H:%M')}"
        )