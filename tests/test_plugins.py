"""Comprehensive tests for plugin architecture system."""

import pytest
import tempfile
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

from src.plugins.base import Plugin
from src.plugins.loader import PluginLoader
from src.plugins.manager import PluginManager
from src.errors.exceptions import JmAgentError


# ============================================================================
# Test Plugin Fixtures and Implementations
# ============================================================================

class SimplePlugin(Plugin):
    """Simple test plugin for testing."""

    name = "test_plugin"
    version = "1.0.0"
    description = "Test plugin for unit tests"
    author = "Test Author"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.execution_count = 0
        self.last_hook = None
        self.last_args = None
        self.last_kwargs = None

    async def execute(self, hook: str, *args, **kwargs) -> Any:
        """Execute plugin hook."""
        if not self.is_enabled():
            return None
        self.execution_count += 1
        self.last_hook = hook
        self.last_args = args
        self.last_kwargs = kwargs
        return {"status": "success", "hook": hook}


class FailingPlugin(Plugin):
    """Plugin that fails on execute."""

    name = "failing_plugin"
    version = "1.0.0"
    description = "Plugin that fails"
    author = "Test Author"

    async def execute(self, hook: str, *args, **kwargs) -> Any:
        """Execute plugin hook and fail."""
        raise ValueError("Plugin execution failed")


class HookTrackingPlugin(Plugin):
    """Plugin that tracks hooks executed."""

    name = "hook_tracking_plugin"
    version = "1.0.0"
    description = "Tracks hooks"
    author = "Test Author"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.hooks_executed = []

    async def execute(self, hook: str, *args, **kwargs) -> Any:
        """Track hook execution."""
        if not self.is_enabled():
            return None
        self.hooks_executed.append(hook)
        return {"tracked": hook}


@pytest.fixture
def temp_plugin_dir():
    """Create a temporary plugin directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def plugin_metadata_file(temp_plugin_dir):
    """Create a test plugin metadata file."""
    pytest.importorskip("yaml")
    import yaml

    metadata = {
        "name": "test_plugin",
        "version": "1.0.0",
        "description": "Test plugin",
        "author": "Test Author",
        "dependencies": [],
        "hooks": ["before_generate", "after_generate"]
    }
    metadata_path = temp_plugin_dir / "plugin.yaml"
    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f)
    return metadata_path


# ============================================================================
# TestPluginBase - Base Plugin Class Tests
# ============================================================================

class TestPluginBase:
    """Test base Plugin class."""

    def test_plugin_init(self):
        """Test Plugin initialization."""
        plugin = SimplePlugin()
        assert plugin.name == "test_plugin"
        assert plugin.version == "1.0.0"
        assert plugin.description == "Test plugin for unit tests"
        assert plugin.author == "Test Author"
        assert plugin.is_enabled() is False  # Should be disabled by default

    def test_plugin_init_with_config(self):
        """Test Plugin initialization with configuration."""
        config = {"timeout": 30, "max_retries": 3}
        plugin = SimplePlugin(config=config)
        assert plugin.config == config

    def test_plugin_enable(self):
        """Test enabling a plugin."""
        plugin = SimplePlugin()
        assert plugin.is_enabled() is False
        plugin.enable()
        assert plugin.is_enabled() is True

    def test_plugin_disable(self):
        """Test disabling a plugin."""
        plugin = SimplePlugin()
        plugin.enable()
        assert plugin.is_enabled() is True
        plugin.disable()
        assert plugin.is_enabled() is False

    def test_plugin_enable_idempotent(self):
        """Test that enabling is idempotent."""
        plugin = SimplePlugin()
        plugin.enable()
        plugin.enable()
        assert plugin.is_enabled() is True

    def test_plugin_disable_idempotent(self):
        """Test that disabling is idempotent."""
        plugin = SimplePlugin()
        plugin.enable()
        plugin.disable()
        plugin.disable()
        assert plugin.is_enabled() is False

    @pytest.mark.asyncio
    async def test_plugin_execute(self):
        """Test plugin execution."""
        plugin = SimplePlugin()
        plugin.enable()
        result = await plugin.execute("before_generate", arg1="value1")
        assert result["status"] == "success"
        assert result["hook"] == "before_generate"
        assert plugin.execution_count == 1

    @pytest.mark.asyncio
    async def test_plugin_execute_disabled(self):
        """Test that disabled plugin doesn't execute."""
        plugin = SimplePlugin()
        # Don't enable
        result = await plugin.execute("before_generate")
        # Should return None and not execute
        assert result is None
        assert plugin.execution_count == 0

    @pytest.mark.asyncio
    async def test_plugin_execute_multiple_hooks(self):
        """Test executing multiple hooks."""
        plugin = SimplePlugin()
        plugin.enable()
        await plugin.execute("before_generate")
        await plugin.execute("after_generate")
        await plugin.execute("before_refactor")
        assert plugin.execution_count == 3
        assert plugin.last_hook == "before_refactor"

    @pytest.mark.asyncio
    async def test_plugin_execute_with_args_kwargs(self):
        """Test plugin execution with arguments."""
        plugin = SimplePlugin()
        plugin.enable()
        await plugin.execute("test_hook", "arg1", "arg2", key1="value1", key2="value2")
        assert plugin.last_args == ("arg1", "arg2")
        assert plugin.last_kwargs == {"key1": "value1", "key2": "value2"}

    def test_plugin_metadata(self):
        """Test plugin metadata access."""
        plugin = SimplePlugin()
        metadata = plugin.get_metadata()
        assert metadata["name"] == "test_plugin"
        assert metadata["version"] == "1.0.0"
        assert metadata["author"] == "Test Author"

    def test_plugin_with_empty_config(self):
        """Test plugin with empty config."""
        plugin = SimplePlugin(config={})
        assert plugin.config == {}

    def test_plugin_with_none_config(self):
        """Test plugin with None config."""
        plugin = SimplePlugin(config=None)
        assert plugin.config is None


