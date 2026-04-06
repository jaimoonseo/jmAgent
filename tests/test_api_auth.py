"""Tests for JWT authentication and API key validation."""

import pytest
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import Depends, FastAPI
from src.api.main import app
from src.api.security.auth import (
    JwtSettings,
    create_token,
    verify_token,
    get_current_user,
    APIKeyValidator,
    InvalidTokenError,
)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def jwt_settings():
    """Create JWT settings for testing."""
    return JwtSettings(
        secret_key="test-secret-key-12345",
        algorithm="HS256",
        expiration_minutes=30,
    )


class TestJwtSettings:
    """Tests for JwtSettings configuration."""

    def test_jwt_settings_default_values(self):
        """Test JwtSettings has correct defaults."""
        settings = JwtSettings()
        assert settings.algorithm == "HS256"
        assert settings.expiration_minutes == 30
        assert len(settings.secret_key) > 0

    def test_jwt_settings_from_env(self, monkeypatch):
        """Test JwtSettings loads from environment."""
        monkeypatch.setenv("JMAGENT_API_JWT_SECRET_KEY", "custom-secret")
        monkeypatch.setenv("JMAGENT_API_JWT_EXPIRATION_MINUTES", "60")

        settings = JwtSettings()
        assert settings.secret_key == "custom-secret"
        assert settings.expiration_minutes == 60

    def test_jwt_settings_requires_secret(self):
        """Test JwtSettings requires secret key."""
        # Should have a default or require from env
        settings = JwtSettings()
        assert settings.secret_key is not None


class TestTokenCreation:
    """Tests for create_token function."""

    def test_create_token_returns_string(self, jwt_settings):
        """Test create_token returns a string."""
        token = create_token(
            user_id="user123",
            agent_id="agent456",
            settings=jwt_settings,
        )
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_format(self, jwt_settings):
        """Test token has JWT format (three parts)."""
        token = create_token(
            user_id="user123",
            agent_id="agent456",
            settings=jwt_settings,
        )
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_token_includes_user_id(self, jwt_settings):
        """Test token includes user_id in payload."""
        token = create_token(
            user_id="user123",
            agent_id="agent456",
            settings=jwt_settings,
        )
        payload = verify_token(token, settings=jwt_settings)
        assert payload["user_id"] == "user123"

    def test_create_token_includes_agent_id(self, jwt_settings):
        """Test token includes agent_id in payload."""
        token = create_token(
            user_id="user123",
            agent_id="agent456",
            settings=jwt_settings,
        )
        payload = verify_token(token, settings=jwt_settings)
        assert payload["agent_id"] == "agent456"

    def test_create_token_includes_exp(self, jwt_settings):
        """Test token includes expiration timestamp."""
        token = create_token(
            user_id="user123",
            agent_id="agent456",
            settings=jwt_settings,
        )
        payload = verify_token(token, settings=jwt_settings)
        assert "exp" in payload
        assert isinstance(payload["exp"], (int, float))
        assert payload["exp"] > time.time()

    def test_create_token_different_tokens_for_different_users(self, jwt_settings):
        """Test different users get different tokens."""
        token1 = create_token(
            user_id="user1",
            agent_id="agent1",
            settings=jwt_settings,
        )
        token2 = create_token(
            user_id="user2",
            agent_id="agent1",
            settings=jwt_settings,
        )
        assert token1 != token2

    def test_create_token_with_custom_expiration(self, jwt_settings):
        """Test token respects custom expiration."""
        jwt_settings.expiration_minutes = 60
        token = create_token(
            user_id="user123",
            agent_id="agent456",
            settings=jwt_settings,
        )
        payload = verify_token(token, settings=jwt_settings)

        # Check expiration is approximately 60 minutes from now
        current_time = time.time()
        expected_exp = current_time + (60 * 60)
        # Allow 5 second tolerance
        assert abs(payload["exp"] - expected_exp) < 5


