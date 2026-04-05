"""Base Plugin class and interfaces for jmAgent plugin system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Plugin(ABC):
    """Abstract base class for all jmAgent plugins.

    Plugins provide extensibility to jmAgent by hooking into various action
    lifecycle events (before/after actions, error handling).

    Attributes:
        name: Unique plugin identifier
        version: Plugin version string (semantic versioning)
        description: Human-readable plugin description
        author: Plugin author name
    """

    # Class-level metadata that must be defined in subclasses
    name: str = ""
    version: str = ""
    description: str = ""
    author: str = ""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize plugin with optional configuration.

        Args:
            config: Optional configuration dictionary for the plugin.
                   Plugins can use this to customize behavior.
        """
        self.config = config
        self._enabled = False

    def enable(self) -> None:
        """Enable the plugin.

        Once enabled, the plugin will be called on relevant hooks.
        This method is idempotent.
        """
        self._enabled = True

    def disable(self) -> None:
        """Disable the plugin.

        Once disabled, the plugin will not be called on hooks.
        This method is idempotent.
        """
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if plugin is currently enabled.

        Returns:
            True if plugin is enabled, False otherwise.
        """
        return self._enabled

    @abstractmethod
    async def execute(self, hook: str, *args: Any, **kwargs: Any) -> Any:
        """Execute plugin hook.

        This method is called when the plugin's hook is triggered.
        Only called if the plugin is enabled.

        Args:
            hook: Hook name (e.g., 'before_generate', 'after_refactor')
            *args: Positional arguments passed to the hook
            **kwargs: Keyword arguments passed to the hook

        Returns:
            Plugin-specific return value. Can be any type.

        Raises:
            Exception: Plugins may raise exceptions which will be
                      handled by PluginManager with graceful degradation.
        """
        pass

    def get_metadata(self) -> Dict[str, str]:
        """Get plugin metadata.

        Returns:
            Dictionary containing plugin metadata.
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
        }

    def __repr__(self) -> str:
        """String representation of plugin."""
        return f"Plugin(name={self.name}, version={self.version}, enabled={self._enabled})"
