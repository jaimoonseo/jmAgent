# jmAgent Plugin Architecture

## Overview

The jmAgent plugin system provides an extensible architecture for customizing and extending jmAgent functionality without modifying core code. Plugins can hook into various action lifecycle events, implement custom logic, and integrate seamlessly with jmAgent's async execution model.

## Key Features

- **Extensible Base Class**: Abstract `Plugin` class with lifecycle methods
- **Plugin Manager**: Centralized plugin registration, enable/disable, and lifecycle management
- **Plugin Loader**: Automatic plugin discovery and loading from directories
- **Hook System**: Pre/post-action hooks and error handlers
- **Graceful Degradation**: Plugin failures don't crash jmAgent
- **Configuration Support**: Per-plugin configuration dictionaries
- **Async Execution**: Full async/await support for non-blocking operations

## Quick Start

### 1. Create a Plugin

Create a new Python file in your plugins directory:

```python
# plugins/my_plugin.py
from src.plugins.base import Plugin
from typing import Any, Optional, Dict

class MyPlugin(Plugin):
    """Custom plugin that logs actions."""
    
    name = "my_plugin"
    version = "1.0.0"
    description = "Logs all jmAgent actions"
    author = "Your Name"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.action_count = 0
    
    async def execute(self, hook: str, *args, **kwargs) -> Any:
        """Hook into jmAgent actions."""
        if hook.startswith("before_"):
            self.action_count += 1
            print(f"Action #{self.action_count}: {hook}")
        
        return {"action": hook, "count": self.action_count}
```

### 2. Register and Enable Plugin

```python
from src.plugins.manager import PluginManager
from plugins.my_plugin import MyPlugin

# Create manager
manager = PluginManager()

# Register plugin
plugin = MyPlugin()
manager.register_plugin(plugin)

# Enable plugin
manager.enable_plugin("my_plugin")

# Execute hooks
results = await manager.execute_hook("before_generate", code="...")
```

### 3. Load Plugins from Directory

```python
from src.plugins.loader import PluginLoader
from src.plugins.manager import PluginManager

# Create loader
loader = PluginLoader("/path/to/plugins")

# Discover plugins
plugin_classes = loader.discover_plugins()

# Load and register
manager = PluginManager()
for plugin_class in plugin_classes:
    plugin = plugin_class()
    manager.register_plugin(plugin)
    manager.enable_plugin(plugin.name)
```

## Plugin Development Guide

### Plugin Anatomy

Every plugin must inherit from `Plugin` and implement:

#### Required Class Attributes

```python
class MyPlugin(Plugin):
    name: str = "my_plugin"              # Unique plugin identifier
    version: str = "1.0.0"               # Semantic version
    description: str = "..."             # Human-readable description
    author: str = "Your Name"            # Plugin author
```

#### Required Methods

```python
async def execute(self, hook: str, *args, **kwargs) -> Any:
    """Called when hook is triggered.
    
    Args:
        hook: Hook name (e.g., 'before_generate', 'after_refactor')
        *args: Positional arguments from caller
        **kwargs: Keyword arguments from caller
    
    Returns:
        Plugin-specific result. Can be any type.
    
    Raises:
        Exception: Plugins may raise exceptions.
                   PluginManager handles gracefully.
    """
    pass
```

#### Optional Methods

```python
# Called when plugin is enabled
async def on_enable(self) -> None:
    """Initialize plugin resources."""
    pass

# Called when plugin is disabled
async def on_disable(self) -> None:
    """Clean up plugin resources."""
    pass
```

### Configuration

Plugins can accept configuration during initialization:

```python
# Define plugin
class ConfigurablePlugin(Plugin):
    name = "configurable"
    version = "1.0.0"
    description = "Plugin with configuration"
    author = "Test"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # Access config
        self.timeout = (config or {}).get("timeout", 30)
        self.retries = (config or {}).get("retries", 3)

# Create with config
config = {"timeout": 60, "retries": 5}
plugin = ConfigurablePlugin(config=config)
```

### Plugin Metadata

Access plugin metadata:

```python
plugin = MyPlugin()
metadata = plugin.get_metadata()
# Returns: {
#   "name": "my_plugin",
#   "version": "1.0.0",
#   "description": "...",
#   "author": "..."
# }
```

