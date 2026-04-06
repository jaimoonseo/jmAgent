"""API exceptions and error handling."""

from fastapi import HTTPException
from typing import Optional, Dict, Any


class APIException(HTTPException):
    """Base API exception class."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class ValidationError(APIException):
    """Raised when request validation fails."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=400,
            detail=detail,
            error_code="VALIDATION_ERROR",
        )


class AuthenticationError(APIException):
    """Raised when authentication fails."""

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=401,
            detail=detail,
            error_code="AUTH_ERROR",
        )


class AuthorizationError(APIException):
    """Raised when user lacks required permissions."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=403,
            detail=detail,
            error_code="AUTHZ_ERROR",
        )


class NotFoundError(APIException):
    """Raised when requested resource is not found."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=404,
            detail=detail,
            error_code="NOT_FOUND",
        )


class ConflictError(APIException):
    """Raised when request conflicts with existing resource."""

    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(
            status_code=409,
            detail=detail,
            error_code="CONFLICT",
        )


class RateLimitError(APIException):
    """Raised when rate limit is exceeded."""

    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=429,
            detail=detail,
            error_code="RATE_LIMIT",
        )


class ServerError(APIException):
    """Raised when server encounters an error."""

    def __init__(self, detail: str = "Internal server error"):
        super().__init__(
            status_code=500,
            detail=detail,
            error_code="SERVER_ERROR",
        )


class ServiceUnavailableError(APIException):
    """Raised when service is temporarily unavailable."""

    def __init__(self, detail: str = "Service unavailable"):
        super().__init__(
            status_code=503,
            detail=detail,
            error_code="SERVICE_UNAVAILABLE",
        )
