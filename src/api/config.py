"""API Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List, Optional
import os
import secrets


class APISettings(BaseSettings):
    """API settings with environment variable support."""

    # Server settings
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    reload: bool = False

    # API metadata
    api_title: str = "jmAgent API"
    api_version: str = "1.0.0"
    api_description: str = "REST API for jmAgent - Claude coding assistant"

    # CORS settings
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:6110",  # Frontend dev server
        "http://localhost:8080",
    ]
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]

    # JWT settings
    jwt_secret_key: str = Field(
        default_factory=lambda: os.getenv("JMAGENT_API_JWT_SECRET_KEY", secrets.token_urlsafe(32))
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30

    # API Key settings
    api_key: Optional[str] = Field(default=None)

    # Rate limiting settings
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 100

    # Logging settings
    log_level: str = "INFO"
    enable_request_logging: bool = True
    enable_error_logging: bool = True

    model_config = SettingsConfigDict(
        env_prefix="JMAGENT_API_",
        env_file=".env",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from environment
    )


# Global settings instance
settings = APISettings()