## Available Hooks

### Action Hooks

Plugins can hook into jmAgent action lifecycle events:

- `before_generate` - Called before code generation
- `after_generate` - Called after code generation
- `before_refactor` - Called before code refactoring
- `after_refactor` - Called after code refactoring
- `before_test` - Called before test generation
- `after_test` - Called after test generation
- `before_explain` - Called before code explanation
- `after_explain` - Called after code explanation
- `before_fix` - Called before bug fixing
- `after_fix` - Called after bug fixing
- `before_chat` - Called before chat interaction
- `after_chat` - Called after chat interaction

### Error Hooks

- `on_error` - Called when an action fails

## Plugin Manager API

### Core Methods

```python
manager = PluginManager()

# Register plugin
manager.register_plugin(plugin)

# Unregister plugin
manager.unregister_plugin("plugin_name")

# Get plugin by name
plugin = manager.get_plugin("plugin_name")  # Returns None if not found

# List all registered plugins
plugins = manager.list_plugins()  # Returns Dict[str, Plugin]

# Get plugin count
count = manager.get_plugin_count()

# Enable/disable plugins
manager.enable_plugin("plugin_name")
manager.disable_plugin("plugin_name")

# Execute hook on all enabled plugins
results = await manager.execute_hook("hook_name", arg1=value1)

# Get enabled/disabled plugins
enabled = manager.get_enabled_plugins()
disabled = manager.get_disabled_plugins()
```

## Plugin Loader API

```python
loader = PluginLoader("/path/to/plugins")

# Discover all plugins in directory
plugin_classes = loader.discover_plugins()

# Load specific plugin by class name
plugin = loader.load_plugin("MyPlugin", config={"timeout": 30})
```

## Error Handling

Plugins can raise exceptions without crashing jmAgent. The PluginManager catches exceptions and:

1. Logs the error with context
2. Returns error details in results
3. Continues executing remaining plugins

```python
# Plugin raises exception
class FailingPlugin(Plugin):
    name = "failing"
    version = "1.0.0"
    description = "..."
    author = "Test"
    
    async def execute(self, hook: str, *args, **kwargs) -> Any:
        raise ValueError("Something went wrong")

# Manager handles gracefully
manager = PluginManager()
manager.register_plugin(FailingPlugin())
manager.enable_plugin("failing")

results = await manager.execute_hook("before_generate")
# Results includes: {
#   "plugin": "failing",
#   "hook": "before_generate",
#   "error": "Something went wrong",
#   "status": "failed"
# }
```

## Best Practices

1. **Keep Plugins Lightweight**: Minimize overhead in execute() method
2. **Use Configuration**: Make plugins configurable for flexibility
3. **Handle Errors Gracefully**: Don't assume successful execution
4. **Log Important Events**: Use StructuredLogger for observability
5. **Version Properly**: Use semantic versioning (MAJOR.MINOR.PATCH)
6. **Document Hooks**: Document which hooks your plugin uses
7. **Test Thoroughly**: Test with and without plugin enabled
8. **Avoid State Sharing**: Keep plugin state isolated

## Example Plugins

### Plugin 1: Logging Plugin

```python
# logs_plugin.py
from src.plugins.base import Plugin
from src.logging.logger import StructuredLogger
from typing import Any, Optional, Dict

class LoggingPlugin(Plugin):
    """Logs all jmAgent actions."""
    
    name = "logging_plugin"
    version = "1.0.0"
    description = "Logs all actions to structured logger"
    author = "jmAgent Team"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger = StructuredLogger("plugin.logging")
        self.action_count = 0
    
    async def execute(self, hook: str, *args, **kwargs) -> Any:
        self.action_count += 1
        self.logger.info(
            f"Plugin hook executed: {hook}",
            extra={
                "plugin": "logging_plugin",
                "hook": hook,
                "count": self.action_count,
                "args_count": len(args),
                "kwargs_count": len(kwargs)
            }
        )
        return {"logged": True, "count": self.action_count}
```

### Plugin 2: Rate Limiting Plugin

