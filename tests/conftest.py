"""Shared pytest fixtures and configuration."""

import pytest
import os


@pytest.fixture(autouse=True)
def setup_bedrock_auth(monkeypatch):
    """Set up Bedrock authentication for all tests."""
    # Set a dummy Bedrock token to prevent auth errors
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "test-bearer-token-12345")
    monkeypatch.setenv("AWS_BEDROCK_REGION", "us-east-1")


@pytest.fixture
def jwt_secret(monkeypatch):
    """Provide a consistent JWT secret for tests."""
    test_secret = "test-secret-key-for-testing-12345"
    monkeypatch.setenv("JMAGENT_API_JWT_SECRET_KEY", test_secret)
    return test_secret
