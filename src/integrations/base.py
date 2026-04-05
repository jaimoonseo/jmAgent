"""Base integration class for all external service integrations."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseIntegration(ABC):
    """
    Abstract base class for all external service integrations.

    Provides a standard interface for integrating jmAgent with external
    services like GitHub, GitLab, Jira, etc.
    """

    @abstractmethod
    async def authenticate(self) -> None:
        """
        Authenticate with the external service.

        Raises:
            AuthenticationError: If authentication fails.
        """
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated with the service.

        Returns:
            bool: True if authenticated, False otherwise.
        """
        pass

    @abstractmethod
    async def get_context(self) -> Dict[str, Any]:
        """
        Get context information from the external service.

        Returns:
            dict: Context data suitable for injection into prompts.

        Raises:
            JmAgentError: If context retrieval fails.
        """
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """
        Get status information about the integration.

        Returns:
            dict: Status information including authentication status.

        Raises:
            JmAgentError: If status check fails.
        """
        pass
