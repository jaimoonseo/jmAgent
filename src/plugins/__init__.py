"""Plugin architecture for jmAgent."""

from .base import Plugin
from .manager import PluginManager
from .loader import PluginLoader

__all__ = [
    "Plugin",
    "PluginManager",
    "PluginLoader",
]
