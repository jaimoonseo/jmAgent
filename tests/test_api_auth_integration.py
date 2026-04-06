"""Integration tests for authentication and security features."""

import pytest
from src.api.security.auth import (
    JwtSettings,
    create_token,
    verify_token,
    get_current_user,
    APIKeyValidator,
)
from src.api.security.rate_limiter import RateLimiter
from src.api.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client for the main app."""
    return TestClient(app)


class TestAuthenticationIntegration:
    """Integration tests for JWT authentication with main API."""

    def test_health_endpoint_accessible(self, client):
        """Test that public endpoint is accessible."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_token_creation_and_verification_integration(self):
        """Test complete token creation and verification flow."""
        settings = JwtSettings()

        # Create token
        token = create_token(
            user_id="test_user",
            agent_id="test_agent",
            settings=settings,
        )

        # Verify token
        payload = verify_token(token, settings=settings)

        # Assertions
        assert payload["user_id"] == "test_user"
        assert payload["agent_id"] == "test_agent"
        assert "exp" in payload
        assert "iat" in payload

    def test_different_secret_keys_invalidate_token(self):
        """Test that tokens are bound to their secret key."""
        settings1 = JwtSettings(secret_key="secret1")
        settings2 = JwtSettings(secret_key="secret2")

        token = create_token("user1", "agent1", settings=settings1)

        # Should work with original settings
        payload = verify_token(token, settings=settings1)
        assert payload["user_id"] == "user1"

        # Should fail with different settings
        from src.api.security.auth import InvalidTokenError

        with pytest.raises(InvalidTokenError):
            verify_token(token, settings=settings2)


class TestAPIKeyIntegration:
    """Integration tests for API key validation."""

    def test_api_key_validator_integration(self):
        """Test APIKeyValidator integration with settings."""
        validator = APIKeyValidator(api_key="test-key-12345")

        # Valid key
        assert validator.validate("test-key-12345") is True

        # Invalid key
        assert validator.validate("wrong-key") is False


class TestRateLimiterIntegration:
    """Integration tests for rate limiting."""

    def test_rate_limiter_prevents_abuse(self):
        """Test rate limiter prevents request abuse."""
        limiter = RateLimiter(default_limit=3, default_window=60)
        user_id = "user123"

        # First 3 requests should succeed
        assert limiter.check_rate_limit(user_id) is True
        assert limiter.check_rate_limit(user_id) is True
        assert limiter.check_rate_limit(user_id) is True

        # 4th should fail
        assert limiter.check_rate_limit(user_id) is False

    def test_rate_limiter_independent_users(self):
        """Test rate limiter tracks users independently."""
        limiter = RateLimiter(default_limit=2, default_window=60)

        # User1 maxes out
        assert limiter.check_rate_limit("user1") is True
        assert limiter.check_rate_limit("user1") is True
        assert limiter.check_rate_limit("user1") is False

        # User2 should still work
        assert limiter.check_rate_limit("user2") is True
        assert limiter.check_rate_limit("user2") is True
        assert limiter.check_rate_limit("user2") is False

    def test_rate_limiter_reset_clears_state(self):
        """Test rate limiter reset functionality."""
        limiter = RateLimiter(default_limit=1, default_window=60)

        # User hits limit
        assert limiter.check_rate_limit("user1") is True
        assert limiter.check_rate_limit("user1") is False

        # After reset, should work again
        limiter.reset()
        assert limiter.check_rate_limit("user1") is True


class TestTokenLifecycle:
    """Tests for complete token lifecycle."""

    def test_create_verify_token_cycle(self):
        """Test complete token creation and verification cycle."""
        settings = JwtSettings()

        # Create
        token = create_token("user1", "agent1", settings=settings)
        assert token is not None
        assert len(token) > 0

        # Verify
        payload = verify_token(token, settings=settings)
        assert payload["user_id"] == "user1"
        assert payload["agent_id"] == "agent1"
        assert "exp" in payload
        assert "iat" in payload

    def test_token_payload_accessible(self):
        """Test token payload contains expected data."""
        settings = JwtSettings()
        token = create_token("test_user", "test_agent", settings=settings)
        payload = verify_token(token, settings=settings)

        # Verify all required fields
        assert "user_id" in payload
        assert "agent_id" in payload
        assert "iat" in payload
        assert "exp" in payload

        # Verify values
        assert payload["user_id"] == "test_user"
        assert payload["agent_id"] == "test_agent"


class TestSecurityHeadersIntegration:
    """Tests for security headers in actual API responses."""

    def test_security_headers_in_response(self):
        """Test security headers are included in all responses."""
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/api/v1/health")

        # Verify security headers
        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"

        assert "x-frame-options" in response.headers
        assert response.headers["x-frame-options"] == "DENY"

        assert "x-xss-protection" in response.headers
        assert response.headers["x-xss-protection"] == "1; mode=block"

    def test_security_headers_on_error(self):
        """Test security headers present even on error responses."""
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/api/v1/nonexistent")

        # Should be 404 but still have security headers
        assert response.status_code == 404
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers
        assert "x-xss-protection" in response.headers
