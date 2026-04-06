"""JWT authentication and API key validation for jmAgent API."""

import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, HTTPBasic
import secrets

from src.logging.logger import StructuredLogger

logger = StructuredLogger(__name__)


class InvalidTokenError(Exception):
    """Raised when JWT token is invalid or expired."""

    pass


class JwtSettings(BaseSettings):
    """JWT configuration settings."""

    secret_key: str = Field(default_factory=lambda: os.getenv("JMAGENT_API_JWT_SECRET_KEY", secrets.token_urlsafe(32)))
    algorithm: str = "HS256"
    expiration_minutes: int = 30

    model_config = SettingsConfigDict(
        env_prefix="JMAGENT_API_JWT_",
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


def create_token(
    user_id: str,
    agent_id: str,
    settings: Optional[JwtSettings] = None,
) -> str:
    """
    Create a JWT token with user and agent information.

    Args:
        user_id: Unique user identifier
        agent_id: Unique agent identifier
        settings: JWT settings (uses default if not provided)

    Returns:
        JWT token string

    Raises:
        ValueError: If user_id or agent_id is empty
    """
    if not user_id or not agent_id:
        raise ValueError("user_id and agent_id cannot be empty")

    if settings is None:
        settings = JwtSettings()

    # Create payload
    now = datetime.now(timezone.utc)
    expiration = now + timedelta(minutes=settings.expiration_minutes)

    payload = {
        "user_id": user_id,
        "agent_id": agent_id,
        "iat": int(now.timestamp()),
        "exp": int(expiration.timestamp()),
    }

    # Encode token
    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    logger.info(
        "JWT token created",
        extra={
            "user_id": user_id,
            "agent_id": agent_id,
        },
    )

    return token


def verify_token(
    token: str,
    settings: Optional[JwtSettings] = None,
) -> Dict[str, Any]:
    """
    Verify a JWT token and return its payload.

    Args:
        token: JWT token string
        settings: JWT settings (uses default if not provided)

    Returns:
        Token payload dictionary

    Raises:
        InvalidTokenError: If token is invalid or expired
    """
    if settings is None:
        settings = JwtSettings()

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Attempt to verify expired token")
        raise InvalidTokenError("Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid token verification attempt", extra={"error": str(e)})
        raise InvalidTokenError("Invalid authentication credentials")


def get_current_user(
    token: str = Depends(HTTPBearer()),
    settings: Optional[JwtSettings] = None,
) -> Dict[str, Any]:
    """
    FastAPI dependency to get the current user from Bearer token.

    Args:
        token: Bearer token from HTTPBearer
        settings: JWT settings (uses default if not provided)

    Returns:
        Token payload with user_id and agent_id

    Raises:
        HTTPException: If token is invalid or missing
    """
    if settings is None:
        settings = JwtSettings()

    try:
        payload = verify_token(token.credentials, settings=settings)
        return payload
    except InvalidTokenError as e:
        logger.warning("Authentication failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


class APIKeyValidator:
    """Validator for API key authentication."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize API key validator.

        Args:
            api_key: Optional API key to validate against
        """
        self.api_key = api_key or os.getenv("JMAGENT_API_KEY")

    def validate(self, provided_key: Optional[str]) -> bool:
        """
        Validate an API key.

        Args:
            provided_key: API key to validate

        Returns:
            True if valid, False otherwise
        """
        if not self.api_key:
            # No API key configured
            return False

        if not provided_key:
            return False

        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(self.api_key, provided_key)


async def get_current_user_by_key(
    x_api_key: Optional[str] = Header(None),
    validator: Optional[APIKeyValidator] = None,
) -> Dict[str, Any]:
    """
    FastAPI dependency to get the current user from API key.

    Args:
        x_api_key: API key from x-api-key header
        validator: API key validator instance

    Returns:
        Dictionary with user info derived from API key

    Raises:
        HTTPException: If API key is invalid
    """
    if validator is None:
        validator = APIKeyValidator()

    if not validator.validate(x_api_key):
        logger.warning("Invalid API key authentication attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    # Return a minimal user context for API key auth
    return {
        "user_id": "api_user",
        "agent_id": "api_agent",
        "auth_type": "api_key",
    }