# ============================================================================
# TestPluginManager - Plugin Manager Tests
# ============================================================================

class TestPluginManager:
    """Test PluginManager functionality."""

    def test_manager_init(self):
        """Test PluginManager initialization."""
        manager = PluginManager()
        assert isinstance(manager, PluginManager)
        assert manager.get_plugin_count() == 0

    def test_register_plugin(self):
        """Test registering a plugin."""
        manager = PluginManager()
        plugin = SimplePlugin()
        manager.register_plugin(plugin)
        assert manager.get_plugin_count() == 1
        assert manager.get_plugin("test_plugin") == plugin

    def test_register_multiple_plugins(self):
        """Test registering multiple plugins."""
        manager = PluginManager()
        plugin1 = SimplePlugin()
        plugin2 = HookTrackingPlugin()
        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)
        assert manager.get_plugin_count() == 2

    def test_get_plugin(self):
        """Test retrieving a plugin."""
        manager = PluginManager()
        plugin = SimplePlugin()
        manager.register_plugin(plugin)
        retrieved = manager.get_plugin("test_plugin")
        assert retrieved == plugin

    def test_get_nonexistent_plugin(self):
        """Test getting a nonexistent plugin returns None."""
        manager = PluginManager()
        result = manager.get_plugin("nonexistent")
        assert result is None

    def test_list_plugins(self):
        """Test listing all plugins."""
        manager = PluginManager()
        plugin1 = SimplePlugin()
        plugin2 = HookTrackingPlugin()
        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)
        plugins = manager.list_plugins()
        assert len(plugins) == 2
        assert "test_plugin" in plugins
        assert "hook_tracking_plugin" in plugins

    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        manager = PluginManager()
        plugin = SimplePlugin()
        manager.register_plugin(plugin)
        assert manager.get_plugin_count() == 1
        manager.unregister_plugin("test_plugin")
        assert manager.get_plugin_count() == 0

    def test_unregister_nonexistent_plugin(self):
        """Test unregistering a nonexistent plugin."""
        manager = PluginManager()
        # Should not raise
        manager.unregister_plugin("nonexistent")
        assert manager.get_plugin_count() == 0

    def test_enable_plugin(self):
        """Test enabling a plugin through manager."""
        manager = PluginManager()
        plugin = SimplePlugin()
        manager.register_plugin(plugin)
        assert plugin.is_enabled() is False
        manager.enable_plugin("test_plugin")
        assert plugin.is_enabled() is True

    def test_disable_plugin(self):
        """Test disabling a plugin through manager."""
        manager = PluginManager()
        plugin = SimplePlugin()
        manager.register_plugin(plugin)
        manager.enable_plugin("test_plugin")
        assert plugin.is_enabled() is True
        manager.disable_plugin("test_plugin")
        assert plugin.is_enabled() is False

    def test_enable_nonexistent_plugin(self):
        """Test enabling a nonexistent plugin raises error."""
        manager = PluginManager()
        with pytest.raises(JmAgentError):
            manager.enable_plugin("nonexistent")

    def test_disable_nonexistent_plugin(self):
        """Test disabling a nonexistent plugin raises error."""
        manager = PluginManager()
        with pytest.raises(JmAgentError):
            manager.disable_plugin("nonexistent")

    @pytest.mark.asyncio
    async def test_execute_hook(self):
        """Test executing a hook on all enabled plugins."""
        manager = PluginManager()
        plugin1 = SimplePlugin()
        plugin2 = HookTrackingPlugin()
        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)
        manager.enable_plugin("test_plugin")
        manager.enable_plugin("hook_tracking_plugin")

        results = await manager.execute_hook("before_generate", arg1="value1")
        assert len(results) == 2
        assert plugin1.last_hook == "before_generate"
        assert "before_generate" in plugin2.hooks_executed

    @pytest.mark.asyncio
    async def test_execute_hook_disabled_plugins_skipped(self):
        """Test that disabled plugins are skipped."""
        manager = PluginManager()
        plugin1 = SimplePlugin()
        plugin2 = SimplePlugin()
        plugin2.name = "test_plugin_2"
        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)
        manager.enable_plugin("test_plugin")
        # Don't enable test_plugin_2

        results = await manager.execute_hook("before_generate")
        assert len(results) == 1
        assert plugin1.execution_count == 1
        assert plugin2.execution_count == 0

    @pytest.mark.asyncio
    async def test_execute_hook_with_failing_plugin(self):
        """Test executing hook with a failing plugin."""
        manager = PluginManager()
        plugin1 = SimplePlugin()
        plugin2 = FailingPlugin()
        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)
        manager.enable_plugin("test_plugin")
        manager.enable_plugin("failing_plugin")

        # Should gracefully handle failure
        results = await manager.execute_hook("before_generate")
        # Should have results from both plugins
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_execute_hook_no_plugins(self):
        """Test executing hook with no plugins."""
        manager = PluginManager()
        results = await manager.execute_hook("before_generate")
        assert results == []

    @pytest.mark.asyncio
    async def test_execute_hook_no_enabled_plugins(self):
        """Test executing hook with no enabled plugins."""
        manager = PluginManager()
        plugin = SimplePlugin()
        manager.register_plugin(plugin)
        # Don't enable
        results = await manager.execute_hook("before_generate")
        assert results == []


