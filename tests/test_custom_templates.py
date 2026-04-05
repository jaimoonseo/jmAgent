"""Comprehensive tests for custom prompt template system."""

import json
import os
import pytest
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any

from src.templates.loader import TemplateLoader
from src.templates.manager import TemplateManager, Template
from src.errors.exceptions import JmAgentError, ConfigurationError


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_templates_dir():
    """Create temporary directory for templates."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_generate_template() -> Dict[str, Any]:
    """Sample generate action template."""
    return {
        "name": "Custom Generate",
        "action": "generate",
        "version": "1.0",
        "description": "Custom code generation template",
        "system_prompt": "You are an expert code generator. Generate clean, well-documented code.",
        "user_prompt_template": "Generate {{language}} code for: {{prompt}}",
        "required_variables": ["prompt"],
        "optional_variables": ["language", "context"]
    }


@pytest.fixture
def sample_refactor_template() -> Dict[str, Any]:
    """Sample refactor action template."""
    return {
        "name": "Custom Refactor",
        "action": "refactor",
        "version": "1.0",
        "description": "Custom refactoring template",
        "system_prompt": "You are a code refactoring expert.",
        "user_prompt_template": "Refactor the code according to: {{requirements}}",
        "required_variables": ["requirements"],
        "optional_variables": ["language"]
    }


@pytest.fixture
def sample_test_template() -> Dict[str, Any]:
    """Sample test action template."""
    return {
        "name": "Custom Test",
        "action": "test",
        "version": "1.0",
        "description": "Custom test generation template",
        "system_prompt": "You are a test expert.",
        "user_prompt_template": "Generate {{framework}} tests for the code.",
        "required_variables": [],
        "optional_variables": ["framework", "coverage"]
    }


@pytest.fixture
def sample_explain_template() -> Dict[str, Any]:
    """Sample explain action template."""
    return {
        "name": "Custom Explain",
        "action": "explain",
        "version": "1.0",
        "description": "Custom explanation template",
        "system_prompt": "You are a code explanation expert.",
        "user_prompt_template": "Explain the code in {{language}}.",
        "required_variables": [],
        "optional_variables": ["language"]
    }


@pytest.fixture
def sample_fix_template() -> Dict[str, Any]:
    """Sample fix action template."""
    return {
        "name": "Custom Fix",
        "action": "fix",
        "version": "1.0",
        "description": "Custom bug fix template",
        "system_prompt": "You are a debugging expert.",
        "user_prompt_template": "Fix the following error: {{error}}",
        "required_variables": ["error"],
        "optional_variables": ["context"]
    }


@pytest.fixture
def sample_chat_template() -> Dict[str, Any]:
    """Sample chat action template."""
    return {
        "name": "Custom Chat",
        "action": "chat",
        "version": "1.0",
        "description": "Custom chat template",
        "system_prompt": "You are a helpful coding assistant.",
        "user_prompt_template": "{{message}}",
        "required_variables": ["message"],
        "optional_variables": ["history"]
    }


@pytest.fixture
def templates_with_files(temp_templates_dir, sample_generate_template, sample_refactor_template):
    """Create templates directory with sample templates."""
    # Create generate template
    generate_file = temp_templates_dir / "generate_custom.yaml"
    with open(generate_file, 'w') as f:
        yaml.dump(sample_generate_template, f)

    # Create refactor template
    refactor_file = temp_templates_dir / "refactor_custom.yaml"
    with open(refactor_file, 'w') as f:
        yaml.dump(sample_refactor_template, f)

    return temp_templates_dir


# ============================================================================
# TemplateLoader Tests
# ============================================================================

class TestTemplateLoaderBasics:
    """Test basic template loading functionality."""

    def test_loader_initialization(self, temp_templates_dir):
        """Test TemplateLoader initialization."""
        loader = TemplateLoader(str(temp_templates_dir))
        assert loader.templates_dir == temp_templates_dir
        assert isinstance(loader.cache, dict)

    def test_load_single_template_file(self, temp_templates_dir, sample_generate_template):
        """Test loading a single template file."""
        # Create template file
        template_file = temp_templates_dir / "generate.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_generate_template, f)

        loader = TemplateLoader(str(temp_templates_dir))
        template = loader.load_template(template_file)

        assert template.name == "Custom Generate"
        assert template.action == "generate"
        assert template.version == "1.0"

    def test_load_template_yaml_format(self, temp_templates_dir, sample_generate_template):
        """Test loading template in YAML format."""
        template_file = temp_templates_dir / "generate.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_generate_template, f)

        loader = TemplateLoader(str(temp_templates_dir))
        template = loader.load_template(template_file)

        assert isinstance(template, Template)
        assert template.system_prompt == sample_generate_template["system_prompt"]

    def test_load_nonexistent_template_file(self, temp_templates_dir):
        """Test loading non-existent template file raises error."""
        loader = TemplateLoader(str(temp_templates_dir))
        nonexistent_file = temp_templates_dir / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            loader.load_template(nonexistent_file)

    def test_load_template_caching(self, temp_templates_dir, sample_generate_template):
        """Test that templates are cached after first load."""
        template_file = temp_templates_dir / "generate.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_generate_template, f)

        loader = TemplateLoader(str(temp_templates_dir))

        # First load
        template1 = loader.load_template(template_file)

        # Modify file
        sample_generate_template["name"] = "Modified Name"
        with open(template_file, 'w') as f:
            yaml.dump(sample_generate_template, f)

        # Second load should return cached version
        template2 = loader.load_template(template_file)
        assert template1.name == template2.name  # Both are "Custom Generate"

    def test_clear_cache(self, temp_templates_dir, sample_generate_template):
        """Test clearing template cache."""
        template_file = temp_templates_dir / "generate.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_generate_template, f)

        loader = TemplateLoader(str(temp_templates_dir))
        loader.load_template(template_file)

        assert len(loader.cache) > 0
        loader.clear_cache()
        assert len(loader.cache) == 0


class TestTemplateLoaderValidation:
    """Test template validation in loader."""

    def test_load_template_invalid_yaml(self, temp_templates_dir):
        """Test loading invalid YAML raises error."""
        template_file = temp_templates_dir / "invalid.yaml"
        with open(template_file, 'w') as f:
            f.write("invalid: yaml: content: [")

        loader = TemplateLoader(str(temp_templates_dir))

        with pytest.raises((yaml.YAMLError, Exception)):
            loader.load_template(template_file)

    def test_load_template_missing_required_field(self, temp_templates_dir):
        """Test loading template missing required field raises error."""
        incomplete_template = {
            "name": "Incomplete",
            # Missing 'action' field
            "system_prompt": "Test prompt"
        }

        template_file = temp_templates_dir / "incomplete.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(incomplete_template, f)

        loader = TemplateLoader(str(temp_templates_dir))

        with pytest.raises((ConfigurationError, KeyError)):
            loader.load_template(template_file)

    def test_load_template_invalid_action(self, temp_templates_dir):
        """Test loading template with invalid action raises error."""
        invalid_template = {
            "name": "Invalid Action",
            "action": "invalid_action",
            "system_prompt": "Test",
            "user_prompt_template": "Test {{prompt}}"
        }

        template_file = temp_templates_dir / "invalid_action.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(invalid_template, f)

        loader = TemplateLoader(str(temp_templates_dir))

        with pytest.raises(ConfigurationError):
            loader.load_template(template_file)


class TestTemplateLoaderDiscovery:
    """Test template discovery and loading from directory."""

    def test_load_all_templates_from_directory(self, templates_with_files):
        """Test loading all templates from directory."""
        loader = TemplateLoader(str(templates_with_files))
        templates = loader.load_all_templates()

        assert len(templates) >= 2
        actions = [t.action for t in templates]
        assert "generate" in actions
        assert "refactor" in actions

    def test_get_templates_by_action(self, templates_with_files):
        """Test getting templates by action."""
        loader = TemplateLoader(str(templates_with_files))
        loader.load_all_templates()

        generate_templates = loader.get_templates_by_action("generate")
        assert len(generate_templates) >= 1
        assert all(t.action == "generate" for t in generate_templates)

    def test_get_templates_by_action_no_match(self, temp_templates_dir, sample_generate_template):
        """Test getting templates by action with no matches."""
        template_file = temp_templates_dir / "generate.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_generate_template, f)

        loader = TemplateLoader(str(temp_templates_dir))
        loader.load_all_templates()

        fix_templates = loader.get_templates_by_action("fix")
        assert len(fix_templates) == 0

    def test_empty_templates_directory(self, temp_templates_dir):
        """Test loading from empty templates directory."""
        loader = TemplateLoader(str(temp_templates_dir))
        templates = loader.load_all_templates()

        assert templates == []


# ============================================================================
# Template Data Class Tests
# ============================================================================

class TestTemplateClass:
    """Test Template data class."""

    def test_template_initialization(self, sample_generate_template):
        """Test Template initialization."""
        template = Template(**sample_generate_template)

        assert template.name == sample_generate_template["name"]
        assert template.action == sample_generate_template["action"]
        assert template.version == sample_generate_template["version"]

    def test_template_required_variables(self, sample_generate_template):
        """Test accessing required variables."""
        template = Template(**sample_generate_template)

        assert "prompt" in template.required_variables
        assert len(template.required_variables) == 1

    def test_template_optional_variables(self, sample_generate_template):
        """Test accessing optional variables."""
        template = Template(**sample_generate_template)

        assert "language" in template.optional_variables
        assert "context" in template.optional_variables

    def test_template_all_variables(self, sample_generate_template):
        """Test getting all variables (required + optional)."""
        template = Template(**sample_generate_template)
        all_vars = template.all_variables()

        assert "prompt" in all_vars
        assert "language" in all_vars
        assert "context" in all_vars
        assert len(all_vars) == 3

    def test_template_to_dict(self, sample_generate_template):
        """Test converting template to dictionary."""
        template = Template(**sample_generate_template)
        template_dict = template.to_dict()

        assert isinstance(template_dict, dict)
        assert template_dict["name"] == sample_generate_template["name"]
        assert template_dict["action"] == sample_generate_template["action"]

    def test_template_to_json(self, sample_generate_template):
        """Test serializing template to JSON."""
        template = Template(**sample_generate_template)
        json_str = template.to_json()

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["name"] == sample_generate_template["name"]

    def test_template_validate_variables_success(self, sample_generate_template):
        """Test variable validation with all required variables."""
        template = Template(**sample_generate_template)
        variables = {"prompt": "Create a function"}

        # Should not raise
        template.validate_variables(variables)

    def test_template_validate_variables_missing_required(self, sample_generate_template):
        """Test validation fails with missing required variable."""
        template = Template(**sample_generate_template)
        variables = {}  # Missing 'prompt'

        with pytest.raises(ConfigurationError):
            template.validate_variables(variables)

    def test_template_validate_variables_extra_allowed(self, sample_generate_template):
        """Test validation allows extra variables."""
        template = Template(**sample_generate_template)
        variables = {
            "prompt": "Create a function",
            "language": "Python",
            "context": "For a web app",
            "extra": "Extra variable"
        }

        # Should not raise - extra variables are allowed
        template.validate_variables(variables)


# ============================================================================
# TemplateManager Tests
# ============================================================================

class TestTemplateManagerBasics:
    """Test basic TemplateManager functionality."""

    def test_template_manager_initialization(self, temp_templates_dir):
        """Test TemplateManager initialization."""
        manager = TemplateManager(str(temp_templates_dir))

        assert manager.loader is not None
        assert isinstance(manager.loader, TemplateLoader)

    def test_template_manager_with_env_var(self, monkeypatch, temp_templates_dir):
        """Test TemplateManager uses JMAGENT_TEMPLATES_DIR environment variable."""
        monkeypatch.setenv("JMAGENT_TEMPLATES_DIR", str(temp_templates_dir))

        manager = TemplateManager()

        assert str(temp_templates_dir) in str(manager.loader.templates_dir)

    def test_get_template_by_action_and_name(self, templates_with_files):
        """Test getting template by action and name."""
        manager = TemplateManager(str(templates_with_files))
        template = manager.get_template("generate", "Custom Generate")

        assert template is not None
        assert template.name == "Custom Generate"
        assert template.action == "generate"

    def test_get_template_not_found(self, templates_with_files):
        """Test getting non-existent template returns None."""
        manager = TemplateManager(str(templates_with_files))
        template = manager.get_template("generate", "Nonexistent")

        assert template is None

    def test_get_default_template_for_action(self, templates_with_files):
        """Test getting default template for action."""
        manager = TemplateManager(str(templates_with_files))
        template = manager.get_default_template("generate")

        # Should return first available template for action or built-in default
        assert template is not None

    def test_list_available_templates(self, templates_with_files):
        """Test listing available templates."""
        manager = TemplateManager(str(templates_with_files))
        templates = manager.list_templates()

        assert isinstance(templates, list)
        assert len(templates) >= 2

    def test_list_templates_by_action(self, templates_with_files):
        """Test listing templates by action."""
        manager = TemplateManager(str(templates_with_files))
        generate_templates = manager.list_templates(action="generate")

        assert all(t.action == "generate" for t in generate_templates)

    def test_list_templates_empty_directory(self, temp_templates_dir):
        """Test listing templates from empty directory."""
        manager = TemplateManager(str(temp_templates_dir))
        templates = manager.list_templates()

        # Should have at least built-in defaults
        assert isinstance(templates, list)


class TestTemplateManagerBuiltInDefaults:
    """Test built-in default templates."""

    def test_has_builtin_templates_for_all_actions(self):
        """Test that built-in templates exist for all actions."""
        manager = TemplateManager()

        actions = ["generate", "refactor", "test", "explain", "fix", "chat"]
        for action in actions:
            template = manager.get_default_template(action)
            assert template is not None, f"No default template for {action}"
            assert template.action == action

    def test_builtin_template_has_valid_structure(self):
        """Test that built-in templates have valid structure."""
        manager = TemplateManager()
        template = manager.get_default_template("generate")

        assert template.name is not None
        assert template.system_prompt is not None
        assert template.user_prompt_template is not None
        assert isinstance(template.required_variables, list)
        assert isinstance(template.optional_variables, list)


class TestTemplateManagerVariableSubstitution:
    """Test variable substitution in templates."""

    def test_render_template_basic(self, temp_templates_dir, sample_generate_template):
        """Test rendering template with variable substitution."""
        template_file = temp_templates_dir / "generate.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_generate_template, f)

        manager = TemplateManager(str(temp_templates_dir))
        template = manager.get_template("generate", "Custom Generate")

        variables = {
            "prompt": "Create a FastAPI endpoint",
            "language": "Python"
        }

        rendered = manager.render_template(template, variables)

        assert "FastAPI endpoint" in rendered
        assert "Python" in rendered

    def test_render_template_with_all_variables(self, temp_templates_dir, sample_generate_template):
        """Test rendering with both required and optional variables."""
        template_file = temp_templates_dir / "generate.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_generate_template, f)

        manager = TemplateManager(str(temp_templates_dir))
        template = manager.get_template("generate", "Custom Generate")

        variables = {
            "prompt": "FastAPI endpoint",
            "language": "Python",
            "context": "for a REST API"
        }

        rendered = manager.render_template(template, variables)

        assert "{{" not in rendered  # All variables should be substituted
        assert "FastAPI endpoint" in rendered

    def test_render_template_missing_optional_variable(self, temp_templates_dir, sample_generate_template):
        """Test rendering with missing optional variable leaves placeholder."""
        sample_generate_template["user_prompt_template"] = "Generate {{language}} code for: {{prompt}}"

        template_file = temp_templates_dir / "generate.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_generate_template, f)

        manager = TemplateManager(str(temp_templates_dir))
        template = manager.get_template("generate", "Custom Generate")

        variables = {"prompt": "Create function"}  # Missing language

        rendered = manager.render_template(template, variables)

        # Optional variable can be left unsubstituted or empty
        assert "Create function" in rendered

    def test_render_template_missing_required_variable_raises_error(self, temp_templates_dir, sample_generate_template):
        """Test rendering without required variable raises error."""
        template_file = temp_templates_dir / "generate.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_generate_template, f)

        manager = TemplateManager(str(temp_templates_dir))
        template = manager.get_template("generate", "Custom Generate")

        variables = {}  # Missing required 'prompt'

        with pytest.raises(ConfigurationError):
            manager.render_template(template, variables)


class TestTemplateManagerCaching:
    """Test template caching in manager."""

    def test_templates_cached_after_load(self, templates_with_files):
        """Test templates are cached after loading."""
        manager = TemplateManager(str(templates_with_files))

        # First access
        template1 = manager.get_template("generate", "Custom Generate")

        # Second access should use cache
        template2 = manager.get_template("generate", "Custom Generate")

        # Both should be the same object (cached)
        assert template1 is template2

    def test_clear_template_cache(self, templates_with_files):
        """Test clearing template cache."""
        manager = TemplateManager(str(templates_with_files))

        manager.get_template("generate", "Custom Generate")
        manager.clear_cache()

        # Cache should be empty
        template = manager.get_template("generate", "Custom Generate")
        # After clearing, it should still load (from loader cache)
        assert template is not None


# ============================================================================
# Integration Tests
# ============================================================================

class TestTemplateSystemIntegration:
    """Integration tests for complete template system."""

    def test_end_to_end_custom_template_loading(self, temp_templates_dir):
        """Test complete workflow: create, load, and use custom template."""
        # Create custom template
        custom_template = {
            "name": "My Generate",
            "action": "generate",
            "version": "1.0",
            "description": "My custom generator",
            "system_prompt": "Generate high-quality code following best practices.",
            "user_prompt_template": "Generate {{language}} code: {{prompt}}",
            "required_variables": ["prompt"],
            "optional_variables": ["language"]
        }

        template_file = temp_templates_dir / "my_generate.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(custom_template, f)

        # Load and use
        manager = TemplateManager(str(temp_templates_dir))
        template = manager.get_template("generate", "My Generate")

        assert template is not None

        # Render with variables
        rendered = manager.render_template(template, {
            "prompt": "Parse JSON",
            "language": "TypeScript"
        })

        assert "Parse JSON" in rendered
        assert "TypeScript" in rendered

    def test_multiple_templates_for_same_action(self, temp_templates_dir):
        """Test managing multiple templates for the same action."""
        # Create multiple generate templates
        template1 = {
            "name": "Fast Generator",
            "action": "generate",
            "version": "1.0",
            "description": "Fast code generation",
            "system_prompt": "Generate code quickly.",
            "user_prompt_template": "{{prompt}}",
            "required_variables": ["prompt"],
            "optional_variables": []
        }

        template2 = {
            "name": "Quality Generator",
            "action": "generate",
            "version": "1.0",
            "description": "High-quality code generation",
            "system_prompt": "Generate high-quality code with extensive documentation.",
            "user_prompt_template": "Generate: {{prompt}}",
            "required_variables": ["prompt"],
            "optional_variables": []
        }

        with open(temp_templates_dir / "fast.yaml", 'w') as f:
            yaml.dump(template1, f)
        with open(temp_templates_dir / "quality.yaml", 'w') as f:
            yaml.dump(template2, f)

        manager = TemplateManager(str(temp_templates_dir))

        # Both should be available
        fast = manager.get_template("generate", "Fast Generator")
        quality = manager.get_template("generate", "Quality Generator")

        assert fast is not None
        assert quality is not None
        assert fast.name != quality.name

    def test_override_builtin_template(self, temp_templates_dir):
        """Test custom template overrides built-in template."""
        # Create custom generate template with same name as built-in
        custom_template = {
            "name": "Generate",  # Built-in name
            "action": "generate",
            "version": "2.0",
            "description": "Custom override of built-in",
            "system_prompt": "CUSTOM system prompt",
            "user_prompt_template": "CUSTOM: {{prompt}}",
            "required_variables": ["prompt"],
            "optional_variables": []
        }

        with open(temp_templates_dir / "custom_generate.yaml", 'w') as f:
            yaml.dump(custom_template, f)

        manager = TemplateManager(str(temp_templates_dir))
        template = manager.get_template("generate", "Generate")

        # Custom should be found
        assert template is not None

    def test_all_action_types_supported(self, temp_templates_dir):
        """Test that all action types can have custom templates."""
        actions = ["generate", "refactor", "test", "explain", "fix", "chat"]

        for action in actions:
            template_data = {
                "name": f"{action.title()} Custom",
                "action": action,
                "version": "1.0",
                "description": f"Custom {action} template",
                "system_prompt": f"You are a {action} expert.",
                "user_prompt_template": f"{{{{request}}}}",
                "required_variables": ["request"],
                "optional_variables": []
            }

            with open(temp_templates_dir / f"{action}.yaml", 'w') as f:
                yaml.dump(template_data, f)

        manager = TemplateManager(str(temp_templates_dir))

        for action in actions:
            template = manager.get_template(action, f"{action.title()} Custom")
            assert template is not None
            assert template.action == action


class TestTemplateErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_template_directory_raises_error(self):
        """Test that invalid template directory path raises error."""
        with pytest.raises((FileNotFoundError, ValueError)):
            TemplateManager("/nonexistent/path/to/templates")

    def test_template_with_syntax_errors(self, temp_templates_dir):
        """Test handling of template with invalid syntax."""
        invalid_template = {
            "name": "Invalid",
            "action": "generate",
            "system_prompt": "Test",
            "user_prompt_template": "{{unclosed_variable",  # Unclosed variable
            "required_variables": ["unclosed_variable"]
        }

        template_file = temp_templates_dir / "invalid.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(invalid_template, f)

        loader = TemplateLoader(str(temp_templates_dir))
        # Should load without error, validation happens at render time
        template = loader.load_template(template_file)
        assert template is not None


class TestTemplatePerformance:
    """Test template system performance."""

    def test_large_number_of_templates(self, temp_templates_dir):
        """Test manager handles large number of templates."""
        # Create 50 templates
        for i in range(50):
            template = {
                "name": f"Template {i}",
                "action": "generate",
                "version": "1.0",
                "description": f"Template {i}",
                "system_prompt": f"System {i}",
                "user_prompt_template": f"User {{{{prompt}}}}",
                "required_variables": ["prompt"],
                "optional_variables": []
            }

            with open(temp_templates_dir / f"template_{i}.yaml", 'w') as f:
                yaml.dump(template, f)

        manager = TemplateManager(str(temp_templates_dir))

        # Should efficiently handle many templates
        all_templates = manager.list_templates()
        assert len(all_templates) >= 50

    def test_template_rendering_performance(self, temp_templates_dir):
        """Test template rendering with many variables."""
        template_data = {
            "name": "Complex",
            "action": "generate",
            "version": "1.0",
            "description": "Complex template",
            "system_prompt": "System prompt",
            "user_prompt_template": " ".join([f"{{{{var{i}}}}}" for i in range(20)]),
            "required_variables": [f"var{i}" for i in range(20)],
            "optional_variables": []
        }

        with open(temp_templates_dir / "complex.yaml", 'w') as f:
            yaml.dump(template_data, f)

        manager = TemplateManager(str(temp_templates_dir))
        template = manager.get_template("generate", "Complex")

        variables = {f"var{i}": f"value{i}" for i in range(20)}

        # Should render efficiently
        rendered = manager.render_template(template, variables)
        assert rendered is not None
