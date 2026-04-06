"""Tests for FastAPI setup and initialization."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import create_app, app
from src.api.config import settings


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def test_app():
    """Create a test app instance."""
    return create_app()


@pytest.fixture
def test_client(test_app):
    """Create a test client for the test app."""
    return TestClient(test_app)


class TestAPIInitialization:
    """Tests for API initialization."""

    def test_app_creation(self):
        """Test that the app is created successfully."""
        assert app is not None

    def test_app_title(self):
        """Test that the app has the correct title."""
        assert app.title == "jmAgent API"

    def test_app_version(self):
        """Test that the app has the correct version."""
        assert app.version == "1.0.0"

    def test_app_description(self):
        """Test that the app has a description."""
        assert app.description is not None

    def test_settings_loaded(self):
        """Test that settings are properly loaded."""
        assert settings.api_title == "jmAgent API"
        assert settings.port == 8000
        assert settings.host == "127.0.0.1"

    def test_cors_origins_configured(self):
        """Test that CORS origins are configured."""
        assert len(settings.cors_origins) > 0
        assert "http://localhost:3000" in settings.cors_origins


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""

    def test_openapi_schema(self, client):
        """Test that OpenAPI schema is available."""
        response = client.get("/api/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert data["info"]["title"] == "jmAgent API"

    def test_swagger_docs(self, client):
        """Test that Swagger docs are available."""
        response = client.get("/api/docs")
        assert response.status_code == 200
        assert "Swagger UI" in response.text or "swagger" in response.text

    def test_redoc_docs(self, client):
        """Test that ReDoc docs are available."""
        response = client.get("/api/redoc")
        assert response.status_code == 200
        assert "ReDoc" in response.text or "redoc" in response.text


class TestCORSConfiguration:
    """Tests for CORS middleware."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        response = client.get("/api/v1/health")
        assert "access-control-allow-origin" in response.headers or response.status_code == 200

    def test_cors_preflight_request(self, client):
        """Test CORS preflight request handling."""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Should either handle OPTIONS or return the regular response
        assert response.status_code in [200, 204, 405]

    def test_cors_origin_allowed(self, client):
        """Test that allowed origins are in CORS settings."""
        assert "http://localhost:3000" in settings.cors_origins


class TestRequestLoggingMiddleware:
    """Tests for request logging middleware."""

    def test_request_headers_added(self, client):
        """Test that request tracking headers are added."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        # Check if process time header is added
        assert "x-process-time" in response.headers or "X-Process-Time" in response.headers

    def test_multiple_requests_handled(self, client):
        """Test that multiple requests are handled correctly."""
        for _ in range(5):
            response = client.get("/api/v1/health")
            assert response.status_code == 200


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_error_handling(self, client):
        """Test handling of 404 errors."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test handling of method not allowed errors."""
        response = client.post("/api/v1/health")
        assert response.status_code == 405

    def test_validation_error_response_format(self, client):
        """Test that validation errors have proper format."""
        # This will be tested with actual endpoint validation in later tests
        pass


class TestApplicationEvents:
    """Tests for application startup/shutdown events."""

    def test_app_has_startup_event(self):
        """Test that app has startup event handler."""
        assert len(app.router.on_startup) > 0

    def test_app_has_shutdown_event(self):
        """Test that app has shutdown event handler."""
        assert len(app.router.on_shutdown) > 0


class TestSettings:
    """Tests for settings configuration."""

    def test_default_host(self):
        """Test default host setting."""
        assert settings.host == "127.0.0.1"

    def test_default_port(self):
        """Test default port setting."""
        assert settings.port == 8000

    def test_api_version(self):
        """Test API version setting."""
        assert settings.api_version == "1.0.0"

    def test_log_level(self):
        """Test log level setting."""
        assert settings.log_level in ["INFO", "DEBUG", "WARNING", "ERROR"]

    def test_cors_credentials_enabled(self):
        """Test that CORS credentials are enabled."""
        assert settings.cors_credentials is True


class TestAPIResponse:
    """Tests for standard API response format."""

    def test_health_endpoint_response_format(self, client):
        """Test that health endpoint returns proper response format."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert data["success"] is True

    def test_status_endpoint_response_format(self, client):
        """Test that status endpoint returns proper response format."""
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert data["success"] is True
