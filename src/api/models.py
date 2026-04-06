"""Shared API data models and schemas."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict, List
from enum import Enum
from datetime import datetime, timezone


class HealthStatus(str, Enum):
    """Health check status enum."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class APIResponse(BaseModel):
    """Standard API response wrapper."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {"key": "value"},
                "error": None,
                "error_code": None,
            }
        }
    )

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if applicable")
    error_code: Optional[str] = Field(None, description="Error code if applicable")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of the response",
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": "Resource not found",
                "error_code": "NOT_FOUND",
            }
        }
    )

    success: bool = False
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of the error",
    )


class HealthComponent(BaseModel):
    """Health status of a single component."""

    name: str = Field(..., description="Component name")
    status: HealthStatus = Field(..., description="Component health status")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional component details"
    )


class HealthCheck(BaseModel):
    """Server health check response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime_seconds": 3600.5,
                "components": [
                    {
                        "name": "bedrock",
                        "status": "healthy",
                        "details": {"available": True},
                    },
                    {
                        "name": "cache",
                        "status": "healthy",
                        "details": {"items": 42},
                    },
                ],
            }
        }
    )

    status: HealthStatus = Field(..., description="Overall server health status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of the health check",
    )
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    components: Optional[List[HealthComponent]] = Field(
        None, description="Health status of individual components"
    )


class StatusResponse(BaseModel):
    """Server status response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version": "1.0.0",
                "api_version": "v1",
                "status": "operational",
            }
        }
    )

    version: str = Field(..., description="API version")
    api_version: str = Field(..., description="API version identifier (e.g., v1)")
    status: str = Field(..., description="Overall server status")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of the status check",
    )


class TokenPayload(BaseModel):
    """JWT token payload."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user123",
                "agent_id": "agent456",
                "iat": 1234567890,
                "exp": 1234571490,
            }
        }
    )

    user_id: str = Field(..., description="User identifier")
    agent_id: str = Field(..., description="Agent identifier")
    iat: int = Field(..., description="Issued at timestamp")
    exp: int = Field(..., description="Expiration timestamp")


class TokenResponse(BaseModel):
    """JWT token response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 1800,
                },
                "error": None,
                "error_code": None,
            }
        }
    )

    success: bool = Field(..., description="Whether token creation was successful")
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Token data including token string and expiration",
    )
    error: Optional[str] = Field(None, description="Error message if applicable")
    error_code: Optional[str] = Field(None, description="Error code if applicable")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of the response",
    )