# ============================================================================
# TestPluginLoader - Plugin Discovery and Loading Tests
# ============================================================================

class TestPluginLoader:
    """Test PluginLoader functionality."""

    def test_loader_init(self, temp_plugin_dir):
        """Test PluginLoader initialization."""
        loader = PluginLoader(str(temp_plugin_dir))
        assert loader.plugin_dir == str(temp_plugin_dir)

    def test_discover_plugins(self, temp_plugin_dir):
        """Test plugin discovery."""
        # Create a plugin module
        plugin_path = temp_plugin_dir / "sample_plugin.py"
        plugin_code = """
from src.plugins.base import Plugin
from typing import Optional, Dict, Any

class SamplePlugin(Plugin):
    name = "sample_plugin"
    version = "1.0.0"
    description = "Sample plugin"
    author = "Test Author"

    async def execute(self, hook: str, *args, **kwargs):
        return {"status": "success"}
"""
        plugin_path.write_text(plugin_code)

        loader = PluginLoader(str(temp_plugin_dir))
        plugins = loader.discover_plugins()
        assert len(plugins) > 0

    def test_load_plugin_from_file(self, temp_plugin_dir):
        """Test loading a plugin from file."""
        # Create a plugin module
        plugin_path = temp_plugin_dir / "test_sample_plugin.py"
        plugin_code = """
from src.plugins.base import Plugin
from typing import Optional, Dict, Any

class TestSamplePlugin(Plugin):
    name = "test_sample_plugin"
    version = "1.0.0"
    description = "Test sample plugin"
    author = "Test Author"

    async def execute(self, hook: str, *args, **kwargs):
        return {"status": "success"}
"""
        plugin_path.write_text(plugin_code)

        loader = PluginLoader(str(temp_plugin_dir))
        plugin_classes = loader.discover_plugins()
        assert len(plugin_classes) > 0

    def test_plugin_directory_does_not_exist(self):
        """Test with non-existent plugin directory."""
        loader = PluginLoader("/nonexistent/path")
        plugins = loader.discover_plugins()
        # Should gracefully return empty list
        assert plugins == []

    def test_load_plugin_with_dependencies(self, temp_plugin_dir):
        """Test loading plugin metadata with dependencies."""
        pytest.importorskip("yaml")
        import yaml

        # Create metadata file
        metadata = {
            "name": "dependent_plugin",
            "version": "1.0.0",
            "description": "Plugin with dependencies",
            "author": "Test Author",
            "dependencies": [
                {"name": "jmAgent", "version": ">=1.0.0"}
            ]
        }
        metadata_path = temp_plugin_dir / "plugin.yaml"
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f)

        loader = PluginLoader(str(temp_plugin_dir))
        assert loader.plugin_dir == str(temp_plugin_dir)

    def test_plugin_validation_missing_required_attributes(self, temp_plugin_dir):
        """Test validation of plugin with missing attributes."""
        # Create an invalid plugin
        plugin_path = temp_plugin_dir / "invalid_plugin.py"
        plugin_code = """
from src.plugins.base import Plugin

class InvalidPlugin(Plugin):
    # Missing required attributes
    pass
"""
        plugin_path.write_text(plugin_code)

        loader = PluginLoader(str(temp_plugin_dir))
        # Should still discover but mark as invalid
        plugins = loader.discover_plugins()
        # Should not raise


