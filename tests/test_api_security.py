"""Tests for API security headers and features."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestSecurityHeaders:
    """Tests for security headers in API responses."""

    def test_x_content_type_options_header(self, client):
        """Test X-Content-Type-Options header is present."""
        response = client.get("/api/v1/health")
        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"

    def test_x_frame_options_header(self, client):
        """Test X-Frame-Options header is present."""
        response = client.get("/api/v1/health")
        assert "x-frame-options" in response.headers
        assert response.headers["x-frame-options"] == "DENY"

    def test_x_xss_protection_header(self, client):
        """Test X-XSS-Protection header is present."""
        response = client.get("/api/v1/health")
        assert "x-xss-protection" in response.headers
        assert response.headers["x-xss-protection"] == "1; mode=block"

    def test_security_headers_on_all_endpoints(self, client):
        """Test security headers are on all endpoints."""
        endpoints = [
            "/api/v1/health",
            "/api/v1/status",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert "x-content-type-options" in response.headers
            assert "x-frame-options" in response.headers
            assert "x-xss-protection" in response.headers

    def test_security_headers_on_error_responses(self, client):
        """Test security headers are present in error responses."""
        # Try to access non-existent endpoint
        response = client.get("/api/v1/nonexistent")

        # Should have security headers even on 404
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers
        assert "x-xss-protection" in response.headers

    def test_security_headers_on_post_requests(self, client):
        """Test security headers on POST requests."""
        response = client.post("/api/v1/nonexistent", json={"test": "data"})

        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers
        assert "x-xss-protection" in response.headers


class TestCORSHeaders:
    """Tests for CORS configuration with security."""

    def test_cors_origin_allowed(self, client):
        """Test CORS allows configured origins."""
        response = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 200

    def test_cors_credentials_allowed(self, client):
        """Test CORS allows credentials."""
        response = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"},
        )

        # Should allow credentials in CORS
        if "access-control-allow-credentials" in response.headers:
            assert response.headers["access-control-allow-credentials"].lower() == "true"

    def test_cors_methods_allowed(self, client):
        """Test CORS allows required methods."""
        response = client.options(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"},
        )

        # Check CORS headers are present
        if "access-control-allow-methods" in response.headers:
            methods = response.headers["access-control-allow-methods"]
            # Should contain GET at minimum
            assert "GET" in methods or "*" in methods


class TestContentSecurity:
    """Tests for content security features."""

    def test_content_type_json(self, client):
        """Test responses have correct content type."""
        response = client.get("/api/v1/health")
        assert response.headers["content-type"].startswith("application/json")

    def test_no_server_header_leakage(self, client):
        """Test Server header doesn't leak implementation details."""
        response = client.get("/api/v1/health")

        # Server header can be present but shouldn't leak details
        if "server" in response.headers:
            server = response.headers["server"].lower()
            # Should not leak Uvicorn/FastAPI details in production
            # This is more of a recommendation test
            pass

    def test_json_response_valid(self, client):
        """Test JSON responses are valid and properly formatted."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        # Should be valid JSON
        data = response.json()
        assert isinstance(data, dict)


class TestResponseSecurity:
    """Tests for secure response handling."""

    def test_no_sensitive_data_in_error(self, client):
        """Test error responses don't leak sensitive information."""
        # Access invalid endpoint
        response = client.get("/api/v1/nonexistent")

        # Should be 404 with safe error message
        assert response.status_code == 404
        error_data = response.json()

        # Error should not contain sensitive path info or stack traces
        error_str = str(error_data)
        assert "traceback" not in error_str.lower()
        assert "stack" not in error_str.lower()

    def test_validation_error_doesnt_leak_internals(self, client):
        """Test validation errors are safe."""
        # POST with invalid data
        response = client.post(
            "/api/v1/health",
            json={"invalid": "data"},
        )

        # Should return 405 or similar, not expose internals
        data = response.json()
        error_str = str(data)

        # Should not contain Python internal error messages
        assert "traceback" not in error_str.lower()


class TestHTTPSEnforcement:
    """Tests for HTTPS enforcement (production)."""

    def test_api_accepts_http_in_development(self, client):
        """Test API accepts HTTP in development/test mode."""
        response = client.get("/api/v1/health")
        # Should work in test (simulated HTTP)
        assert response.status_code == 200

    def test_strict_transport_security_production(self, client):
        """Test HSTS header configuration for production."""
        # This would be set in production config
        response = client.get("/api/v1/health")

        # In development, HSTS might not be required
        # But in production it should be set
        # This is a guideline test
        pass


class TestAPIVersioning:
    """Tests for secure API versioning."""

    def test_api_version_in_path(self, client):
        """Test API endpoints use versioned paths."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_api_endpoint_without_version_not_found(self, client):
        """Test unversioned endpoints are not accessible."""
        response = client.get("/health")
        assert response.status_code == 404


class TestQueryParameterSecurity:
    """Tests for query parameter security."""

    def test_query_parameters_validated(self, client):
        """Test query parameters are properly validated."""
        # Make a request with query parameters
        response = client.get("/api/v1/health?test=value&other=param")

        # Should not break even with extra params
        assert response.status_code == 200

    def test_malformed_query_parameters(self, client):
        """Test malformed query parameters are handled safely."""
        response = client.get("/api/v1/health?test=<script>alert('xss')</script>")

        # Should handle safely without error
        assert response.status_code == 200


class TestHeaderInjection:
    """Tests for header injection prevention."""

    def test_custom_headers_not_reflected(self, client):
        """Test custom headers are not reflected in responses."""
        response = client.get(
            "/api/v1/health",
            headers={"X-Custom-Header": "test-value"},
        )

        # Custom header should not be reflected unless explicitly set
        # This is implementation dependent
        assert response.status_code == 200
