"""Template manager for managing and rendering templates."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.logging.logger import StructuredLogger
from src.errors.exceptions import ConfigurationError
from src.templates.loader import Template, TemplateLoader


logger = StructuredLogger(__name__)


# Built-in default templates
BUILTIN_TEMPLATES: Dict[str, Dict[str, str]] = {
    "generate": {
        "name": "Generate",
        "action": "generate",
        "version": "1.0",
        "description": "Default code generation template",
        "system_prompt": (
            "You are an expert code generator. Generate clean, well-documented, "
            "and well-tested code that follows best practices and coding standards."
        ),
        "user_prompt_template": "Generate {{language}} code for: {{prompt}}\n\nContext: {{context}}",
        "required_variables": ["prompt"],
        "optional_variables": ["language", "context"]
    },
    "refactor": {
        "name": "Refactor",
        "action": "refactor",
        "version": "1.0",
        "description": "Default code refactoring template",
        "system_prompt": (
            "You are an expert code refactoring specialist. Improve code quality, "
            "readability, performance, and maintainability while preserving functionality."
        ),
        "user_prompt_template": "Refactor the code according to these requirements: {{requirements}}\n\nFile content:\n{{file_content}}",
        "required_variables": ["requirements"],
        "optional_variables": ["language", "file_content"]
    },
    "test": {
        "name": "Test",
        "action": "test",
        "version": "1.0",
        "description": "Default test generation template",
        "system_prompt": (
            "You are an expert test engineer. Generate comprehensive test cases that cover "
            "normal cases, edge cases, and error conditions. Use the specified testing framework."
        ),
        "user_prompt_template": "Generate {{framework}} tests for the following code:\n\n{{file_content}}\n\nCoverage target: {{coverage}}",
        "required_variables": [],
        "optional_variables": ["file_content", "framework", "coverage"]
    },
    "explain": {
        "name": "Explain",
        "action": "explain",
        "version": "1.0",
        "description": "Default code explanation template",
        "system_prompt": (
            "You are an expert code explainer. Provide clear, detailed explanations "
            "that help developers understand code logic, design patterns, and best practices."
        ),
        "user_prompt_template": "Explain the following {{language}} code in detail:\n\n{{file_content}}",
        "required_variables": [],
        "optional_variables": ["file_content", "language"]
    },
    "fix": {
        "name": "Fix",
        "action": "fix",
        "version": "1.0",
        "description": "Default bug fix template",
        "system_prompt": (
            "You are an expert debugging specialist. Identify and fix bugs, providing clear "
            "explanations of the root cause and the solution."
        ),
        "user_prompt_template": "Fix the following error in the code:\n\nError: {{error}}\n\nCode:\n{{file_content}}\n\nContext: {{context}}",
        "required_variables": ["error"],
        "optional_variables": ["file_content", "context"]
    },
    "chat": {
        "name": "Chat",
        "action": "chat",
        "version": "1.0",
        "description": "Default chat template",
        "system_prompt": (
            "You are a helpful coding assistant. Provide accurate, concise answers to "
            "programming questions and coding challenges."
        ),
        "user_prompt_template": "{{message}}",
        "required_variables": ["message"],
        "optional_variables": ["history"]
    }
}


class TemplateManager:
    """Manages template loading, caching, and rendering."""

    def __init__(self, templates_dir: Optional[str] = None) -> None:
        """Initialize template manager.

        Args:
            templates_dir: Directory containing custom templates. If not provided,
                          uses JMAGENT_TEMPLATES_DIR environment variable or defaults
                          to None (built-in templates only).

        Raises:
            ValueError: If templates_dir is invalid.
        """
        # Determine templates directory
        if templates_dir is None:
            templates_dir = os.getenv("JMAGENT_TEMPLATES_DIR")

        if templates_dir:
            templates_path = Path(templates_dir)
            if not templates_path.exists():
                raise ValueError(f"Templates directory does not exist: {templates_dir}")
            self.loader = TemplateLoader(templates_dir)
        else:
            self.loader = TemplateLoader(str(Path.home()))  # Dummy, will use built-ins

        self.builtin_templates: Dict[str, Template] = self._load_builtin_templates()
        self.custom_templates: Dict[tuple, Template] = {}  # (action, name) -> Template

    def _load_builtin_templates(self) -> Dict[str, Template]:
        """Load built-in templates.

        Returns:
            Dictionary mapping action to builtin Template.
        """
        templates = {}
        for action, template_data in BUILTIN_TEMPLATES.items():
            try:
                template = Template(**template_data)
                templates[action] = template
            except Exception as e:
                logger.error(
                    "Failed to load built-in template",
                    extra={"action": action, "error": str(e)}
                )
        return templates

    def get_template(self, action: str, name: str) -> Optional[Template]:
        """Get template by action and name.

        First checks custom templates, then built-in defaults.

        Args:
            action: Action name (e.g., 'generate', 'refactor').
            name: Template name.

        Returns:
            Template instance or None if not found.
        """
        # Check custom templates cache
        cache_key = (action, name)
        if cache_key in self.custom_templates:
            return self.custom_templates[cache_key]

        # Try to load custom template
        try:
            all_templates = self.loader.load_all_templates()
            for template in all_templates:
                if template.action == action and template.name == name:
                    self.custom_templates[cache_key] = template
                    return template
        except Exception as e:
            logger.debug(
                "Failed to load custom templates",
                extra={"error": str(e)}
            )

        # Fall back to built-in template
        if action in self.builtin_templates:
            builtin = self.builtin_templates[action]
            if builtin.name == name:
                return builtin

        return None

    def get_default_template(self, action: str) -> Optional[Template]:
        """Get default template for action.

        Args:
            action: Action name (e.g., 'generate', 'refactor').

        Returns:
            Template instance or None if action not found.
        """
        # Try to get custom default (first custom template for action)
        try:
            all_templates = self.loader.load_all_templates()
            for template in all_templates:
                if template.action == action:
                    cache_key = (action, template.name)
                    self.custom_templates[cache_key] = template
                    return template
        except Exception as e:
            logger.debug(
                "Failed to load custom templates for default",
                extra={"action": action, "error": str(e)}
            )

        # Fall back to built-in default
        return self.builtin_templates.get(action)

    def list_templates(self, action: Optional[str] = None) -> List[Template]:
        """List available templates.

        Args:
            action: Optional action to filter by.

        Returns:
            List of available templates.
        """
        templates = []

        # Load custom templates
        try:
            custom_templates = self.loader.load_all_templates()
            templates.extend(custom_templates)
        except Exception as e:
            logger.debug(
                "Failed to load custom templates",
                extra={"error": str(e)}
            )

        # Add built-in templates (if not overridden by custom)
        custom_names = {(t.action, t.name) for t in templates}
        for builtin_template in self.builtin_templates.values():
            cache_key = (builtin_template.action, builtin_template.name)
            if cache_key not in custom_names:
                templates.append(builtin_template)

        # Filter by action if specified
        if action:
            templates = [t for t in templates if t.action == action]

        return templates

    def render_template(
        self,
        template: Template,
        variables: Dict[str, Any]
    ) -> str:
        """Render template with variable substitution.

        Args:
            template: Template to render.
            variables: Dictionary of variables for substitution.

        Returns:
            Rendered template string.

        Raises:
            ConfigurationError: If required variables are missing.
        """
        # Validate required variables
        template.validate_variables(variables)

        # Render user prompt template
        rendered = template.user_prompt_template

        # Replace all variables
        for var_name, var_value in variables.items():
            placeholder = "{{" + var_name + "}}"
            rendered = rendered.replace(placeholder, str(var_value))

        # Remove any remaining unsubstituted optional variables
        rendered = re.sub(r'\{\{[^}]+\}\}', '', rendered)

        return rendered

    def render_system_prompt(self, template: Template) -> str:
        """Get rendered system prompt from template.

        Args:
            template: Template to render system prompt from.

        Returns:
            System prompt string.
        """
        return template.system_prompt

    def clear_cache(self) -> None:
        """Clear all caches."""
        self.loader.clear_cache()
        self.custom_templates.clear()
