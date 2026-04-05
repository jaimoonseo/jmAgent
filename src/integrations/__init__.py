"""Integration modules for jmAgent.

This package provides integrations with external services like GitHub.
"""

from src.integrations.base import BaseIntegration
from src.integrations.github import GitHubClient, GitHubContext

__all__ = [
    "BaseIntegration",
    "GitHubClient",
    "GitHubContext",
]
