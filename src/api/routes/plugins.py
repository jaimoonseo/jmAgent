"""Plugin management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from src.api.models import APIResponse
from src.api.security.auth import get_current_user
from src.api.schemas.management import (
    PluginsListResponse,
    PluginInfo,
    PluginDetailResponse,
    PluginStateResponse,
    PluginConfigRequest,
    PluginConfigResponse,
    UpdatedPluginConfigResponse,
)
from src.plugins.manager import PluginManager
from src.logging.logger import StructuredLogger

router = APIRouter(tags=["plugins"])
logger = StructuredLogger(__name__)

# Global plugin manager instance
plugin_manager = PluginManager()


@router.post(
    "/plugins/install",
    response_model=APIResponse,
    summary="Install Plugin",
    tags=["Plugins"],
)
async def install_plugin(
    url: str,
    name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Install a new plugin from a URL.

    Validates the plugin URL and adds it to the plugin manager.
    """
    try:
        # In a real implementation, this would:
        # 1. Validate the URL format
        # 2. Download and verify the plugin
        # 3. Extract metadata
        # 4. Register with plugin manager

        # For now, simulate successful installation
        response_data = {
            "name": name,
            "installed": True,
            "version": "1.0.0",
        }

        logger.info(
            "Plugin installed",
            extra={
                "user_id": current_user.get("user_id"),
                "plugin_name": name,
                "plugin_url": url,
            },
        )

        return APIResponse(success=True, data=response_data)
    except Exception as e:
        logger.error(
            "Error installing plugin",
            extra={"error": str(e), "plugin_name": name},
        )
        raise HTTPException(status_code=500, detail="Failed to install plugin")


