"""Tests for health check endpoints."""

import pytest
import time
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.models import HealthStatus
from datetime import datetime


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestHealthCheckEndpoint:
    """Tests for /api/v1/health endpoint."""

    def test_health_endpoint_returns_200(self, client):
        """Test that health endpoint returns 200 OK."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client):
        """Test that health endpoint returns JSON."""
        response = client.get("/api/v1/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_response_structure(self, client):
        """Test that health response has required fields."""
        response = client.get("/api/v1/health")
        data = response.json()

        # Check top-level fields
        assert "success" in data
        assert "data" in data
        assert data["success"] is True

        # Check health data fields
        health_data = data["data"]
        assert "status" in health_data
        assert "version" in health_data
        assert "timestamp" in health_data
        assert "uptime_seconds" in health_data
        assert "components" in health_data

    def test_health_status_value(self, client):
        """Test that health status is valid."""
        response = client.get("/api/v1/health")
        data = response.json()
        status = data["data"]["status"]
        assert status in ["healthy", "degraded", "unhealthy"]

    def test_health_version(self, client):
        """Test that health response contains version."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["data"]["version"] == "1.0.0"

    def test_health_uptime_positive(self, client):
        """Test that uptime is a positive number."""
        response = client.get("/api/v1/health")
        data = response.json()
        uptime = data["data"]["uptime_seconds"]
        assert isinstance(uptime, (int, float))
        assert uptime >= 0

    def test_health_timestamp_valid_iso(self, client):
        """Test that timestamp is valid ISO format."""
        response = client.get("/api/v1/health")
        data = response.json()
        timestamp = data["data"]["timestamp"]
        # Should be parseable as ISO format
        try:
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"Invalid ISO timestamp: {timestamp}")

    def test_health_components_list(self, client):
        """Test that components is a list."""
        response = client.get("/api/v1/health")
        data = response.json()
        components = data["data"]["components"]
        assert isinstance(components, list)
        assert len(components) > 0

    def test_health_components_structure(self, client):
        """Test that each component has required fields."""
        response = client.get("/api/v1/health")
        data = response.json()
        components = data["data"]["components"]

        for component in components:
            assert "name" in component
            assert "status" in component
            assert component["status"] in ["healthy", "degraded", "unhealthy"]

    def test_health_bedrock_component(self, client):
        """Test that bedrock component is present."""
        response = client.get("/api/v1/health")
        data = response.json()
        components = data["data"]["components"]
        component_names = [c["name"] for c in components]
        assert "bedrock" in component_names

    def test_health_cache_component(self, client):
        """Test that cache component is present."""
        response = client.get("/api/v1/health")
        data = response.json()
        components = data["data"]["components"]
        component_names = [c["name"] for c in components]
        assert "cache" in component_names

    def test_health_database_component(self, client):
        """Test that database component is present."""
        response = client.get("/api/v1/health")
        data = response.json()
        components = data["data"]["components"]
        component_names = [c["name"] for c in components]
        assert "database" in component_names

    def test_health_idempotent(self, client):
        """Test that multiple health checks return consistent results."""
        response1 = client.get("/api/v1/health")
        time.sleep(0.1)
        response2 = client.get("/api/v1/health")

        data1 = response1.json()
        data2 = response2.json()

        # Status should be the same
        assert data1["data"]["status"] == data2["data"]["status"]
        # Version should be the same
        assert data1["data"]["version"] == data2["data"]["version"]
        # Uptime should be greater for second call
        assert data2["data"]["uptime_seconds"] > data1["data"]["uptime_seconds"]


class TestStatusEndpoint:
    """Tests for /api/v1/status endpoint."""

    def test_status_endpoint_returns_200(self, client):
        """Test that status endpoint returns 200 OK."""
        response = client.get("/api/v1/status")
        assert response.status_code == 200

    def test_status_response_structure(self, client):
        """Test that status response has required fields."""
        response = client.get("/api/v1/status")
        data = response.json()

        assert "success" in data
        assert "data" in data
        assert data["success"] is True

        # Check status data fields
        status_data = data["data"]
        assert "version" in status_data
        assert "api_version" in status_data
        assert "status" in status_data
        assert "timestamp" in status_data

    def test_status_version(self, client):
        """Test that status response contains correct version."""
        response = client.get("/api/v1/status")
        data = response.json()
        assert data["data"]["version"] == "1.0.0"

    def test_status_api_version(self, client):
        """Test that status response contains correct API version."""
        response = client.get("/api/v1/status")
        data = response.json()
        assert data["data"]["api_version"] == "v1"

    def test_status_operational(self, client):
        """Test that status is operational."""
        response = client.get("/api/v1/status")
        data = response.json()
        assert data["data"]["status"] == "operational"

    def test_status_timestamp_valid_iso(self, client):
        """Test that status timestamp is valid ISO format."""
        response = client.get("/api/v1/status")
        data = response.json()
        timestamp = data["data"]["timestamp"]
        try:
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"Invalid ISO timestamp: {timestamp}")


class TestReadinessEndpoint:
    """Tests for /api/v1/ready endpoint."""

    def test_readiness_endpoint_returns_200(self, client):
        """Test that readiness endpoint returns 200 OK."""
        response = client.get("/api/v1/ready")
        assert response.status_code == 200

    def test_readiness_response_structure(self, client):
        """Test that readiness response has required fields."""
        response = client.get("/api/v1/ready")
        data = response.json()

        assert "success" in data
        assert "data" in data
        assert data["success"] is True

    def test_readiness_ready_field(self, client):
        """Test that readiness response has ready field."""
        response = client.get("/api/v1/ready")
        data = response.json()
        assert "ready" in data["data"]
        assert data["data"]["ready"] is True

    def test_readiness_uptime_field(self, client):
        """Test that readiness response has uptime_seconds."""
        response = client.get("/api/v1/ready")
        data = response.json()
        assert "uptime_seconds" in data["data"]
        assert isinstance(data["data"]["uptime_seconds"], (int, float))


class TestHealthEndpointIntegration:
    """Integration tests for health endpoints."""

    def test_health_accessible_multiple_times(self, client):
        """Test that health endpoint can be called multiple times."""
        for _ in range(10):
            response = client.get("/api/v1/health")
            assert response.status_code == 200

    def test_all_health_endpoints_accessible(self, client):
        """Test that all health endpoints are accessible."""
        endpoints = ["/api/v1/health", "/api/v1/status", "/api/v1/ready"]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Endpoint {endpoint} failed"

    def test_health_error_field_missing_on_success(self, client):
        """Test that error fields are not present in successful responses."""
        response = client.get("/api/v1/health")
        data = response.json()
        # error and error_code should either be None or missing
        assert data.get("error") is None
        assert data.get("error_code") is None
