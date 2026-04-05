"""Template loader for loading templates from YAML files."""

import json
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.errors.exceptions import ConfigurationError, JmAgentError


# Valid action types
VALID_ACTIONS = {"generate", "refactor", "test", "explain", "fix", "chat"}


@dataclass
class Template:
    """Data class representing a template."""

    name: str
    action: str
    system_prompt: str
    user_prompt_template: str
    version: str = "1.0"
    description: str = ""
    required_variables: List[str] = field(default_factory=list)
    optional_variables: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate template after initialization."""
        if not self.name:
            raise ConfigurationError("Template name is required")
        if self.action not in VALID_ACTIONS:
            raise ConfigurationError(
                f"Invalid action '{self.action}'. Must be one of: {', '.join(VALID_ACTIONS)}"
            )
        if not self.system_prompt:
            raise ConfigurationError("Template system_prompt is required")
        if not self.user_prompt_template:
            raise ConfigurationError("Template user_prompt_template is required")

    def all_variables(self) -> List[str]:
        """Get all variables (required and optional).

        Returns:
            List of all variable names.
        """
        return list(set(self.required_variables + self.optional_variables))

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary.

        Returns:
            Dictionary representation of template.
        """
        return {
            "name": self.name,
            "action": self.action,
            "version": self.version,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "required_variables": self.required_variables,
            "optional_variables": self.optional_variables
        }

    def to_json(self) -> str:
        """Serialize template to JSON string.

        Returns:
            JSON string representation of template.
        """
        return json.dumps(self.to_dict())

    def validate_variables(self, variables: Dict[str, Any]) -> None:
        """Validate that all required variables are present.

        Args:
            variables: Dictionary of variables to validate.

        Raises:
            ConfigurationError: If required variables are missing.
        """
        for required_var in self.required_variables:
            if required_var not in variables:
                raise ConfigurationError(
                    f"Missing required variable '{required_var}' for template '{self.name}'"
                )


class TemplateLoader:
    """Loads templates from YAML files."""

    def __init__(self, templates_dir: str) -> None:
        """Initialize loader with templates directory.

        Args:
            templates_dir: Path to directory containing template YAML files.

        Raises:
            ValueError: If templates_dir doesn't exist.
        """
        self.templates_dir = Path(templates_dir)
        if not self.templates_dir.exists():
            raise ValueError(f"Templates directory does not exist: {templates_dir}")

        self.cache: Dict[str, Template] = {}

    def load_template(self, template_file: Path) -> Template:
        """Load template from YAML file.

        Args:
            template_file: Path to YAML template file.

        Returns:
            Template instance.

        Raises:
            FileNotFoundError: If template file doesn't exist.
            ConfigurationError: If template is invalid.
            yaml.YAMLError: If YAML parsing fails.
        """
        template_file = Path(template_file)

        # Check cache first
        cache_key = str(template_file)
        if cache_key in self.cache:
            return self.cache[cache_key]

        if not template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_file}")

        try:
            with open(template_file, 'r') as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                raise ConfigurationError(f"Invalid template format in {template_file}")

            # Create Template instance (will validate in __post_init__)
            try:
                template = Template(**data)
            except TypeError as e:
                raise ConfigurationError(f"Invalid template data in {template_file}: {e}")

            # Cache the template
            self.cache[cache_key] = template

            return template

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse YAML template {template_file}: {e}")

    def load_all_templates(self) -> List[Template]:
        """Load all templates from directory.

        Returns:
            List of loaded templates.
        """
        templates = []

        for yaml_file in self.templates_dir.glob("*.yaml"):
            try:
                template = self.load_template(yaml_file)
                templates.append(template)
            except Exception as e:
                # Log and continue with other templates
                # Could use logging here
                pass

        return templates

    def get_templates_by_action(self, action: str) -> List[Template]:
        """Get all templates for a specific action.

        Args:
            action: Action name (e.g., 'generate', 'refactor').

        Returns:
            List of templates for the action.
        """
        all_templates = self.load_all_templates()
        return [t for t in all_templates if t.action == action]

    def clear_cache(self) -> None:
        """Clear template cache."""
        self.cache.clear()
