"""Custom exceptions for the application."""

from typing import Any, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception with safe string conversion for detail."""

    def __init__(
        self,
        status_code: int,
        detail: Any,
        headers: Optional[dict[str, Any]] = None
    ):
        # Convertir le détail en string si ce n'est pas déjà une chaîne
        if not isinstance(detail, str):
            try:
                detail = str(detail)
            except Exception:
                detail = "Unknown error"
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundException(AppException):
    """Resource not found exception."""

    def __init__(self, detail: Any = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BadRequestException(AppException):
    """Bad request exception."""

    def __init__(self, detail: Any = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnauthorizedException(AppException):
    """Unauthorized exception."""

    def __init__(self, detail: Any = "Unauthorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenException(AppException):
    """Forbidden exception."""

    def __init__(self, detail: Any = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ConflictException(AppException):
    """Conflict exception."""

    def __init__(self, detail: Any = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ValidationException(AppException):
    """Validation exception."""

    def __init__(self, detail: Any = "Validation error"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)