```python
# rate_limit_plugin.py
from src.plugins.base import Plugin
from typing import Any, Optional, Dict
import time

class RateLimitPlugin(Plugin):
    """Enforces rate limiting on actions."""
    
    name = "rate_limit_plugin"
    version = "1.0.0"
    description = "Rate limits rapid-fire actions"
    author = "jmAgent Team"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.min_interval = (config or {}).get("min_interval", 1.0)
        self.last_action_time = 0
    
    async def execute(self, hook: str, *args, **kwargs) -> Any:
        current_time = time.time()
        elapsed = current_time - self.last_action_time
        
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            return {
                "rate_limited": True,
                "wait_time": wait_time,
                "message": f"Rate limited. Please wait {wait_time:.2f}s"
            }
        
        self.last_action_time = current_time
        return {"rate_limited": False}
```

### Plugin 3: Metrics Plugin

```python
# metrics_plugin.py
from src.plugins.base import Plugin
from typing import Any, Optional, Dict

class MetricsPlugin(Plugin):
    """Collects metrics about jmAgent actions."""
    
    name = "metrics_plugin"
    version = "1.0.0"
    description = "Collects metrics on all actions"
    author = "jmAgent Team"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.metrics = {}
    
    async def execute(self, hook: str, *args, **kwargs) -> Any:
        hook_type = hook.split("_")[0]  # "before" or "after"
        action = "_".join(hook.split("_")[1:])  # e.g., "generate"
        
        key = f"{action}_{hook_type}"
        self.metrics[key] = self.metrics.get(key, 0) + 1
        
        return {"metric": key, "count": self.metrics[key]}
    
    def get_metrics(self) -> Dict[str, int]:
        return dict(self.metrics)
```

## Integration with jmAgent

To integrate plugins with the jmAgent agent class:

```python
from src.agent import JmAgent
from src.plugins.manager import PluginManager

# Create agent and plugin manager
agent = JmAgent()
plugin_manager = PluginManager()

# Load and register plugins
# ... (register plugins) ...

# Execute hooks during agent operations
results = await plugin_manager.execute_hook("before_generate", prompt=prompt)
response = await agent.generate(prompt)
results = await plugin_manager.execute_hook("after_generate", response=response)
```

## Troubleshooting

### Plugin Not Found

```
JmAgentError: Plugin not found: my_plugin
```

**Solution**: Ensure plugin is registered with manager before accessing.

### Plugin Execution Failed

Check logs for detailed error information:

```python
# Enable debug logging to see plugin errors
from src.logging.logger import StructuredLogger
logger = StructuredLogger("jmagent", level="DEBUG")
```

### Plugin State Not Isolated

Ensure each plugin instance maintains its own state:

```python
# Bad: Shared state
class BadPlugin(Plugin):
    shared_list = []  # Shared across instances!
    
# Good: Instance state
class GoodPlugin(Plugin):
    def __init__(self, config=None):
        super().__init__(config)
        self.instance_list = []  # Per-instance state
```

## Testing Plugins

```python
import pytest
from src.plugins.manager import PluginManager
from my_plugin import MyPlugin

@pytest.mark.asyncio
async def test_my_plugin():
    manager = PluginManager()
    plugin = MyPlugin()
    manager.register_plugin(plugin)
    manager.enable_plugin("my_plugin")
    
    results = await manager.execute_hook("before_generate")
    assert len(results) == 1
    assert results[0]["status"] == "success"
```

## Performance Considerations

- **Async Operations**: Use async/await for I/O operations
- **Caching**: Cache expensive computations
- **Early Return**: Return early when hook not relevant
- **Minimal Processing**: Keep execute() method lean

```python
class EfficientPlugin(Plugin):
    name = "efficient"
    version = "1.0.0"
    description = "..."
    author = "Test"
    
    def __init__(self, config=None):
        super().__init__(config)
        self.cache = {}
    
    async def execute(self, hook: str, *args, **kwargs) -> Any:
        # Early return for irrelevant hooks
        if not hook.startswith("before_"):
            return None
        
        # Use cache
        if hook in self.cache:
            return self.cache[hook]
        
        # Expensive operation
        result = await self.expensive_operation()
        self.cache[hook] = result
        return result
```

## See Also

- [Plugin API Reference](./API.md) - Detailed API documentation
- [Plugin Examples](./examples/) - Example plugins
- [Testing Plugins](./TESTING.md) - Plugin testing guide
