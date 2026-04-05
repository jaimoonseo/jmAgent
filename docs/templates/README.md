# Custom Prompt Templates for jmAgent

This directory contains example and documentation for jmAgent's custom prompt template system.

## Overview

Custom templates allow you to override the default system and user prompts for each jmAgent action. This enables:

- **Customization**: Tailor prompts to your specific coding style and preferences
- **Consistency**: Maintain consistent behavior across multiple runs
- **Quality Control**: Fine-tune prompt templates for better output quality
- **Specialization**: Create action-specific templates for different languages or frameworks

## Template Structure

Each template is a YAML file with the following structure:

```yaml
name: "Template Name"                    # Unique name within the action
action: "generate"                       # Action: generate, refactor, test, explain, fix, chat
version: "1.0"                          # Template version
description: "Brief description"         # What this template does

system_prompt: |                        # System prompt for Claude
  You are an expert code generator.
  Generate clean, well-documented code.

user_prompt_template: |                 # User prompt template with variables
  Generate {{language}} code for: {{prompt}}

required_variables:                     # Variables that must be provided
  - prompt

optional_variables:                     # Variables that are optional
  - language
  - context
```

## Template Variables

Variables are used in prompts using `{{variable_name}}` syntax. Available variables depend on the action:

### Generate Action
- `prompt` (required): What code to generate
- `language` (optional): Programming language
- `context` (optional): Additional context

### Refactor Action
- `requirements` (required): Refactoring requirements
- `file_content` (optional): Code to refactor
- `language` (optional): Programming language

### Test Action
- `file_content` (optional): Code to test
- `framework` (optional): Testing framework (pytest, vitest, jest, etc.)
- `coverage` (optional): Target coverage percentage

### Explain Action
- `file_content` (optional): Code to explain
- `language` (optional): Programming language

### Fix Action
- `error` (required): Error message or description
- `file_content` (optional): Code with the bug
- `context` (optional): Additional context about the bug

### Chat Action
- `message` (required): User message
- `history` (optional): Conversation history

## Using Custom Templates

### 1. Set Templates Directory

Create a directory for your custom templates, then either:

**Option A: Environment Variable**
```bash
export JMAGENT_TEMPLATES_DIR=/path/to/templates
```

**Option B: Pass to TemplateManager**
```python
from src.templates.manager import TemplateManager

manager = TemplateManager("/path/to/templates")
```

### 2. Create Template Files

Create YAML files in your templates directory:

```bash
templates/
├── generate_custom.yaml
├── refactor_custom.yaml
└── test_custom.yaml
```

### 3. Load and Use Templates

```python
from src.templates.manager import TemplateManager

manager = TemplateManager("/path/to/templates")

# Get a specific template
template = manager.get_template("generate", "My Custom Generate")

# Get default template for action
default = manager.get_default_template("generate")

# List all templates
all_templates = manager.list_templates()

# Render template with variables
rendered = manager.render_template(template, {
    "prompt": "Create a FastAPI endpoint",
    "language": "Python"
})
```

## Example Templates

This directory includes example templates:

- `generate_example.yaml` - Fast code generation
- `refactor_example.yaml` - Comprehensive refactoring
- `test_example.yaml` - Comprehensive testing
- `explain_example.yaml` - Detailed explanations
- `fix_example.yaml` - Comprehensive bug fixing
- `chat_example.yaml` - Expert chat assistant

Use these as starting points for your custom templates.

## Best Practices

### 1. Clear System Prompts

Write clear, detailed system prompts that set expectations:

```yaml
system_prompt: |
  You are an expert Python developer.
  Focus on:
  - Clean, readable code
  - Type hints for all functions
  - Comprehensive docstrings
  - Unit test coverage
```

### 2. Variable Substitution

Use variables effectively in user prompts:

```yaml
user_prompt_template: |
  Generate {{language}} code for:
  
  {{prompt}}
  
  Additional requirements:
  - Follow {{language}} best practices
  - Include error handling
  - Add comments for complex logic
```

### 3. Required vs Optional Variables

Be clear about required vs optional variables:

```yaml
required_variables:
  - prompt              # User must provide this

optional_variables:
  - language            # Will be substituted if provided
  - context             # Can be left unspecified
```

### 4. Consistent Naming

Use consistent template names across your organization:

- `Fast Generate` - Quick generation with minimal docs
- `Quality Generate` - Comprehensive generation with full docs
- `Refactor Heavy` - Aggressive refactoring
- `Refactor Light` - Conservative refactoring

### 5. Documentation

Include clear descriptions in your templates:

```yaml
description: "Generate TypeScript React components with proper types and JSDoc"
```

## Template Discovery

Custom templates override built-in templates when they have the same action and name.

Priority:
1. Custom templates (from templates directory)
2. Built-in default templates

## Error Handling

### Missing Required Variables

If a required variable is missing during rendering:

```python
from src.errors.exceptions import ConfigurationError

try:
    rendered = manager.render_template(template, {})
except ConfigurationError as e:
    print(f"Error: {e}")  # "Missing required variable 'prompt'"
```

### Invalid Template Files

Templates are validated when loaded:

```python
from src.errors.exceptions import ConfigurationError

try:
    template = manager.get_template("generate", "My Template")
except ConfigurationError as e:
    print(f"Invalid template: {e}")
```

## Performance Considerations

- Templates are cached after loading (no file re-reads on subsequent access)
- Built-in templates are always available (zero I/O)
- Large template directories scale efficiently
- Variable substitution is optimized for performance

## Advanced Usage

### Template Inheritance (via Custom Code)

Extend base templates programmatically:

```python
manager = TemplateManager()
base = manager.get_default_template("generate")

# Create a modified version
custom_prompt = base.system_prompt + "\nAlso include error handling."
```

### Dynamic Template Loading

Load templates on-demand:

```python
templates = manager.loader.load_all_templates()
for template in templates:
    print(f"{template.action}: {template.name}")
```

### Template Auditing

Export templates to JSON for auditing:

```python
template = manager.get_template("generate", "My Template")
json_str = template.to_json()
```

## Troubleshooting

### Template Not Found

Ensure:
1. Template file exists in templates directory
2. File is valid YAML
3. Has correct action and name fields
4. No syntax errors in template

### Variables Not Substituting

Check:
1. Variable names match exactly (case-sensitive)
2. Variables are wrapped in `{{` and `}}`
3. Variable is in required_variables or optional_variables
4. Variable is provided when rendering

### Performance Issues

For large template directories:
1. Clear cache regularly: `manager.clear_cache()`
2. Use environment variable for templates directory
3. Consider template organization by action

## Integration with jmAgent

Templates integrate seamlessly with all jmAgent actions:

```python
from src.agent import JmAgent
from src.templates.manager import TemplateManager

manager = TemplateManager("/path/to/templates")
agent = JmAgent()

# Use custom template for generation
template = manager.get_template("generate", "My Custom")
rendered = manager.render_template(template, {
    "prompt": "FastAPI endpoint",
    "language": "Python"
})

# Pass rendered prompt to agent
response = await agent.generate(prompt=rendered)
```

## Contributing Templates

To contribute templates to jmAgent:

1. Test thoroughly with various inputs
2. Document variables clearly
3. Follow naming conventions
4. Include examples in description
5. Ensure no sensitive information in templates

## See Also

- [jmAgent README](../../README.md)
- [Architecture Overview](../../CLAUDE.md)
- [Configuration Guide](../CONFIG.md)
