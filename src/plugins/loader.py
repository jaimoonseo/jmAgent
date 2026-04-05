"""Plugin discovery and loading for jmAgent plugin system."""

import sys
import importlib.util
from pathlib import Path
from typing import List, Type, Optional, Dict, Any

from src.logging.logger import StructuredLogger
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
                    plugin_classes.append(attr)
                    logger.debug(
                        f"Discovered plugin class {attr_name}",
                        extra={
                            "module": py_file.name,
                            "class": attr_name
                        }
                    )

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
