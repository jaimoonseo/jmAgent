# Phase 4: Advanced Configuration, Monitoring & Management Features

This document provides a comprehensive overview of Phase 4 features implemented for jmAgent, including configuration management, metrics tracking, audit logging, plugin management, and template customization.

## Overview

Phase 4 introduces enterprise-grade management and monitoring capabilities to jmAgent, enabling users to:
- Manage configuration dynamically via CLI
- Monitor performance metrics and costs
- Track all actions in audit logs
- Extend functionality through plugins
- Customize behavior with templates

All Phase 4 features maintain backward compatibility with Phases 1-3.

## Table of Contents

1. [Configuration Management](#configuration-management)
2. [Metrics & Monitoring](#metrics--monitoring)
3. [Audit Logging](#audit-logging)
4. [Plugin System](#plugin-system)
5. [Template System](#template-system)
6. [CLI Commands Reference](#cli-commands-reference)

---

## Configuration Management

### Overview

The configuration management system allows users to view, modify, and reset settings without editing environment variables.

### Key Features

- **Dynamic Configuration**: Update settings at runtime
- **Type Validation**: Automatic validation of configuration values
- **Environment Variable Support**: Settings read from `JMAGENT_*` prefixed environment variables
- **Safe Defaults**: Reset to sensible defaults at any time
- **Masked Sensitive Values**: Sensitive settings (tokens, keys) are masked in output

### Configuration Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `jm_default_model` | str | haiku | Default LLM model (haiku, sonnet, opus) |
| `jm_temperature` | float | 0.2 | Sampling temperature (0.0-1.0) |
| `jm_max_tokens` | int | 4096 | Maximum output tokens |
| `aws_bedrock_region` | str | us-east-1 | AWS Bedrock region |
| `jm_project_root` | str | None | Project root directory |
| `jm_enable_caching` | bool | True | Enable prompt caching |
| `jm_cache_ttl` | int | 3600 | Cache TTL in seconds |
| `jm_enable_streaming` | bool | False | Enable streaming responses |

### Configuration Commands

```bash
# Show all current configuration
jm config show

# Show specific configuration key
jm config show --key jm_default_model

# Set configuration value
jm config set --key jm_default_model --value sonnet

# Reset all configuration to defaults
jm config reset
```

### Examples

```bash
# Change default model to Sonnet for better quality
jm config set --key jm_default_model --value sonnet

# Enable streaming for faster responses
jm config set --key jm_enable_streaming --value true

# Increase max tokens for longer outputs
jm config set --key jm_max_tokens --value 8192

# Change AWS region
jm config set --key aws_bedrock_region --value eu-west-1
```

---

## Metrics & Monitoring

### Overview

The metrics system tracks performance, usage, and cost data for all jmAgent actions.

### Key Features

- **Action Metrics**: Track response time, tokens used, success rate per action
- **Cost Estimation**: Calculate estimated costs based on token usage
- **Aggregated Statistics**: View statistics across all actions or filter by action type
- **Performance Monitoring**: Identify slow operations and optimization opportunities

### Metrics Collected

For each action, the following metrics are recorded:
- Action type (generate, refactor, test, explain, fix, chat)
- Response time (seconds)
- Input tokens used
- Output tokens used
- Success/failure status
- Error messages (if applicable)
- Timestamp

### Metrics Commands

```bash
# Show overall metrics summary
jm metrics summary

# Show metrics for specific action type
jm metrics summary --action generate

# Show cost breakdown (based on Haiku pricing)
jm metrics cost

# Reset all metrics
jm metrics reset
```

### Examples

```bash
# View performance summary
jm metrics summary

# Output:
# Metrics Summary:
# ============================================================
# 
# GENERATE:
#   Count: 10
#   Success Rate: 100.0%
#   Avg Response Time: 2.45s
#   Min Response Time: 1.92s
#   Max Response Time: 3.18s
#   Total Tokens: 15432
# ============================================================

# Check costs for refactoring operations
jm metrics summary --action refactor

# View cost breakdown
jm metrics cost
```

### Pricing Information

jmAgent estimates costs based on AWS Bedrock pricing (April 2024):

**Haiku 4.5**
- Input: $0.80 per million tokens
- Output: $4.00 per million tokens

**Sonnet 4.6**
- Input: $3.00 per million tokens
- Output: $15.00 per million tokens

**Opus 4.6**
- Input: $15.00 per million tokens
- Output: $75.00 per million tokens

---

## Audit Logging

### Overview

The audit logging system provides comprehensive tracking of all actions for compliance, debugging, and analysis.

### Key Features

- **Complete Audit Trail**: Record all user actions with context
- **Persistent Storage**: Store audit logs in SQLite database
- **Query & Search**: Search logs by action type, user, status, date range
- **Detailed Records**: Include input data, output summary, tokens, errors
- **User Attribution**: Track which user performed each action
- **Status Tracking**: Record success, failure, and partial results

### Audit Record Fields

- **action_type**: Type of action performed (generate, refactor, test, explain, fix, chat)
- **user**: Username performing the action (default: 'anonymous')
- **timestamp**: ISO 8601 timestamp of the action
- **input_data**: Input parameters for the action
- **output_data**: Generated output (if any)
- **status**: Result status (success, failure, partial)
- **error_message**: Error details if applicable
- **duration**: Execution time in seconds
- **tokens_used**: Dictionary with input_tokens and output_tokens
- **metadata**: Additional custom fields

### Audit Commands

```bash
# Show recent audit logs (default: last 10)
jm audit log

# Show last 20 audit logs
jm audit log --limit 20

# Search audit logs by action type
jm audit search --action generate

# Search with multiple filters
jm audit search --action refactor --user alice --status success

# Search by status
jm audit search --status failure
```

### Examples

```bash
# View recent activity
jm audit log --limit 5

# Find all failed operations
jm audit search --status failure

# Check what user 'alice' did
jm audit search --user alice

# Find all generate operations that succeeded
jm audit search --action generate --status success
```

### Database Location

By default, audit logs are stored in `audit.db` in the current working directory. The database includes indexed columns for efficient querying by action type, user, status, and timestamp.

---

## Plugin System

### Overview

The plugin system allows extending jmAgent functionality through custom plugins.

### Key Features

- **Plugin Manager**: Register, enable, disable plugins
- **Plugin Loader**: Load plugins from configuration
- **Hook System**: Plugins can hook into action lifecycle
- **Lifecycle Management**: Plugins have enable/disable states
- **Error Handling**: Graceful failure handling for plugin errors

### Built-in Plugins

jmAgent includes these built-in plugins:
- **github_integration**: GitHub integration for PR/issue operations
- **caching**: Prompt caching for cost reduction
- **monitoring**: Performance monitoring and analytics

### Plugin Commands

```bash
# List all registered plugins
jm plugin list

# List only enabled plugins
jm plugin list --enabled

# Enable a plugin
jm plugin enable --name github_integration

# Disable a plugin
jm plugin disable --name github_integration
```

### Examples

```bash
# View available plugins
jm plugin list

# Enable GitHub integration
jm plugin enable --name github_integration

# Show only active plugins
jm plugin list --enabled
```

### Creating Custom Plugins

Plugins extend the `Plugin` base class:

```python
from src.plugins.base import Plugin

class CustomPlugin(Plugin):
    def __init__(self):
        super().__init__(
            name="custom_plugin",
            version="1.0.0",
            description="My custom plugin"
        )
    
    def on_action_start(self, action_type: str, input_data: dict) -> None:
        """Called when an action starts."""
        pass
    
    def on_action_complete(self, action_type: str, result: dict) -> None:
        """Called when an action completes."""
        pass
```

---

## Template System

### Overview

The template system enables customization of prompts for each action type, allowing users to tailor LLM behavior to their needs.

### Key Features

- **Built-in Templates**: Default templates for all action types
- **Custom Templates**: Create and use custom templates
- **Variable Substitution**: Templates support Jinja2-style variables
- **Action-Specific**: Templates can be customized per action type
- **Easy Switching**: Switch between templates at runtime

### Built-in Templates

jmAgent includes templates for:
- **generate**: Code generation template
- **refactor**: Code refactoring template
- **test**: Test generation template
- **explain**: Code explanation template
- **fix**: Bug fixing template
- **chat**: Interactive chat template

### Template Commands

```bash
# List all available templates
jm template list

# List templates for specific action
jm template list --action generate

# Use a custom template
jm template use --action generate --name custom_gen
```

### Examples

```bash
# View all available templates
jm template list

# View only generation templates
jm template list --action generate

# Use custom generation template
jm template use --action generate --name optimized_gen
```

### Template Variables

Templates support these variables:
- `{{prompt}}` - User prompt for generation
- `{{file_content}}` - Content of file being operated on
- `{{language}}` - Programming language
- `{{requirements}}` - Refactoring requirements
- `{{framework}}` - Testing framework
- `{{error}}` - Error message for debugging
- `{{context}}` - Additional context
- `{{history}}` - Chat history

### Creating Custom Templates

Templates are defined in YAML or JSON format:

```yaml
name: "custom_generate"
action: "generate"
version: "1.0"
description: "Optimized code generation template"
system_prompt: |
  You are an expert code generator focused on performance and maintainability.
  Generate efficient, well-documented code.
user_prompt_template: |
  Generate {{language}} code for: {{prompt}}
  
  Context: {{context}}
required_variables: ["prompt"]
optional_variables: ["language", "context"]
```

---

## CLI Commands Reference

### Summary Table

| Command | Subcommand | Purpose |
|---------|-----------|---------|
| `config` | show | Display configuration settings |
| `config` | set | Update configuration value |
| `config` | reset | Reset to default configuration |
| `metrics` | summary | Show performance metrics summary |
| `metrics` | cost | Show cost breakdown |
| `metrics` | reset | Clear all metrics |
| `audit` | log | Show recent audit logs |
| `audit` | search | Search audit logs with filters |
| `plugin` | list | List available plugins |
| `plugin` | enable | Enable a plugin |
| `plugin` | disable | Disable a plugin |
| `template` | list | List available templates |
| `template` | use | Use a custom template |

### Full Command Examples

```bash
# Configuration
jm config show
jm config show --key jm_temperature
jm config set --key jm_temperature --value 0.5
jm config reset

# Metrics
jm metrics summary
jm metrics summary --action refactor
jm metrics cost
jm metrics reset

# Audit
jm audit log
jm audit log --limit 20
jm audit search --action generate
jm audit search --user alice --status success

# Plugins
jm plugin list
jm plugin list --enabled
jm plugin enable --name github_integration
jm plugin disable --name github_integration

# Templates
jm template list
jm template list --action generate
jm template use --action refactor --name optimized
```

---

## Integration with Phases 1-3

Phase 4 features are fully compatible with Phases 1-3:

- **Phase 1**: Basic code generation, refactoring, testing, explaining, bug fixing
- **Phase 2**: Project context support for better generation
- **Phase 3**: Streaming, caching, multi-file operations, auto-formatting

Phase 4 adds management layers on top without modifying core functionality.

---

## Performance Considerations

- **Metrics Collection**: Minimal overhead, stored in-memory
- **Audit Logging**: Asynchronous I/O to SQLite database
- **Plugin System**: Only enabled plugins are executed
- **Template System**: Templates are cached after first load

---

## Security & Privacy

- **Sensitive Configuration**: Tokens and keys are masked in output
- **Audit Logs**: Stored locally in SQLite, no remote transmission
- **Plugin Isolation**: Plugins run in same process (trust boundary)
- **Configuration Validation**: All values are validated before acceptance

---

## Troubleshooting

### Configuration won't update
Check that the key name is valid and the value matches the expected type.

### Metrics show 0 tokens
Ensure the agent was initialized with the metrics collector integrated.

### Audit logs not appearing
Check that the `audit.db` file exists and has write permissions.

### Plugins not loading
Verify plugin names are correct and plugins are installed.

---

## Future Enhancements

Planned improvements for Phase 4:
- Remote audit log storage (cloud backends)
- Plugin marketplace for community plugins
- Advanced template builder UI
- Performance optimization recommendations
- Cost allocation per user/project
- Integration with monitoring platforms (DataDog, New Relic)

---

## Support

For issues or questions about Phase 4 features:
1. Check the CLI help: `jm <command> --help`
2. Review configuration: `jm config show`
3. Check audit logs: `jm audit log`
4. Enable debug logging in your code

---

## Version Info

- **Phase 4 Released**: April 2026
- **jmAgent Version**: 1.4.0+
- **AWS Bedrock**: Latest Claude 4 series
- **Minimum Python**: 3.10+

