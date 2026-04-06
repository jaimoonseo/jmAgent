"""Unit tests for plugin management endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from src.api.main import app
from src.plugins.manager import PluginManager


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
def plugin_manager():
    """Create a plugin manager with test plugins."""
    from src.plugins.base import Plugin

    manager = PluginManager()

    # Create test plugin classes
    class TestPlugin1(Plugin):
        name = "test_plugin_1"
        version = "1.0.0"
        description = "Test plugin 1"
        author = "test"

        async def execute(self, hook: str, *args, **kwargs):
            return {"hook": hook, "status": "executed"}

    class TestPlugin2(Plugin):
        name = "test_plugin_2"
        version = "2.0.0"
        description = "Test plugin 2"
        author = "test"

        async def execute(self, hook: str, *args, **kwargs):
            return {"hook": hook, "status": "executed"}

    # Register test plugins
    plugin1 = TestPlugin1()
    plugin1.enable()
    manager.register_plugin(plugin1)

    plugin2 = TestPlugin2()
    # Leave plugin2 disabled
    manager.register_plugin(plugin2)

    return manager


def get_auth_headers(token: str) -> dict:
    """Get authorization headers with Bearer token."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def mock_plugin_singleton(plugin_manager, monkeypatch):
    """Mock the PluginManager singleton."""
    import src.api.routes.plugins as plugins_module

    monkeypatch.setattr(
        plugins_module,
        "plugin_manager",
        plugin_manager,
    )
    return plugin_manager