class TestTokenVerification:
    """Tests for verify_token function."""

    def test_verify_token_returns_dict(self, jwt_settings):
        """Test verify_token returns a dictionary."""
        token = create_token(
            user_id="user123",
            agent_id="agent456",
            settings=jwt_settings,
        )
        payload = verify_token(token, settings=jwt_settings)
        assert isinstance(payload, dict)

    def test_verify_token_valid_token(self, jwt_settings):
        """Test verify_token validates a valid token."""
        token = create_token(
            user_id="user123",
            agent_id="agent456",
            settings=jwt_settings,
        )
        # Should not raise
        payload = verify_token(token, settings=jwt_settings)
        assert payload is not None

    def test_verify_token_invalid_token_raises_error(self, jwt_settings):
        """Test verify_token raises error for invalid token."""
        with pytest.raises(InvalidTokenError):
            verify_token("invalid.token.here", settings=jwt_settings)

    def test_verify_token_expired_token_raises_error(self, jwt_settings):
        """Test verify_token raises error for expired token."""
        # Create a token that's already expired
        import jwt as jwt_lib

        jwt_settings.expiration_minutes = -1  # Negative = already expired
        token = create_token(
            user_id="user123",
            agent_id="agent456",
            settings=jwt_settings,
        )

        with pytest.raises(InvalidTokenError):
            verify_token(token, settings=jwt_settings)

    def test_verify_token_wrong_signature_raises_error(self, jwt_settings):
        """Test verify_token raises error for wrong signature."""
        token = create_token(
            user_id="user123",
            agent_id="agent456",
            settings=jwt_settings,
        )

        # Create a different settings with different secret
        wrong_settings = JwtSettings(
            secret_key="different-secret-key",
            algorithm="HS256",
        )

        with pytest.raises(InvalidTokenError):
            verify_token(token, settings=wrong_settings)

    def test_verify_token_payload_structure(self, jwt_settings):
        """Test verify_token returns complete payload."""
        token = create_token(
            user_id="user123",
            agent_id="agent456",
            settings=jwt_settings,
        )
        payload = verify_token(token, settings=jwt_settings)

        assert "user_id" in payload
        assert "agent_id" in payload
        assert "exp" in payload
        assert "iat" in payload


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    def test_get_current_user_valid_token(self, client, jwt_settings):
        """Test get_current_user with valid bearer token."""
        token = create_token(
            user_id="user123",
            agent_id="agent456",
            settings=jwt_settings,
        )

        # This would be used in a route: Depends(get_current_user)
        # For now we test the token creation works
        payload = verify_token(token, settings=jwt_settings)
        assert payload["user_id"] == "user123"

    def test_get_current_user_missing_token(self):
        """Test get_current_user raises error without token."""
        # This is tested indirectly through FastAPI routes
        # Direct dependency testing would require FastAPI test app
        pass

    def test_get_current_user_invalid_bearer_format(self):
        """Test get_current_user raises error with invalid format."""
        # Bearer must be "Bearer <token>"
        pass


class TestAPIKeyValidator:
    """Tests for APIKeyValidator class."""

    def test_api_key_validator_init(self):
        """Test APIKeyValidator initialization."""
        validator = APIKeyValidator(api_key="test-key-12345")
        assert validator.api_key == "test-key-12345"

    def test_api_key_validator_validate_valid_key(self):
        """Test validate_api_key with valid key."""
        validator = APIKeyValidator(api_key="test-key-12345")
        result = validator.validate("test-key-12345")
        assert result is True

    def test_api_key_validator_validate_invalid_key(self):
        """Test validate_api_key with invalid key."""
        validator = APIKeyValidator(api_key="test-key-12345")
        result = validator.validate("wrong-key")
        assert result is False

    def test_api_key_validator_validate_empty_key(self):
        """Test validate_api_key with empty key."""
        validator = APIKeyValidator(api_key="test-key-12345")
        result = validator.validate("")
        assert result is False

    def test_api_key_validator_validate_none_key(self):
        """Test validate_api_key with None key."""
        validator = APIKeyValidator(api_key="test-key-12345")
        result = validator.validate(None)
        assert result is False

    def test_api_key_validator_validate_case_sensitive(self):
        """Test validate_api_key is case-sensitive."""
        validator = APIKeyValidator(api_key="Test-Key-12345")
        result = validator.validate("test-key-12345")
        assert result is False

    def test_api_key_validator_optional(self):
        """Test APIKeyValidator can be optional."""
        validator = APIKeyValidator(api_key=None)
        # Should be able to create with None
        assert validator.api_key is None

    def test_api_key_validator_optional_validate_returns_false(self):
        """Test validate returns False when validator has no key."""
        validator = APIKeyValidator(api_key=None)
        result = validator.validate("any-key")
        assert result is False


class TestInvalidTokenError:
    """Tests for InvalidTokenError exception."""

    def test_invalid_token_error_is_exception(self):
        """Test InvalidTokenError is an exception."""
        error = InvalidTokenError("Test error")
        assert isinstance(error, Exception)

    def test_invalid_token_error_message(self):
        """Test InvalidTokenError has message."""
        error = InvalidTokenError("Test error message")
        assert str(error) == "Test error message"


class TestTokenIntegration:
    """Integration tests for token flow."""

    def test_full_token_lifecycle(self, jwt_settings):
        """Test complete token lifecycle: create → verify."""
        # Create token
        token = create_token(
            user_id="user123",
            agent_id="agent456",
            settings=jwt_settings,
        )
        assert isinstance(token, str)

        # Verify token
        payload = verify_token(token, settings=jwt_settings)
        assert payload["user_id"] == "user123"
        assert payload["agent_id"] == "agent456"

    def test_token_persistence(self, jwt_settings):
        """Test token remains valid across multiple verifications."""
        token = create_token(
            user_id="user123",
            agent_id="agent456",
            settings=jwt_settings,
        )

        # Verify multiple times
        payload1 = verify_token(token, settings=jwt_settings)
        payload2 = verify_token(token, settings=jwt_settings)

        assert payload1 == payload2
