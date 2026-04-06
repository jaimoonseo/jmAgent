"""Shared pytest fixtures and configuration."""

import pytest
import os
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock


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


def create_mock_bedrock_response(text: str = "def hello(): pass", input_tokens: int = 50, output_tokens: int = 30) -> dict:
    """Create a mock Bedrock API response."""
    response_body = {
        "content": [
            {
                "type": "text",
                "text": text
            }
        ],
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }
    }

    # Create a mock response object that mimics boto3 response structure
    mock_response = {
        "body": MagicMock(),
        "ResponseMetadata": {
            "HTTPStatusCode": 200,
            "HTTPHeaders": {},
            "RetryAttempts": 0
        }
    }

    # Make the body.read() method return the JSON-encoded response
    mock_response["body"].read.return_value = json.dumps(response_body).encode("utf-8")

    return mock_response


@pytest.fixture
def mock_bedrock_runtime():
    """Create a mock Bedrock runtime client that intercepts invoke_model calls."""
    mock_client = MagicMock()
    mock_client.invoke_model.return_value = create_mock_bedrock_response(
        text="def hello(): pass\n    return 'Hello World'",
        input_tokens=50,
        output_tokens=30
    )
    mock_client.invoke_model_with_response_stream.return_value = {
        "body": [
            {
                "chunk": {
                    "bytes": json.dumps({
                        "type": "content_block_delta",
                        "delta": {"type": "text_delta", "text": "def hello(): "}
                    }).encode("utf-8")
                }
            },
            {
                "chunk": {
                    "bytes": json.dumps({
                        "type": "content_block_delta",
                        "delta": {"type": "text_delta", "text": "pass"}
                    }).encode("utf-8")
                }
            },
            {
                "chunk": {
                    "bytes": json.dumps({
                        "type": "message_stop"
                    }).encode("utf-8")
                }
            }
        ]
    }
    return mock_client


@pytest.fixture(autouse=True)
def patch_bedrock_client(mock_bedrock_runtime, monkeypatch):
    """Automatically patch boto3.client to return our mock Bedrock runtime."""
    original_boto3_client = None

    def mock_boto3_client(service_name, *args, **kwargs):
        if service_name == "bedrock-runtime":
            return mock_bedrock_runtime
        # For other services, create a real client (shouldn't happen in tests)
        import boto3
        return boto3.client(service_name, *args, **kwargs)

    monkeypatch.setattr("boto3.client", mock_boto3_client)
    return mock_bedrock_runtime
