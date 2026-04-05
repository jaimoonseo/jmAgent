"""Exception hierarchy for jmAgent."""


class JmAgentError(Exception):
    """Base exception for jmAgent."""

    pass


class BedrockAPIError(JmAgentError):
    """Error from Bedrock API."""

    pass


class RateLimitError(BedrockAPIError):
    """Rate limit exceeded on Bedrock API."""

    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class ModelError(BedrockAPIError):
    """Error related to model operation or availability."""

    pass


class ConfigurationError(JmAgentError):
    """Configuration is invalid or missing."""

    pass


class AuthenticationError(JmAgentError):
    """Authentication failed or credentials are invalid."""

    pass


class PluginError(JmAgentError):
    """Base exception for plugin-related errors."""

    pass


class PluginValidationError(PluginError):
    """Raised when a plugin fails validation checks."""

    pass


class PluginExecutionError(PluginError):
    """Raised when a plugin fails during execution."""

    pass