# ============================================================================
# TestPluginIntegration - Integration Tests
# ============================================================================

class TestPluginIntegration:
    """Test plugin system integration."""

    @pytest.mark.asyncio
    async def test_plugin_workflow(self):
        """Test complete plugin workflow."""
        manager = PluginManager()
        plugin = SimplePlugin()

        # Register and enable plugin
        manager.register_plugin(plugin)
        manager.enable_plugin("test_plugin")

        # Execute hook
        results = await manager.execute_hook("before_generate", code="sample")
        assert len(results) == 1

        # Check plugin was executed
        assert plugin.execution_count == 1
        assert plugin.last_hook == "before_generate"

        # Disable plugin
        manager.disable_plugin("test_plugin")

        # Execute hook again
        results = await manager.execute_hook("after_generate")
        # Should still be 1 since plugin is disabled
        assert plugin.execution_count == 1

    @pytest.mark.asyncio
    async def test_multiple_plugin_execution_order(self):
        """Test that multiple plugins execute in order."""
        manager = PluginManager()
        plugins = []
        for i in range(3):
            plugin = HookTrackingPlugin()
            plugin.name = f"plugin_{i}"
            plugins.append(plugin)
            manager.register_plugin(plugin)
            manager.enable_plugin(f"plugin_{i}")

        await manager.execute_hook("before_generate")

        # All plugins should have executed
        for plugin in plugins:
            assert "before_generate" in plugin.hooks_executed

    @pytest.mark.asyncio
    async def test_plugin_result_aggregation(self):
        """Test aggregating results from multiple plugins."""
        manager = PluginManager()
        plugin1 = SimplePlugin()
        plugin2 = HookTrackingPlugin()
        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)
        manager.enable_plugin("test_plugin")
        manager.enable_plugin("hook_tracking_plugin")

        results = await manager.execute_hook("test_hook")
        assert len(results) == 2
        # Results should all be dicts with standard format
        assert all(isinstance(r, dict) for r in results)
        assert all("plugin_name" in r and "status" in r for r in results)
        assert all(r["status"] in ("success", "failed") for r in results)
        # Both plugins should have succeeded
        assert all(r["status"] == "success" for r in results)

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_plugin_failure(self):
        """Test graceful degradation when plugin fails."""
        manager = PluginManager()
        plugin1 = SimplePlugin()
        plugin2 = FailingPlugin()
        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)
        manager.enable_plugin("test_plugin")
        manager.enable_plugin("failing_plugin")

        # Should not raise despite plugin failure
        results = await manager.execute_hook("before_generate")
        # Manager should have handled the error
        assert plugin1.execution_count == 1  # First plugin still executed

    @pytest.mark.asyncio
    async def test_plugin_state_isolation(self):
        """Test that plugins have isolated state."""
        plugin1 = SimplePlugin()
        plugin2 = SimplePlugin()
        plugin2.name = "test_plugin_2"

        plugin1.enable()
        plugin2.enable()

        await plugin1.execute("hook1")
        await plugin2.execute("hook2")

        # States should be isolated
        assert plugin1.last_hook == "hook1"
        assert plugin2.last_hook == "hook2"
        assert plugin1.execution_count == 1
        assert plugin2.execution_count == 1

    def test_plugin_manager_with_plugin_config(self):
        """Test plugin manager handling plugin configuration."""
        config = {"timeout": 30}
        plugin = SimplePlugin(config=config)
        manager = PluginManager()
        manager.register_plugin(plugin)

        retrieved = manager.get_plugin("test_plugin")
        assert retrieved.config == config


