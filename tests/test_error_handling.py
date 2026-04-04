"""Tests for custom exception hierarchy."""

import pytest
from src.errors.exceptions import (
    JmAgentError,
    BedrockAPIError,
    ConfigurationError,
    RateLimitError,
    ModelError,
    AuthenticationError,
)


def test_jmagent_error_base():
    """Test base JmAgentError exception."""
    err = JmAgentError("Test error")
    assert str(err) == "Test error"
    assert isinstance(err, Exception)


def test_bedrock_api_error():
    """Test BedrockAPIError is subclass of JmAgentError."""
    err = BedrockAPIError("API failed")
    assert isinstance(err, JmAgentError)
    assert str(err) == "API failed"


def test_rate_limit_error():
    """Test RateLimitError with retry_after."""
    err = RateLimitError("Too many requests", retry_after=60)
    assert err.retry_after == 60
    assert isinstance(err, BedrockAPIError)


def test_rate_limit_error_default_retry_after():
    """Test RateLimitError with default retry_after."""
    err = RateLimitError("Too many requests")
    assert err.retry_after == 60


def test_model_error():
    """Test ModelError exception."""
    err = ModelError("Model not found")
    assert isinstance(err, BedrockAPIError)


def test_configuration_error():
    """Test ConfigurationError exception."""
    err = ConfigurationError("Invalid config")
    assert isinstance(err, JmAgentError)


def test_authentication_error():
    """Test AuthenticationError exception."""
    err = AuthenticationError("Auth failed")
    assert isinstance(err, JmAgentError)


def test_exception_message_preserved():
    """Test that exception messages are preserved."""
    message = "Detailed error message with context"
    err = JmAgentError(message)
    assert message in str(err)


def test_exception_inheritance_hierarchy():
    """Test full exception inheritance hierarchy."""
    # Create different exception types
    base_err = JmAgentError("base")
    api_err = BedrockAPIError("api")
    rate_err = RateLimitError("rate")
    model_err = ModelError("model")
    config_err = ConfigurationError("config")
    auth_err = AuthenticationError("auth")

    # All should be JmAgentError instances
    assert isinstance(base_err, JmAgentError)
    assert isinstance(api_err, JmAgentError)
    assert isinstance(rate_err, JmAgentError)
    assert isinstance(model_err, JmAgentError)
    assert isinstance(config_err, JmAgentError)
    assert isinstance(auth_err, JmAgentError)

    # API-related should be BedrockAPIError
    assert isinstance(api_err, BedrockAPIError)
    assert isinstance(rate_err, BedrockAPIError)
    assert isinstance(model_err, BedrockAPIError)

    # Config and Auth should NOT be BedrockAPIError
    assert not isinstance(config_err, BedrockAPIError)
    assert not isinstance(auth_err, BedrockAPIError)
