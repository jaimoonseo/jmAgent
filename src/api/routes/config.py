"""Configuration management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from src.api.models import APIResponse
from src.api.config import settings
from src.api.security.auth import get_current_user
from src.api.schemas.management import (
    UpdateConfigRequest,
    UpdateAllConfigRequest,
    ConfigResponse,
    UpdatedConfigResponse,
    ReplacedConfigResponse,
    DeletedConfigResponse,
    ResetConfigResponse,
)
from src.logging.logger import StructuredLogger

router = APIRouter(tags=["config"])
logger = StructuredLogger(__name__)

# Default values for settings
SETTING_DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8000,
    "debug": False,
    "reload": False,
    "api_title": "jmAgent API",
    "api_version": "1.0.0",
    "api_description": "REST API for jmAgent - Claude coding assistant",
    "jwt_expiration_minutes": 30,
    "rate_limit_enabled": True,
    "rate_limit_per_minute": 100,
    "log_level": "INFO",
    "enable_request_logging": True,
    "enable_error_logging": True,
}

# Track current config overrides (in-memory for this session)
_config_overrides: Dict[str, Any] = {}


def get_all_settings() -> Dict[str, Any]:
    """Get all current settings including overrides."""
    current_settings = {
        "host": _config_overrides.get("host", settings.host),
        "port": _config_overrides.get("port", settings.port),
        "debug": _config_overrides.get("debug", settings.debug),
        "reload": _config_overrides.get("reload", settings.reload),
        "api_title": _config_overrides.get("api_title", settings.api_title),
        "api_version": _config_overrides.get("api_version", settings.api_version),
        "api_description": _config_overrides.get(
            "api_description", settings.api_description
        ),
        "cors_origins": _config_overrides.get("cors_origins", settings.cors_origins),
        "cors_credentials": _config_overrides.get(
            "cors_credentials", settings.cors_credentials
        ),
        "cors_methods": _config_overrides.get("cors_methods", settings.cors_methods),
        "cors_headers": _config_overrides.get("cors_headers", settings.cors_headers),
        "jwt_secret_key": "***REDACTED***",  # Don't expose secret
        "jwt_algorithm": _config_overrides.get("jwt_algorithm", settings.jwt_algorithm),
        "jwt_expiration_minutes": _config_overrides.get(
            "jwt_expiration_minutes", settings.jwt_expiration_minutes
        ),
        "api_key": "***REDACTED***" if settings.api_key else None,
        "rate_limit_enabled": _config_overrides.get(
            "rate_limit_enabled", settings.rate_limit_enabled
        ),
        "rate_limit_per_minute": _config_overrides.get(
            "rate_limit_per_minute", settings.rate_limit_per_minute
        ),
        "log_level": _config_overrides.get("log_level", settings.log_level),
        "enable_request_logging": _config_overrides.get(
            "enable_request_logging", settings.enable_request_logging
        ),
        "enable_error_logging": _config_overrides.get(
            "enable_error_logging", settings.enable_error_logging
        ),
    }
    return current_settings


def is_admin(user: Dict[str, Any]) -> bool:
    """Check if user has admin privileges."""
    # Check for admin marker in JWT claims
    # In this implementation, we look for an 'admin' claim or specific user ID
    return user.get("admin", False) or user.get("user_id") == "admin_user"


@router.get(
    "/config",
    response_model=APIResponse,
    summary="Get All Configuration Settings",
    tags=["Config"],
)
async def get_config(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieve all current configuration settings.

    Returns all API configuration settings as a dictionary.
    Sensitive values like secret keys are redacted.
    """
    try:
        all_settings = get_all_settings()

        logger.info(
            "Configuration retrieved",
            extra={
                "user_id": current_user.get("user_id"),
                "setting_count": len(all_settings),
            },
        )

        return APIResponse(
            success=True,
            data=ConfigResponse(all_settings=all_settings),
        )
    except Exception as e:
        logger.error(
            "Error retrieving configuration",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve configuration")


@router.post(
    "/config",
    response_model=APIResponse,
    summary="Update Single Configuration Setting",
    tags=["Config"],
)
async def update_config(
    request: UpdateConfigRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Update a single configuration setting.

    Validates that the setting key exists and the value is valid.
    Returns the updated key and value.
    """
    try:
        # Validate that setting exists
        if request.key not in SETTING_DEFAULTS and request.key not in get_all_settings():
            logger.warning(
                "Attempted to update invalid setting",
                extra={
                    "user_id": current_user.get("user_id"),
                    "key": request.key,
                },
            )
            raise HTTPException(
                status_code=400,
                detail=f"Invalid setting key: {request.key}",
            )

        # Validate setting type based on known settings
        if request.key == "jwt_expiration_minutes" or request.key == "port":
            if not isinstance(request.value, int):
                raise HTTPException(
                    status_code=400,
                    detail=f"Setting {request.key} must be an integer",
                )

        if request.key == "jm_temperature":
            if not isinstance(request.value, (int, float)):
                raise HTTPException(
                    status_code=400,
                    detail="Temperature must be a number",
                )
            if not (0 <= request.value <= 1):
                raise HTTPException(
                    status_code=400,
                    detail="Temperature must be between 0 and 1",
                )

        if request.key in [
            "rate_limit_enabled",
            "debug",
            "reload",
            "cors_credentials",
            "enable_request_logging",
            "enable_error_logging",
        ]:
            if not isinstance(request.value, bool):
                raise HTTPException(
                    status_code=400,
                    detail=f"Setting {request.key} must be boolean",
                )

        # Store override
        _config_overrides[request.key] = request.value

        logger.info(
            "Configuration setting updated",
            extra={
                "user_id": current_user.get("user_id"),
                "key": request.key,
                "value": (
                    "***REDACTED***" if "secret" in request.key.lower() else request.value
                ),
            },
        )

        return APIResponse(
            success=True,
            data=UpdatedConfigResponse(
                updated=True,
                key=request.key,
                value=request.value,
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error updating configuration",
            extra={"error": str(e), "key": request.key},
        )
        raise HTTPException(status_code=500, detail="Failed to update configuration")


@router.put(
    "/config",
    response_model=APIResponse,
    summary="Replace All Configuration Settings",
    tags=["Config"],
)
async def replace_all_config(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Replace all configuration settings at once.

    Takes a dictionary of settings and replaces all current overrides.
    Returns the count of settings replaced.
    """
    try:
        # Validate all provided keys
        for key in request.keys():
            if key not in SETTING_DEFAULTS and key not in get_all_settings():
                logger.warning(
                    "Attempted to set invalid configuration key",
                    extra={
                        "user_id": current_user.get("user_id"),
                        "key": key,
                    },
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid setting key: {key}",
                )

        # Clear and replace all overrides
        _config_overrides.clear()
        _config_overrides.update(request)

        logger.info(
            "All configuration settings replaced",
            extra={
                "user_id": current_user.get("user_id"),
                "count": len(request),
            },
        )

        return APIResponse(
            success=True,
            data=ReplacedConfigResponse(
                replaced=True,
                count=len(request),
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error replacing configuration",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to replace configuration")


@router.delete(
    "/config/{key}",
    response_model=APIResponse,
    summary="Reset Single Configuration Setting to Default",
    tags=["Config"],
)
async def delete_config(
    key: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Reset a single configuration setting to its default value.

    Removes the setting override and reverts to the default value.
    Returns the setting key and its default value.
    """
    try:
        # Check if setting exists
        all_settings = get_all_settings()
        if key not in SETTING_DEFAULTS and key not in all_settings:
            logger.warning(
                "Attempted to delete invalid setting",
                extra={
                    "user_id": current_user.get("user_id"),
                    "key": key,
                },
            )
            raise HTTPException(
                status_code=404,
                detail=f"Setting not found: {key}",
            )

        # Get default value
        default_value = SETTING_DEFAULTS.get(key, getattr(settings, key, None))

        # Remove override if it exists
        if key in _config_overrides:
            del _config_overrides[key]

        logger.info(
            "Configuration setting reset to default",
            extra={
                "user_id": current_user.get("user_id"),
                "key": key,
            },
        )

        return APIResponse(
            success=True,
            data=DeletedConfigResponse(
                deleted=True,
                key=key,
                default_value=default_value,
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting configuration",
            extra={"error": str(e), "key": key},
        )
        raise HTTPException(status_code=500, detail="Failed to reset configuration")


@router.post(
    "/config/reset",
    response_model=APIResponse,
    summary="Reset All Configuration Settings to Defaults",
    tags=["Config"],
)
async def reset_config(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Reset all configuration settings to their default values.

    This is an admin-only operation. Only users with admin privileges can reset all settings.
    Returns the count of settings reset.
    """
    try:
        # Check admin privilege
        if not is_admin(current_user):
            logger.warning(
                "Non-admin user attempted to reset all configuration",
                extra={"user_id": current_user.get("user_id")},
            )
            raise HTTPException(
                status_code=403,
                detail="Only administrators can reset all configuration settings",
            )

        # Count settings before clearing
        count = len(_config_overrides)

        # Clear all overrides
        _config_overrides.clear()

        logger.info(
            "All configuration settings reset to defaults",
            extra={
                "user_id": current_user.get("user_id"),
                "reset_count": count,
            },
        )

        return APIResponse(
            success=True,
            data=ResetConfigResponse(
                reset=True,
                defaults_count=len(SETTING_DEFAULTS),
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error resetting configuration",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to reset configuration")
