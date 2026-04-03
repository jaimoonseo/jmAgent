from src.prompts.context_loader import ProjectContext
from typing import Optional

class ContextEnhancer:
    """Enhances prompts with project context and coding patterns."""

    def __init__(self, project_context: Optional[ProjectContext] = None) -> None:
        """Initialize enhancer with optional project context.

        Args:
            project_context: ProjectContext from load_project_context()
        """
        self.context = project_context

    def get_project_context_prefix(self) -> str:
        """Get context prefix to prepend to prompts.

        Returns:
            Formatted context string or empty string if no context
        """
        if not self.context:
            return ""

        return f"""## Project Context
{self.context.to_context_string()}

## Instructions
- Follow the project's existing code structure and style
- Use the same naming conventions as existing code
- Match the indentation and formatting style of the project
- Consider existing dependencies and frameworks
"""

    def _enhance_prompt(self, prompt: str, section: str) -> str:
        """Internal method to enhance prompt with context.

        Args:
            prompt: Original prompt
            section: Section header for the prompt (e.g., "Request", "Refactoring Request")

        Returns:
            Enhanced prompt or original if no context
        """
        prefix = self.get_project_context_prefix()
        if prefix:
            return f"{prefix}\n## {section}\n{prompt}"
        return prompt

    def enhance_generate_prompt(self, prompt: str) -> str:
        """Enhance code generation prompt with context."""
        return self._enhance_prompt(prompt, "Request")

    def enhance_refactor_prompt(self, prompt: str) -> str:
        """Enhance refactoring prompt with context."""
        return self._enhance_prompt(prompt, "Refactoring Request")

    def enhance_test_prompt(self, prompt: str) -> str:
        """Enhance test generation prompt with context."""
        return self._enhance_prompt(prompt, "Test Request")

    def enhance_explain_prompt(self, prompt: str) -> str:
        """Enhance code explanation prompt with context."""
        return self._enhance_prompt(prompt, "Explanation Request")

    def enhance_fix_prompt(self, prompt: str) -> str:
        """Enhance bug fix prompt with context."""
        return self._enhance_prompt(prompt, "Bug Fix Request")