class TestPluginsListEndpoint:
    """Tests for GET /api/v1/plugins endpoint."""

    def test_list_plugins_success(self, client, auth_token):
        """Test successful listing of all plugins."""
        response = client.get(
            "/api/v1/plugins",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "plugins" in data["data"]

        plugins = data["data"]["plugins"]
        assert len(plugins) >= 2  # At least 2 test plugins
        assert any(p["name"] == "test_plugin_1" for p in plugins)
        assert any(p["name"] == "test_plugin_2" for p in plugins)

    def test_list_plugins_without_auth(self, client):
        """Test that listing plugins requires authentication."""
        response = client.get("/api/v1/plugins")
        assert response.status_code == 401

    def test_list_plugins_contains_metadata(self, client, auth_token):
        """Test that plugin list includes expected fields."""
        response = client.get(
            "/api/v1/plugins",
            headers=get_auth_headers(auth_token),
        )

        plugins = response.json()["data"]["plugins"]
        if plugins:
            plugin = plugins[0]
            assert "name" in plugin
            assert "enabled" in plugin
            assert "version" in plugin
            assert "description" in plugin

    def test_list_plugins_enabled_status(self, client, auth_token):
        """Test that plugin enabled status is reported."""
        response = client.get(
            "/api/v1/plugins",
            headers=get_auth_headers(auth_token),
        )

        plugins = response.json()["data"]["plugins"]
        plugin_1 = next(p for p in plugins if p["name"] == "test_plugin_1")
        plugin_2 = next(p for p in plugins if p["name"] == "test_plugin_2")

        assert plugin_1["enabled"] is True
        assert plugin_2["enabled"] is False


class TestPluginDetailEndpoint:
    """Tests for GET /api/v1/plugins/{name} endpoint."""

    def test_get_plugin_detail_success(self, client, auth_token):
        """Test successful retrieval of plugin details."""
        response = client.get(
            "/api/v1/plugins/test_plugin_1",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        plugin = data["data"]
        assert plugin["name"] == "test_plugin_1"
        assert plugin["version"] == "1.0.0"
        assert plugin["description"] == "Test plugin 1"
        assert plugin["enabled"] is True
        assert "config_schema" in plugin

    def test_get_plugin_detail_without_auth(self, client):
        """Test that getting plugin details requires authentication."""
        response = client.get("/api/v1/plugins/test_plugin_1")
        assert response.status_code == 401

    def test_get_nonexistent_plugin(self, client, auth_token):
        """Test retrieving a non-existent plugin."""
        response = client.get(
            "/api/v1/plugins/nonexistent_plugin",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_get_plugin_detail_config_schema(self, client, auth_token):
        """Test that plugin config schema is included."""
        response = client.get(
            "/api/v1/plugins/test_plugin_1",
            headers=get_auth_headers(auth_token),
        )

        plugin = response.json()["data"]
        assert "config_schema" in plugin
        assert isinstance(plugin["config_schema"], dict)


class TestPluginEnableEndpoint:
    """Tests for POST /api/v1/plugins/{name}/enable endpoint."""

    def test_enable_plugin_success(self, client, auth_token):
        """Test successful enabling of a plugin."""
        response = client.post(
            "/api/v1/plugins/test_plugin_2/enable",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "test_plugin_2"
        assert data["data"]["enabled"] is True

    def test_enable_plugin_without_auth(self, client):
        """Test that enabling plugin requires authentication."""
        response = client.post("/api/v1/plugins/test_plugin_2/enable")
        assert response.status_code == 401

    def test_enable_nonexistent_plugin(self, client, auth_token):
        """Test enabling a non-existent plugin."""
        response = client.post(
            "/api/v1/plugins/nonexistent_plugin/enable",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 404

    def test_enable_already_enabled_plugin(self, client, auth_token):
        """Test enabling a plugin that's already enabled."""
        response = client.post(
            "/api/v1/plugins/test_plugin_1/enable",
            headers=get_auth_headers(auth_token),
        )

        # Should succeed (idempotent)
        assert response.status_code == 200
        assert response.json()["data"]["enabled"] is True


class TestPluginDisableEndpoint:
    """Tests for POST /api/v1/plugins/{name}/disable endpoint."""

    def test_disable_plugin_success(self, client, auth_token):
        """Test successful disabling of a plugin."""
        response = client.post(
            "/api/v1/plugins/test_plugin_1/disable",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "test_plugin_1"
        assert data["data"]["enabled"] is False

    def test_disable_plugin_without_auth(self, client):
        """Test that disabling plugin requires authentication."""
        response = client.post("/api/v1/plugins/test_plugin_1/disable")
        assert response.status_code == 401

    def test_disable_nonexistent_plugin(self, client, auth_token):
        """Test disabling a non-existent plugin."""
        response = client.post(
            "/api/v1/plugins/nonexistent_plugin/disable",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 404

    def test_disable_already_disabled_plugin(self, client, auth_token):
        """Test disabling a plugin that's already disabled."""
        response = client.post(
            "/api/v1/plugins/test_plugin_2/disable",
            headers=get_auth_headers(auth_token),
        )

        # Should succeed (idempotent)
        assert response.status_code == 200
        assert response.json()["data"]["enabled"] is False


class TestPluginGetConfigEndpoint:
    """Tests for GET /api/v1/plugins/{name}/config endpoint."""

    def test_get_plugin_config_success(self, client, auth_token):
        """Test successful retrieval of plugin configuration."""
        response = client.get(
            "/api/v1/plugins/test_plugin_1/config",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "config" in data["data"]
        assert data["data"]["name"] == "test_plugin_1"

    def test_get_plugin_config_without_auth(self, client):
        """Test that getting config requires authentication."""
        response = client.get("/api/v1/plugins/test_plugin_1/config")
        assert response.status_code == 401

    def test_get_config_nonexistent_plugin(self, client, auth_token):
        """Test getting config for non-existent plugin."""
        response = client.get(
            "/api/v1/plugins/nonexistent_plugin/config",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 404


class TestPluginUpdateConfigEndpoint:
    """Tests for POST /api/v1/plugins/{name}/config endpoint."""

    def test_update_plugin_config_success(self, client, auth_token):
        """Test successful updating of plugin configuration."""
        request_body = {
            "config": {
                "option1": "new_value",
                "option2": True,
            }
        }

        response = client.post(
            "/api/v1/plugins/test_plugin_1/config",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "test_plugin_1"
        assert data["data"]["updated"] is True
        assert data["data"]["config"]["option1"] == "new_value"

    def test_update_plugin_config_without_auth(self, client):
        """Test that updating config requires authentication."""
        request_body = {"config": {"option1": "value"}}
        response = client.post(
            "/api/v1/plugins/test_plugin_1/config",
            json=request_body,
        )
        assert response.status_code == 401

    def test_update_config_nonexistent_plugin(self, client, auth_token):
        """Test updating config for non-existent plugin."""
        request_body = {"config": {"option1": "value"}}
        response = client.post(
            "/api/v1/plugins/nonexistent_plugin/config",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 404

    def test_update_plugin_config_empty(self, client, auth_token):
        """Test updating plugin config with empty config."""
        request_body = {"config": {}}

        response = client.post(
            "/api/v1/plugins/test_plugin_1/config",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        # Should succeed
        assert response.status_code == 200


class TestPluginStateTransitions:
    """Tests for plugin state transitions."""

    def test_enable_disable_cycle(self, client, auth_token):
        """Test enable/disable state transitions."""
        # Start with disabled
        disable_response = client.post(
            "/api/v1/plugins/test_plugin_1/disable",
            headers=get_auth_headers(auth_token),
        )
        assert disable_response.status_code == 200
        assert disable_response.json()["data"]["enabled"] is False

        # Enable
        enable_response = client.post(
            "/api/v1/plugins/test_plugin_1/enable",
            headers=get_auth_headers(auth_token),
        )
        assert enable_response.status_code == 200
        assert enable_response.json()["data"]["enabled"] is True

        # Verify via list
        list_response = client.get(
            "/api/v1/plugins",
            headers=get_auth_headers(auth_token),
        )
        plugins = list_response.json()["data"]["plugins"]
        plugin_1 = next(p for p in plugins if p["name"] == "test_plugin_1")
        assert plugin_1["enabled"] is True

    def test_config_persists_across_disable(self, client, auth_token):
        """Test that config persists when disabling/enabling plugin."""
        # Set config
        set_config_response = client.post(
            "/api/v1/plugins/test_plugin_1/config",
            json={"config": {"option1": "persisted_value"}},
            headers=get_auth_headers(auth_token),
        )
        assert set_config_response.status_code == 200

        # Disable
        client.post(
            "/api/v1/plugins/test_plugin_1/disable",
            headers=get_auth_headers(auth_token),
        )

        # Enable
        client.post(
            "/api/v1/plugins/test_plugin_1/enable",
            headers=get_auth_headers(auth_token),
        )

        # Check config persisted
        get_config_response = client.get(
            "/api/v1/plugins/test_plugin_1/config",
            headers=get_auth_headers(auth_token),
        )
        assert get_config_response.status_code == 200
        config = get_config_response.json()["data"]["config"]
        assert config.get("option1") == "persisted_value"


class TestPluginIntegration:
    """Integration tests for plugin endpoints."""

    def test_plugin_lifecycle(self, client, auth_token):
        """Test complete plugin lifecycle."""
        # List plugins
        list_response = client.get(
            "/api/v1/plugins",
            headers=get_auth_headers(auth_token),
        )
        initial_count = len(list_response.json()["data"]["plugins"])

        # Get details
        detail_response = client.get(
            "/api/v1/plugins/test_plugin_1",
            headers=get_auth_headers(auth_token),
        )
        assert detail_response.status_code == 200

        # Update config
        config_response = client.post(
            "/api/v1/plugins/test_plugin_1/config",
            json={"config": {"option1": "test"}},
            headers=get_auth_headers(auth_token),
        )
        assert config_response.status_code == 200

        # Disable
        disable_response = client.post(
            "/api/v1/plugins/test_plugin_1/disable",
            headers=get_auth_headers(auth_token),
        )
        assert disable_response.status_code == 200

        # Re-list
        recheck_response = client.get(
            "/api/v1/plugins",
            headers=get_auth_headers(auth_token),
        )
        assert len(recheck_response.json()["data"]["plugins"]) == initial_count

    def test_plugin_response_format(self, client, auth_token):
        """Test that plugin responses have correct format."""
        response = client.get(
            "/api/v1/plugins",
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
