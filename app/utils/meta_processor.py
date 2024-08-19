from abc import abstractmethod
from typing import Protocol

from app.value_objects.coordinates import Coordinate


class PhotoMetadataProcessor(Protocol):

    @abstractmethod
    def get_coordinates(self, photo: bytes) -> Coordinate:
        raise NotImplementedError()
