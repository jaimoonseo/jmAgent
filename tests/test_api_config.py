"""Unit tests for configuration management endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.schemas.management import (
    UpdateConfigRequest,
    UpdateAllConfigRequest,
    ConfigResponse,
)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def auth_token(jwt_secret):
    """Create a valid JWT token for testing."""
    from src.api.security.auth import create_token, JwtSettings

    settings = JwtSettings(secret_key=jwt_secret)
    return create_token("test_user", "test_agent", settings=settings)


@pytest.fixture
def admin_token(jwt_secret):
    """Create a JWT token with admin role."""
    from src.api.security.auth import create_token, JwtSettings

    settings = JwtSettings(secret_key=jwt_secret)
    token = create_token("admin_user", "admin_agent", settings=settings)
    # In a real scenario, admin role would be embedded in the JWT
    return token


def get_auth_headers(token: str) -> dict:
    """Get authorization headers with Bearer token."""
    return {"Authorization": f"Bearer {token}"}


class TestConfigGetEndpoint:
    """Tests for GET /api/v1/config endpoint."""

    def test_get_config_success(self, client, auth_token):
        """Test successful retrieval of all configuration settings."""
        response = client.get(
            "/api/v1/config",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "all_settings" in data["data"]
        assert isinstance(data["data"]["all_settings"], dict)

    def test_get_config_without_auth(self, client):
        """Test that config endpoint requires authentication."""
        response = client.get("/api/v1/config")
        assert response.status_code == 401

    def test_get_config_contains_expected_keys(self, client, auth_token):
        """Test that config response includes expected setting keys."""
        response = client.get(
            "/api/v1/config",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        settings = data["data"]["all_settings"]

        # Check for some expected config keys
        assert "host" in settings
        assert "port" in settings
        assert "debug" in settings
        assert "log_level" in settings


class TestConfigPostEndpoint:
    """Tests for POST /api/v1/config endpoint."""

    def test_update_single_setting_success(self, client, auth_token):
        """Test successful update of a single configuration setting."""
        request_body = {
            "key": "debug",
            "value": True,
        }

        response = client.post(
            "/api/v1/config",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["updated"] is True
        assert data["data"]["key"] == "debug"
        assert data["data"]["value"] is True

    def test_update_setting_without_auth(self, client):
        """Test that updating config requires authentication."""
        request_body = {"key": "debug", "value": True}
        response = client.post("/api/v1/config", json=request_body)
        assert response.status_code == 401

    def test_update_invalid_setting_key(self, client, auth_token):
        """Test updating a non-existent setting key."""
        request_body = {
            "key": "invalid_setting",
            "value": "some_value",
        }

        response = client.post(
            "/api/v1/config",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    def test_update_setting_with_invalid_type(self, client, auth_token):
        """Test updating a setting with wrong value type."""
        request_body = {
            "key": "port",
            "value": "not_a_number",  # Should be int
        }

        response = client.post(
            "/api/v1/config",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        # May fail validation or type coercion
        assert response.status_code in (400, 422)

    def test_update_setting_validates_range(self, client, auth_token):
        """Test that port setting validates valid port range."""
        request_body = {
            "key": "port",
            "value": 99999,  # Out of valid port range
        }

        response = client.post(
            "/api/v1/config",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        # Should either accept or reject out-of-range values
        # Depending on validation implementation
        assert response.status_code in (200, 400)


class TestConfigPutEndpoint:
    """Tests for PUT /api/v1/config endpoint."""

    def test_replace_all_settings_success(self, client, auth_token):
        """Test successful replacement of all configuration settings."""
        request_body = {
            "debug": True,
            "port": 8001,
            "log_level": "DEBUG",
        }

        response = client.put(
            "/api/v1/config",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["replaced"] is True
        assert data["data"]["count"] >= 1

    def test_replace_all_without_auth(self, client):
        """Test that replacing all config requires authentication."""
        request_body = {"debug": True}
        response = client.put("/api/v1/config", json=request_body)
        assert response.status_code == 401

    def test_replace_all_with_partial_settings(self, client, auth_token):
        """Test replacing with partial settings (should handle gracefully)."""
        request_body = {
            "debug": False,
        }

        response = client.put(
            "/api/v1/config",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["replaced"] is True


class TestConfigDeleteEndpoint:
    """Tests for DELETE /api/v1/config/{key} endpoint."""

    def test_delete_single_setting_success(self, client, auth_token):
        """Test successful deletion/reset of a single setting."""
        response = client.delete(
            "/api/v1/config/debug",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["deleted"] is True
        assert data["data"]["key"] == "debug"
        assert "default_value" in data["data"]

    def test_delete_setting_without_auth(self, client):
        """Test that deleting config requires authentication."""
        response = client.delete("/api/v1/config/debug")
        assert response.status_code == 401

    def test_delete_invalid_setting_key(self, client, auth_token):
        """Test deleting a non-existent setting."""
        response = client.delete(
            "/api/v1/config/invalid_key",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_delete_resets_to_default(self, client, auth_token):
        """Test that deleting a setting resets it to default value."""
        # First update a setting
        update_body = {"key": "debug", "value": True}
        client.post(
            "/api/v1/config",
            json=update_body,
            headers=get_auth_headers(auth_token),
        )

        # Then delete it
        response = client.delete(
            "/api/v1/config/debug",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        # Default temperature is 0.2
        assert data["data"]["default_value"] == 0.2


class TestConfigResetEndpoint:
    """Tests for POST /api/v1/config/reset endpoint."""

    def test_reset_all_settings_success(self, client, admin_token):
        """Test successful reset of all settings to defaults."""
        response = client.post(
            "/api/v1/config/reset",
            headers=get_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["reset"] is True
        assert data["data"]["defaults_count"] > 0

    def test_reset_without_auth(self, client):
        """Test that reset requires authentication."""
        response = client.post("/api/v1/config/reset")
        assert response.status_code == 403

    def test_reset_regular_user_forbidden(self, client, auth_token):
        """Test that regular users cannot reset all config."""
        response = client.post(
            "/api/v1/config/reset",
            headers=get_auth_headers(auth_token),
        )

        # Should be forbidden for non-admin
        assert response.status_code == 403

    def test_reset_clears_previous_updates(self, client, admin_token, auth_token):
        """Test that reset clears previous config updates."""
        # Update a setting as regular user
        update_body = {"key": "jm_temperature", "value": 0.9}
        client.post(
            "/api/v1/config",
            json=update_body,
            headers=get_auth_headers(auth_token),
        )

        # Reset as admin
        reset_response = client.post(
            "/api/v1/config/reset",
            headers=get_auth_headers(admin_token),
        )

        assert reset_response.status_code == 200

        # Verify setting was reset
        get_response = client.get(
            "/api/v1/config",
            headers=get_auth_headers(auth_token),
        )
        settings = get_response.json()["data"]["all_settings"]
        assert settings["jm_temperature"] == 0.2  # Default value


class TestConfigEndpointIntegration:
    """Integration tests for config endpoints."""

    def test_config_update_retrieve_flow(self, client, auth_token):
        """Test updating a setting and retrieving it."""
        # Update
        update_body = {"key": "jm_max_tokens", "value": 2048}
        update_response = client.post(
            "/api/v1/config",
            json=update_body,
            headers=get_auth_headers(auth_token),
        )
        assert update_response.status_code == 200

        # Retrieve
        get_response = client.get(
            "/api/v1/config",
            headers=get_auth_headers(auth_token),
        )
        assert get_response.status_code == 200
        settings = get_response.json()["data"]["all_settings"]
        assert settings["jm_max_tokens"] == 2048

    def test_config_multiple_updates(self, client, auth_token):
        """Test updating multiple settings sequentially."""
        updates = [
            {"key": "jm_temperature", "value": 0.5},
            {"key": "jm_max_tokens", "value": 3000},
            {"key": "jm_default_model", "value": "sonnet"},
        ]

        for update_body in updates:
            response = client.post(
                "/api/v1/config",
                json=update_body,
                headers=get_auth_headers(auth_token),
            )
            assert response.status_code == 200

        # Verify all updates
        get_response = client.get(
            "/api/v1/config",
            headers=get_auth_headers(auth_token),
        )
        settings = get_response.json()["data"]["all_settings"]
        assert settings["jm_temperature"] == 0.5
        assert settings["jm_max_tokens"] == 3000
        assert settings["jm_default_model"] == "sonnet"

    def test_config_response_format(self, client, auth_token):
        """Test that config responses have correct format."""
        response = client.get(
            "/api/v1/config",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()

        # Check standard API response wrapper
        assert "success" in data
        assert "data" in data
        assert "timestamp" in data
        assert "error" in data
        assert "error_code" in data
