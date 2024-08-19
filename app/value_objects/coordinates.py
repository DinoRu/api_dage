from dataclasses import dataclass


@dataclass(frozen=True)
class Coordinate:
    latitude: float | None
    longitude: float | None
    
