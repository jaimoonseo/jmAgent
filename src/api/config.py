"""API Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


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
        "http://localhost:8080",
        "http://localhost:5173",
    ]
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]

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
