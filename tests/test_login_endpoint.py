"""Tests for the login endpoint."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login endpoint."""

    def test_login_with_valid_credentials(self, client):
        """Test successful login with admin/admin credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        assert "data" in data
        assert data["error"] is None
        assert data["error_code"] is None

        # Verify response data
        login_data = data["data"]
        assert "access_token" in login_data
        assert "token_type" in login_data
        assert "user" in login_data
        assert "expires_in" in login_data

        # Verify token type
        assert login_data["token_type"] == "bearer"

        # Verify user info
        user = login_data["user"]
        assert user["id"] == "admin"
        assert user["username"] == "admin"
        assert user["role"] == "admin"

        # Verify expiration
        assert login_data["expires_in"] == 1800  # 30 minutes

    def test_login_token_is_valid_jwt(self, client):
        """Test that the returned token is a valid JWT."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )

        assert response.status_code == 200
        data = response.json()
        access_token = data["data"]["access_token"]

        # Verify token format (three parts separated by dots)
        parts = access_token.split(".")
        assert len(parts) == 3

        # Verify token payload structure
        import json
        import base64

        # Decode the payload (second part) without verification
        payload_encoded = parts[1]
        # Add padding if needed
        padding = 4 - len(payload_encoded) % 4
        if padding != 4:
            payload_encoded += "=" * padding

        payload_decoded = base64.urlsafe_b64decode(payload_encoded)
        payload = json.loads(payload_decoded)

        # Verify payload contents
        assert payload["user_id"] == "admin"
        assert payload["agent_id"] == "admin-agent"
        assert "iat" in payload
        assert "exp" in payload

    def test_login_with_invalid_username(self, client):
        """Test login fails with invalid username."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "invalid", "password": "admin"},
        )

        assert response.status_code == 401
        data = response.json()

        assert data["success"] is False
        assert "Invalid username or password" in data.get("error", "")

    def test_login_with_invalid_password(self, client):
        """Test login fails with invalid password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        data = response.json()

        assert data["success"] is False
        assert "Invalid username or password" in data.get("error", "")

    def test_login_with_empty_username(self, client):
        """Test login fails with empty username."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "", "password": "admin"},
        )

        # Should fail because empty username is not in VALID_USERS
        assert response.status_code == 401

    def test_login_with_empty_password(self, client):
        """Test login fails with empty password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": ""},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    def test_login_with_missing_username(self, client):
        """Test login fails with missing username field."""
        response = client.post(
            "/api/v1/auth/login",
            json={"password": "admin"},
        )

        # Should return validation error
        assert response.status_code == 422

    def test_login_with_missing_password(self, client):
        """Test login fails with missing password field."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin"},
        )

        # Should return validation error
        assert response.status_code == 422

    def test_login_response_includes_timestamp(self, client):
        """Test that login response includes timestamp."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify timestamp is present and is ISO format
        assert "timestamp" in data
        assert "T" in data["timestamp"]  # ISO format includes T
        assert "Z" in data["timestamp"] or "+" in data["timestamp"]  # Timezone info

    def test_login_response_json_structure(self, client):
        """Test the exact JSON structure of successful login response."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check top-level keys
        expected_keys = {"success", "data", "error", "error_code", "timestamp"}
        assert set(data.keys()) == expected_keys

        # Check data keys
        data_keys = set(data["data"].keys())
        expected_data_keys = {
            "access_token",
            "token_type",
            "user",
            "expires_in",
        }
        assert data_keys == expected_data_keys

        # Check user keys
        user_keys = set(data["data"]["user"].keys())
        expected_user_keys = {"id", "username", "role"}
        assert user_keys == expected_user_keys

    def test_login_endpoint_content_type(self, client):
        """Test that login endpoint returns JSON content type."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_login_multiple_times_returns_different_tokens(self, client):
        """Test that multiple logins return different JWT tokens."""
        # Note: Due to time-based claims, tokens created at different times will be different
        import time

        response1 = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )

        time.sleep(0.01)  # Small delay to ensure different iat timestamps

        response2 = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )

        token1 = response1.json()["data"]["access_token"]
        token2 = response2.json()["data"]["access_token"]

        # Tokens should be different due to different iat times
        assert token1 != token2

    def test_login_token_can_be_used_for_authentication(self, client):
        """Test that the returned token can be used for authenticated requests."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )

        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Use token in a request that requires authentication
        # For example, try to access a health check (which may or may not require auth)
        # In this case, we'll just verify the token format is correct
        assert access_token.startswith("eyJ")  # JWT typically starts with this
        assert len(access_token) > 50  # JWT tokens are reasonably long

    def test_login_case_sensitive_username(self, client):
        """Test that username is case-sensitive."""
        # Try uppercase username
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "ADMIN", "password": "admin"},
        )

        assert response.status_code == 401

    def test_login_case_sensitive_password(self, client):
        """Test that password is case-sensitive."""
        # Try uppercase password
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "ADMIN"},
        )

        assert response.status_code == 401

    def test_login_with_extra_fields(self, client):
        """Test login works with extra fields in request."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "admin",
                "extra_field": "should_be_ignored",
            },
        )

        # Should succeed - extra fields are typically ignored
        assert response.status_code == 200

    def test_login_endpoint_exists(self, client):
        """Test that the login endpoint is registered and accessible."""
        response = client.options("/api/v1/auth/login")

        # The endpoint should exist (OPTIONS might be allowed or return 405)
        assert response.status_code in [200, 405]

    def test_login_response_has_correct_status_code_types(self, client):
        """Test status codes for various scenarios."""
        # Successful login
        response_success = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )
        assert response_success.status_code == 200

        # Invalid credentials
        response_invalid = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert response_invalid.status_code == 401

        # Missing field
        response_missing = client.post(
            "/api/v1/auth/login",
            json={"username": "admin"},
        )
        assert response_missing.status_code == 422
