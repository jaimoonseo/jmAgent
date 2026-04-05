"""Plugin manager for lifecycle management and hook execution."""

from typing import Dict, List, Any, Optional

from src.logging.logger import StructuredLogger
from src.errors.exceptions import JmAgentError
from src.plugins.base import Plugin


logger = StructuredLogger(__name__)


class PluginManager:
    """Manages plugin lifecycle and hook execution.

    The PluginManager handles:
    - Plugin registration and unregistration
    - Plugin enable/disable state management
    - Hook execution across all registered plugins
    - Graceful error handling for plugin failures
    """

    def __init__(self) -> None:
        """Initialize PluginManager with empty plugin registry."""
        self._plugins: Dict[str, Plugin] = {}

    def register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin with the manager.

        If a plugin with the same name already exists, it will be replaced.

        Args:
            plugin: Plugin instance to register.
        """
        self._plugins[plugin.name] = plugin
        logger.info(
            f"Plugin registered: {plugin.name}",
            extra={"plugin_name": plugin.name, "version": plugin.version}
        )

    def unregister_plugin(self, plugin_name: str) -> None:
        """Unregister a plugin by name.

        Does nothing if plugin doesn't exist (idempotent).

        Args:
            plugin_name: Name of the plugin to unregister.
        """
        if plugin_name in self._plugins:
            del self._plugins[plugin_name]
            logger.info(
                f"Plugin unregistered: {plugin_name}",
                extra={"plugin_name": plugin_name}
            )

    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get a registered plugin by name.

        Args:
            plugin_name: Name of the plugin.

        Returns:
            Plugin instance or None if not found.
        """
        return self._plugins.get(plugin_name)

    def get_plugin_count(self) -> int:
        """Get the number of registered plugins.

        Returns:
            Count of registered plugins.
        """
        return len(self._plugins)

    def list_plugins(self) -> Dict[str, Plugin]:
        """Get dictionary of all registered plugins.

        Returns:
            Dictionary mapping plugin names to Plugin instances.
        """
        return dict(self._plugins)

    def enable_plugin(self, plugin_name: str) -> None:
        """Enable a plugin by name.

        Args:
            plugin_name: Name of the plugin to enable.

        Raises:
            JmAgentError: If plugin doesn't exist.
        """
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            raise JmAgentError(f"Plugin not found: {plugin_name}")

        plugin.enable()
        logger.info(
            f"Plugin enabled: {plugin_name}",
            extra={"plugin_name": plugin_name}
        )

    def disable_plugin(self, plugin_name: str) -> None:
        """Disable a plugin by name.

        Args:
            plugin_name: Name of the plugin to disable.

        Raises:
            JmAgentError: If plugin doesn't exist.
        """
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            raise JmAgentError(f"Plugin not found: {plugin_name}")

        plugin.disable()
        logger.info(
            f"Plugin disabled: {plugin_name}",
            extra={"plugin_name": plugin_name}
        )

    async def execute_hook(
        self,
        hook: str,
        *args: Any,
        **kwargs: Any
    ) -> List[Any]:
        """Execute a hook on all enabled plugins.

        Plugins are executed in the order they were registered.
        If a plugin fails, the error is logged but execution continues
        for other plugins (graceful degradation).

        Args:
            hook: Hook name to execute.
            *args: Positional arguments to pass to plugins.
            **kwargs: Keyword arguments to pass to plugins.

        Returns:
            List of results from each plugin that executed.
        """
        results: List[Any] = []

        logger.debug(
            f"Executing hook: {hook}",
            extra={"hook": hook, "plugin_count": len(self._plugins)}
        )

        for plugin_name, plugin in self._plugins.items():
            if not plugin.is_enabled():
                continue

            try:
                result = await plugin.execute(hook, *args, **kwargs)
                results.append(result)
                logger.debug(
                    f"Plugin hook executed: {plugin_name}",
                    extra={"plugin": plugin_name, "hook": hook}
                )
            except Exception as e:
                # Graceful degradation: log error but continue
                logger.error(
                    f"Plugin execution failed: {plugin_name}",
                    extra={
                        "plugin": plugin_name,
                        "hook": hook,
                        "error": str(e)
                    }
                )
                # Add error result so caller knows about failures
                results.append({
                    "plugin": plugin_name,
                    "hook": hook,
                    "error": str(e),
                    "status": "failed"
                })

        return results

    def get_enabled_plugins(self) -> Dict[str, Plugin]:
        """Get dictionary of all enabled plugins.

        Returns:
            Dictionary mapping plugin names to enabled Plugin instances.
        """
        return {
            name: plugin
            for name, plugin in self._plugins.items()
            if plugin.is_enabled()
        }

    def get_disabled_plugins(self) -> Dict[str, Plugin]:
        """Get dictionary of all disabled plugins.

        Returns:
            Dictionary mapping plugin names to disabled Plugin instances.
        """
        return {
            name: plugin
            for name, plugin in self._plugins.items()
            if not plugin.is_enabled()
        }

    def __repr__(self) -> str:
        """String representation of plugin manager."""
        enabled = sum(1 for p in self._plugins.values() if p.is_enabled())
        return f"PluginManager(plugins={len(self._plugins)}, enabled={enabled})"
