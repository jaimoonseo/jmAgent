"""FastAPI REST API module for jmAgent."""

from src.api.main import app, create_app
from src.api.config import settings
from src.api.exceptions import (
    APIException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ServerError,
    ServiceUnavailableError,
)
from src.api.models import (
    APIResponse,
    ErrorResponse,
    HealthCheck,
    HealthStatus,
    StatusResponse,
)

__all__ = [
    "app",
    "create_app",
    "settings",
    "APIException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ServerError",
    "ServiceUnavailableError",
    "APIResponse",
    "ErrorResponse",
    "HealthCheck",
    "HealthStatus",
    "StatusResponse",
]
