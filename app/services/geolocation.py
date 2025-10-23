"""Geolocation service for automatic location detection."""

import logging
from typing import Optional, Tuple
import httpx

from app.config import settings
from app.core.exceptions import BadRequestException

logger = logging.getLogger(__name__)


class GeolocationService:
    """Service for geolocation operations."""
    
    # Allowed radius for location validation (in meters)
    MAX_DISTANCE_FROM_METER = 500  # 500 meters
    
    async def get_location_from_ip(self, ip_address: str) -> Optional[dict]:
        """
        Get approximate location from IP address.
        
        Uses ipapi.co (free tier: 1000 requests/day)
        
        Args:
            ip_address: Client IP address
            
        Returns:
            dict with latitude, longitude, city, country
        """
        # Skip private IPs
        if self._is_private_ip(ip_address):
            logger.warning(f"Cannot geolocate private IP: {ip_address}")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"https://ipapi.co/{ip_address}/json/"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("latitude") and data.get("longitude"):
                        return {
                            "latitude": float(data["latitude"]),
                            "longitude": float(data["longitude"]),
                            "city": data.get("city"),
                            "country": data.get("country_name"),
                            "accuracy": "low",  # IP-based is low accuracy
                            "source": "ip"
                        }
                
                logger.warning(f"Failed to geolocate IP {ip_address}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting location from IP: {e}")
            return None
    
    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is private/local."""
        if ip in ["127.0.0.1", "localhost", "::1"]:
            return True
        
        # Check private ranges
        parts = ip.split(".")
        if len(parts) == 4:
            first = int(parts[0])
            second = int(parts[1])
            
            # 10.0.0.0/8
            if first == 10:
                return True
            # 172.16.0.0/12
            if first == 172 and 16 <= second <= 31:
                return True
            # 192.168.0.0/16
            if first == 192 and second == 168:
                return True
        
        return False
    
    def validate_coordinates(
        self,
        latitude: float,
        longitude: float
    ) -> bool:
        """
        Validate GPS coordinates.
        
        Args:
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)
            
        Returns:
            True if valid
        """
        if not (-90 <= latitude <= 90):
            return False
        if not (-180 <= longitude <= 180):
            return False
        return True
    
    def calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two GPS points using Haversine formula.
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in meters
        """
        from math import radians, sin, cos, sqrt, atan2
        
        # Earth radius in meters
        R = 6371000
        
        # Convert to radians
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        # Haversine formula
        a = (sin(delta_lat / 2) ** 2 +
             cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2)
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c
        
        return distance
    
    async def validate_reading_location(
        self,
        reading_lat: float,
        reading_lon: float,
        meter_lat: Optional[float],
        meter_lon: Optional[float],
        strict: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that reading location is near meter location.
        
        Args:
            reading_lat: Reading latitude
            reading_lon: Reading longitude
            meter_lat: Meter latitude (if known)
            meter_lon: Meter longitude (if known)
            strict: If True, reject readings too far from meter
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate coordinates format
        if not self.validate_coordinates(reading_lat, reading_lon):
            return False, "Coordonnées GPS invalides"
        
        # If meter has no location, accept any location
        if meter_lat is None or meter_lon is None:
            logger.info("Meter has no GPS coordinates, accepting reading location")
            return True, None
        
        # Calculate distance
        distance = self.calculate_distance(
            meter_lat, meter_lon,
            reading_lat, reading_lon
        )
        
        logger.info(
            f"Reading location is {distance:.2f}m from meter location"
        )
        
        # Validate distance
        if distance > self.MAX_DISTANCE_FROM_METER:
            error_msg = (
                f"La lecture est à {distance:.0f}m du compteur. "
                f"Distance maximale autorisée: {self.MAX_DISTANCE_FROM_METER}m"
            )
            
            if strict:
                return False, error_msg
            else:
                logger.warning(error_msg + " (mode non-strict, accepté)")
                return True, None
        
        return True, None
    
    def get_location_accuracy(
        self,
        accuracy: Optional[float]
    ) -> str:
        """
        Get location accuracy level.
        
        Args:
            accuracy: Accuracy in meters from device
            
        Returns:
            Accuracy level: high, medium, low
        """
        if accuracy is None:
            return "unknown"
        
        if accuracy <= 10:
            return "high"
        elif accuracy <= 50:
            return "medium"
        else:
            return "low"


geolocation_service = GeolocationService()