# ============================================================================
# TestPluginEdgeCases - Edge Case Tests
# ============================================================================

class TestPluginEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_plugin_execute_before_enable(self):
        """Test executing plugin before enabling."""
        plugin = SimplePlugin()
        result = await plugin.execute("hook")
        # Should return None and not execute
        assert result is None
        assert plugin.execution_count == 0

    @pytest.mark.asyncio
    async def test_plugin_hook_with_special_characters(self):
        """Test plugin hooks with special characters."""
        plugin = SimplePlugin()
        plugin.enable()
        await plugin.execute("before_action:generate:v2")
        assert plugin.last_hook == "before_action:generate:v2"

    @pytest.mark.asyncio
    async def test_plugin_with_large_payload(self):
        """Test plugin with large arguments."""
        plugin = SimplePlugin()
        plugin.enable()
        large_data = "x" * 10000
        await plugin.execute("hook", large_data)
        assert plugin.last_args[0] == large_data

    @pytest.mark.asyncio
    async def test_plugin_concurrent_execution(self):
        """Test plugins handle concurrent hook execution."""
        import asyncio
        plugin = SimplePlugin()
        plugin.enable()

        # Execute multiple hooks concurrently
        tasks = [plugin.execute(f"hook_{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)
        assert len(results) == 5
        assert plugin.execution_count == 5

    def test_duplicate_plugin_registration(self):
        """Test registering plugin with same name."""
        manager = PluginManager()
        plugin1 = SimplePlugin()
        plugin2 = SimplePlugin()

        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)  # Same name

        # Should replace the first one
        retrieved = manager.get_plugin("test_plugin")
        assert retrieved is plugin2

    def test_plugin_metadata_immutability(self):
        """Test that plugin metadata fields are present."""
        plugin = SimplePlugin()
        assert hasattr(plugin, 'name')
        assert hasattr(plugin, 'version')
        assert hasattr(plugin, 'description')
        assert hasattr(plugin, 'author')

    @pytest.mark.asyncio
    async def test_empty_hook_name(self):
        """Test executing with empty hook name."""
        plugin = SimplePlugin()
        plugin.enable()
        await plugin.execute("")
        assert plugin.last_hook == ""

    @pytest.mark.asyncio
    async def test_plugin_execute_none_result(self):
        """Test plugin returning None."""
        class NonePlugin(Plugin):
            name = "none_plugin"
            version = "1.0.0"
            description = "Returns None"
            author = "Test"

            async def execute(self, hook: str, *args, **kwargs):
                return None

        plugin = NonePlugin()
        plugin.enable()
        result = await plugin.execute("hook")
        assert result is None
