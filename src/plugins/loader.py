"""Plugin discovery and loading for jmAgent plugin system."""

import sys
import importlib.util
import re
from pathlib import Path
from typing import List, Type, Optional, Dict, Any

from src.logging.logger import StructuredLogger
from src.errors.exceptions import PluginValidationError
from src.plugins.base import Plugin


logger = StructuredLogger(__name__)


class PluginLoader:
    """Discovers and loads plugins from the plugin directory.

    The PluginLoader scans a directory for Python modules containing
    Plugin subclasses and provides methods to discover and load them.
    """

    def __init__(self, plugin_dir: str) -> None:
        """Initialize PluginLoader.

        Args:
            plugin_dir: Directory path containing plugins.
        """
        self.plugin_dir = plugin_dir

    def discover_plugins(self) -> List[Type[Plugin]]:
        """Discover all plugins in the plugin directory.

        Scans the plugin directory for Python modules and identifies
        classes that inherit from Plugin.

        Returns:
            List of Plugin subclasses found in the directory.
        """
        plugin_classes: List[Type[Plugin]] = []

        try:
            plugin_path = Path(self.plugin_dir)
            if not plugin_path.exists():
                logger.warning(
                    "Plugin directory does not exist",
                    extra={"plugin_dir": self.plugin_dir}
                )
                return []

            # Find all .py files in the plugin directory
            for py_file in plugin_path.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue

                try:
                    plugin_classes.extend(
                        self._load_plugin_module(py_file)
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to load plugin module {py_file.name}",
                        extra={
                            "file": py_file.name,
                            "error": str(e)
                        }
                    )
                    continue

        except Exception as e:
            logger.error(
                "Error during plugin discovery",
                extra={"error": str(e)}
            )

        return plugin_classes

    def _validate_plugin_class(self, plugin_class: Type[Plugin]) -> None:
        """Validate that a plugin class implements required interface.

        Args:
            plugin_class: Plugin class to validate.

        Raises:
            PluginValidationError: If validation fails.
        """
        # Check required methods exist
        required_methods = ["enable", "disable", "is_enabled", "execute"]
        for method in required_methods:
            if not hasattr(plugin_class, method):
                raise PluginValidationError(
                    f"Plugin {plugin_class.__name__} missing required method: {method}"
                )

        # Check required metadata attributes
        required_attrs = ["name", "version", "description", "author"]
        for attr in required_attrs:
            if not hasattr(plugin_class, attr):
                raise PluginValidationError(
                    f"Plugin {plugin_class.__name__} missing required attribute: {attr}"
                )

        # Validate metadata values
        name = getattr(plugin_class, "name", "")
        version = getattr(plugin_class, "version", "")
        description = getattr(plugin_class, "description", "")
        author = getattr(plugin_class, "author", "")

        if not isinstance(name, str) or not name:
            raise PluginValidationError(
                f"Plugin {plugin_class.__name__} has invalid name: {name}"
            )

        if not isinstance(version, str) or not version:
            raise PluginValidationError(
                f"Plugin {plugin_class.__name__} has invalid version: {version}"
            )

        # Validate semantic versioning format (major.minor.patch)
        if not re.match(r"^\d+\.\d+\.\d+", version):
            raise PluginValidationError(
                f"Plugin {plugin_class.__name__} has invalid version format '{version}' "
                "(expected semantic versioning: major.minor.patch)"
            )

        if not isinstance(description, str) or not description:
            raise PluginValidationError(
                f"Plugin {plugin_class.__name__} has invalid description: {description}"
            )

        if not isinstance(author, str) or not author:
            raise PluginValidationError(
                f"Plugin {plugin_class.__name__} has invalid author: {author}"
            )

    def _load_plugin_module(self, py_file: Path) -> List[Type[Plugin]]:
        """Load a single plugin module and extract Plugin classes.

        Args:
            py_file: Path to Python module file.

        Returns:
            List of Plugin subclasses found in the module.
        """
        plugin_classes: List[Type[Plugin]] = []

        try:
            # Create a unique module name
            module_name = f"jmagent_plugin_{py_file.stem}"

            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(
                module_name,
                py_file
            )
            if spec is None or spec.loader is None:
                return []

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find all Plugin subclasses in the module
            for attr_name in dir(module):
                if attr_name.startswith("_"):
                    continue

                attr = getattr(module, attr_name)

                # Check if it's a class and subclass of Plugin
                if (
                    isinstance(attr, type) and
                    issubclass(attr, Plugin) and
                    attr is not Plugin
                ):
                    try:
                        # Validate the plugin class
                        self._validate_plugin_class(attr)
                        plugin_classes.append(attr)
                        logger.debug(
                            f"Discovered plugin class {attr_name}",
                            extra={
                                "module": py_file.name,
                                "class": attr_name
                            }
                        )
                    except PluginValidationError as e:
                        logger.warning(
                            f"Plugin validation failed: {attr_name}",
                            extra={
                                "module": py_file.name,
                                "class": attr_name,
                                "error": str(e)
                            }
                        )

        except PluginValidationError:
            # Re-raise validation errors during discovery
            raise
        except Exception as e:
            logger.error(
                f"Error loading plugin module {py_file.name}",
                extra={
                    "file": py_file.name,
                    "error": str(e)
                }
            )

        return plugin_classes

    def load_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[Plugin]:
        """Load a specific plugin by name and instantiate it.

        Args:
            plugin_name: Name of the plugin to load (class name or module name).
            config: Optional configuration dictionary for the plugin.

        Returns:
            Instantiated plugin or None if not found.
        """
        try:
            plugin_classes = self.discover_plugins()

            for plugin_class in plugin_classes:
                # Match by class name
                if plugin_class.__name__ == plugin_name:
                    logger.info(
                        f"Loading plugin {plugin_name}",
                        extra={"plugin_name": plugin_name}
                    )
                    return plugin_class(config=config)

            logger.warning(
                f"Plugin not found: {plugin_name}",
                extra={"plugin_name": plugin_name}
            )
            return None

        except Exception as e:
            logger.error(
                f"Error loading plugin {plugin_name}",
                extra={
                    "plugin_name": plugin_name,
                    "error": str(e)
                }
            )
            return None