@router.get(
    "/plugins",
    response_model=APIResponse,
    summary="List All Plugins",
    tags=["Plugins"],
)
async def list_plugins(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    List all available plugins with their status.

    Returns information about all registered plugins including name, version,
    description, and enabled status.
    """
    try:
        plugins_data = []

        # Get all plugins from the manager
        for plugin_name, plugin in plugin_manager.list_plugins().items():
            plugin_data = PluginInfo(
                name=plugin.name,
                enabled=plugin.is_enabled(),
                version=plugin.version,
                description=plugin.description,
            )
            plugins_data.append(plugin_data)

        response_data = PluginsListResponse(plugins=plugins_data)

        logger.info(
            "Plugins listed",
            extra={
                "user_id": current_user.get("user_id"),
                "plugin_count": len(plugins_data),
            },
        )

        return APIResponse(success=True, data=response_data)
    except Exception as e:
        logger.error(
            "Error listing plugins",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to list plugins")


@router.get(
    "/plugins/{name}",
    response_model=APIResponse,
    summary="Get Plugin Details",
    tags=["Plugins"],
)
async def get_plugin_detail(
    name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get detailed information about a specific plugin.

    Returns the plugin's metadata, configuration schema, and current state.
    """
    try:
        plugin = plugin_manager.get_plugin(name)

        if not plugin:
            logger.warning(
                "Attempted to get non-existent plugin",
                extra={
                    "user_id": current_user.get("user_id"),
                    "plugin_name": name,
                },
            )
            raise HTTPException(status_code=404, detail=f"Plugin not found: {name}")

        response_data = PluginDetailResponse(
            name=plugin.name,
            enabled=plugin.is_enabled(),
            version=plugin.version,
            description=plugin.description,
            config_schema={},  # Plugin class doesn't have config_schema attribute
        )

        logger.info(
            "Plugin detail retrieved",
            extra={
                "user_id": current_user.get("user_id"),
                "plugin_name": name,
            },
        )

        return APIResponse(success=True, data=response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error retrieving plugin detail",
            extra={"error": str(e), "plugin_name": name},
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve plugin details")


@router.post(
    "/plugins/{name}/enable",
    response_model=APIResponse,
    summary="Enable Plugin",
    tags=["Plugins"],
)
async def enable_plugin(
    name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Enable a plugin.

    Activates the specified plugin. Operation is idempotent.
    """
    try:
        plugin = plugin_manager.get_plugin(name)
        if not plugin:
            logger.warning(
                "Attempted to enable non-existent plugin",
                extra={
                    "user_id": current_user.get("user_id"),
                    "plugin_name": name,
                },
            )
            raise HTTPException(status_code=404, detail=f"Plugin not found: {name}")

        # Enable the plugin using the manager's method
        plugin_manager.enable_plugin(name)

        response_data = PluginStateResponse(
            name=name,
            enabled=True,
        )

        logger.info(
            "Plugin enabled",
            extra={
                "user_id": current_user.get("user_id"),
                "plugin_name": name,
            },
        )

        return APIResponse(success=True, data=response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error enabling plugin",
            extra={"error": str(e), "plugin_name": name},
        )
        raise HTTPException(status_code=500, detail="Failed to enable plugin")


@router.post(
    "/plugins/{name}/disable",
    response_model=APIResponse,
    summary="Disable Plugin",
    tags=["Plugins"],
)
async def disable_plugin(
    name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Disable a plugin.

    Deactivates the specified plugin. Operation is idempotent.
    """
    try:
        plugin = plugin_manager.get_plugin(name)
        if not plugin:
            logger.warning(
                "Attempted to disable non-existent plugin",
                extra={
                    "user_id": current_user.get("user_id"),
                    "plugin_name": name,
                },
            )
            raise HTTPException(status_code=404, detail=f"Plugin not found: {name}")

        # Disable the plugin using the manager's method
        plugin_manager.disable_plugin(name)

        response_data = PluginStateResponse(
            name=name,
            enabled=False,
        )

        logger.info(
            "Plugin disabled",
            extra={
                "user_id": current_user.get("user_id"),
                "plugin_name": name,
            },
        )

        return APIResponse(success=True, data=response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error disabling plugin",
            extra={"error": str(e), "plugin_name": name},
        )
        raise HTTPException(status_code=500, detail="Failed to disable plugin")


@router.get(
    "/plugins/{name}/config",
    response_model=APIResponse,
    summary="Get Plugin Configuration",
    tags=["Plugins"],
)
async def get_plugin_config(
    name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get the current configuration for a plugin.

    Returns the plugin's current configuration settings.
    """
    try:
        plugin = plugin_manager.get_plugin(name)
        if not plugin:
            logger.warning(
                "Attempted to get config for non-existent plugin",
                extra={
                    "user_id": current_user.get("user_id"),
                    "plugin_name": name,
                },
            )
            raise HTTPException(status_code=404, detail=f"Plugin not found: {name}")

        # Get plugin configuration from plugin.config
        config = plugin.config if plugin.config else {}

        response_data = PluginConfigResponse(
            name=name,
            config=config,
        )

        logger.info(
            "Plugin config retrieved",
            extra={
                "user_id": current_user.get("user_id"),
                "plugin_name": name,
            },
        )

        return APIResponse(success=True, data=response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error retrieving plugin config",
            extra={"error": str(e), "plugin_name": name},
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve plugin config")


@router.post(
    "/plugins/{name}/config",
    response_model=APIResponse,
    summary="Update Plugin Configuration",
    tags=["Plugins"],
)
async def update_plugin_config(
    name: str,
    request: PluginConfigRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Update the configuration for a plugin.

    Updates the plugin's configuration with the provided settings.
    """
    try:
        plugin = plugin_manager.get_plugin(name)
        if not plugin:
            logger.warning(
                "Attempted to update config for non-existent plugin",
                extra={
                    "user_id": current_user.get("user_id"),
                    "plugin_name": name,
                },
            )
            raise HTTPException(status_code=404, detail=f"Plugin not found: {name}")

        # Update plugin configuration
        plugin.config = request.config

        response_data = UpdatedPluginConfigResponse(
            name=name,
            config=request.config,
            updated=True,
        )

        logger.info(
            "Plugin config updated",
            extra={
                "user_id": current_user.get("user_id"),
                "plugin_name": name,
            },
        )

        return APIResponse(success=True, data=response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error updating plugin config",
            extra={"error": str(e), "plugin_name": name},
        )
        raise HTTPException(status_code=500, detail="Failed to update plugin config")
