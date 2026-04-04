import os
import json
import pytest
from unittest.mock import patch, MagicMock
from src.auth.bedrock_auth import detect_auth_mode, build_bedrock_runtime, invoke_bedrock
from src.errors.exceptions import ConfigurationError


def test_detect_auth_mode_with_api_key():
    """Test detect_auth_mode returns 'api_key' when bearer token is set."""
    with patch.dict(os.environ, {"AWS_BEARER_TOKEN_BEDROCK": "test-token"}):
        assert detect_auth_mode() == "api_key"


def test_detect_auth_mode_with_absk_access_key():
    """Test detect_auth_mode returns 'api_key' when ACCESS_KEY starts with ABSK."""
    with patch.dict(os.environ, {"AWS_ACCESS_KEY_ID": "ABSK-12345"}):
        assert detect_auth_mode() == "api_key"


def test_detect_auth_mode_with_iam():
    """Test detect_auth_mode returns 'iam' when only IAM creds are set."""
    with patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "AKIA-12345",
        "AWS_SECRET_ACCESS_KEY": "secret"
    }, clear=True):
        assert detect_auth_mode() == "iam"


def test_detect_auth_mode_default_iam():
    """Test detect_auth_mode defaults to 'iam' when no auth set."""
    with patch.dict(os.environ, {}, clear=True):
        assert detect_auth_mode() == "iam"


def test_build_bedrock_runtime_with_api_key():
    """Test build_bedrock_runtime with API Key auth."""
    with patch.dict(os.environ, {"AWS_BEARER_TOKEN_BEDROCK": "test-token"}):
        with patch("boto3.client") as mock_client:
            result = build_bedrock_runtime()
            mock_client.assert_called_once_with("bedrock-runtime", region_name="us-east-1")


def test_build_bedrock_runtime_with_iam():
    """Test build_bedrock_runtime with IAM auth."""
    with patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "AKIA-12345",
        "AWS_SECRET_ACCESS_KEY": "secret"
    }, clear=True):
        with patch("boto3.client") as mock_client:
            build_bedrock_runtime()
            mock_client.assert_called_once()
            call_kwargs = mock_client.call_args[1]
            assert call_kwargs["aws_access_key_id"] == "AKIA-12345"
            assert call_kwargs["aws_secret_access_key"] == "secret"


def test_build_bedrock_runtime_iam_missing_secret():
    """Test build_bedrock_runtime raises error when secret key missing."""
    with patch.dict(os.environ, {"AWS_ACCESS_KEY_ID": "AKIA-12345"}, clear=True):
        with pytest.raises(ConfigurationError, match="IAM authentication requires"):
            build_bedrock_runtime()


def test_invoke_bedrock_success():
    """Test invoke_bedrock successfully parses response."""
    mock_client = MagicMock()
    mock_response = {
        "body": MagicMock(read=lambda: json.dumps({
            "content": [{"text": "Generated code"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 100, "output_tokens": 50}
        }).encode())
    }
    mock_client.invoke_model.return_value = mock_response

    result = invoke_bedrock(
        mock_client,
        "anthropic.claude-haiku-4-5-20251001-v1:0",
        {"test": "body"}
    )

    assert result["content"] == "Generated code"
    assert result["stop_reason"] == "end_turn"
    assert result["usage"]["input_tokens"] == 100
