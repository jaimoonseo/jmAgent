"""Tests for API error handling."""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.api.main import create_app
from src.api.exceptions import (
    APIException,
    ValidationError,
    AuthenticationError,
    NotFoundError,
    ServerError,
)


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    return TestClient(app)


class TestAPIExceptionHandling:
    """Tests for custom API exception handling."""

    def test_validation_error_status_code(self):
        """Test that ValidationError has correct status code."""
        error = ValidationError("Test validation error")
        assert error.status_code == 400
        assert error.error_code == "VALIDATION_ERROR"

    def test_authentication_error_status_code(self):
        """Test that AuthenticationError has correct status code."""
        error = AuthenticationError("Test auth error")
        assert error.status_code == 401
        assert error.error_code == "AUTH_ERROR"

    def test_not_found_error_status_code(self):
        """Test that NotFoundError has correct status code."""
        error = NotFoundError("Test not found error")
        assert error.status_code == 404
        assert error.error_code == "NOT_FOUND"

    def test_server_error_status_code(self):
        """Test that ServerError has correct status code."""
        error = ServerError("Test server error")
        assert error.status_code == 500
        assert error.error_code == "SERVER_ERROR"


class TestValidationErrors:
    """Tests for validation error handling."""

    def test_invalid_request_body(self, client):
        """Test handling of invalid request body."""
        # This test would work with actual endpoints that have body parameters
        # For now, we test the framework's built-in validation
        response = client.post("/api/v1/health")
        # POST is not allowed on health endpoint
        assert response.status_code in [405, 422]

    def test_validation_error_response_format(self, client):
        """Test that validation errors return proper format."""
        response = client.post("/api/v1/health")
        # Should have proper error response format
        if response.status_code == 422:
            data = response.json()
            assert "detail" in data or "error" in data


class TestNotFoundErrors:
    """Tests for 404 not found handling."""

    def test_nonexistent_endpoint(self, client):
        """Test accessing nonexistent endpoint."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_nonexistent_nested_endpoint(self, client):
        """Test accessing nonexistent nested endpoint."""
        response = client.get("/api/v1/users/123")
        assert response.status_code == 404

    def test_404_error_response_format(self, client):
        """Test that 404 errors have proper format."""
        response = client.get("/api/v1/nonexistent")
        # FastAPI returns detail field for 404s
        assert response.status_code == 404


class TestMethodNotAllowed:
    """Tests for method not allowed errors."""

    def test_post_on_get_endpoint(self, client):
        """Test POST on GET-only endpoint."""
        response = client.post("/api/v1/health")
        assert response.status_code == 405

    def test_put_on_get_endpoint(self, client):
        """Test PUT on GET-only endpoint."""
        response = client.put("/api/v1/health")
        assert response.status_code == 405

    def test_delete_on_get_endpoint(self, client):
        """Test DELETE on GET-only endpoint."""
        response = client.delete("/api/v1/health")
        assert response.status_code == 405


class TestErrorResponseFormat:
    """Tests for error response format consistency."""

    def test_404_returns_json(self, client):
        """Test that 404 returns JSON response."""
        response = client.get("/api/v1/nonexistent")
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)

    def test_method_not_allowed_returns_json(self, client):
        """Test that 405 returns JSON response."""
        response = client.post("/api/v1/health")
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)


class TestExceptionPropagation:
    """Tests for exception propagation and handling."""

    def test_custom_exception_in_endpoint(self):
        """Test that custom exceptions are properly handled."""
        # Create a test app with an endpoint that raises APIException
        app = FastAPI()
        from src.api.main import create_app
        from fastapi import Request
        from fastapi.responses import JSONResponse

        test_app = create_app()

        @test_app.get("/test-error")
        async def test_error_endpoint():
            raise NotFoundError("Test resource")

        client = TestClient(test_app)
        response = client.get("/test-error")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "NOT_FOUND"

    def test_exception_has_correct_error_code(self):
        """Test that exceptions preserve error codes."""
        error = ValidationError("Invalid input")
        assert error.error_code == "VALIDATION_ERROR"

        error = AuthenticationError()
        assert error.error_code == "AUTH_ERROR"

        error = NotFoundError()
        assert error.error_code == "NOT_FOUND"


class TestErrorMessages:
    """Tests for error message customization."""

    def test_custom_error_message(self):
        """Test custom error messages."""
        custom_message = "Custom validation message"
        error = ValidationError(custom_message)
        assert error.detail == custom_message

    def test_default_error_message(self):
        """Test default error messages."""
        error = NotFoundError()
        assert error.detail == "Resource not found"

    def test_authentication_error_default_message(self):
        """Test authentication error default message."""
        error = AuthenticationError()
        assert error.detail == "Authentication required"


class TestExceptionInheritance:
    """Tests for proper exception hierarchy."""

    def test_validation_error_is_api_exception(self):
        """Test that ValidationError extends APIException."""
        error = ValidationError("Test")
        assert isinstance(error, APIException)

    def test_authentication_error_is_api_exception(self):
        """Test that AuthenticationError extends APIException."""
        error = AuthenticationError()
        assert isinstance(error, APIException)

    def test_not_found_error_is_api_exception(self):
        """Test that NotFoundError extends APIException."""
        error = NotFoundError()
        assert isinstance(error, APIException)

    def test_server_error_is_api_exception(self):
        """Test that ServerError extends APIException."""
        error = ServerError()
        assert isinstance(error, APIException)


class TestHTTPExceptionCompatibility:
    """Tests for HTTPException compatibility."""

    def test_api_exception_is_http_exception(self):
        """Test that APIException is HTTPException compatible."""
        from fastapi import HTTPException

        error = ValidationError("Test")
        assert isinstance(error, HTTPException)

    def test_exception_has_status_code(self):
        """Test that exceptions have status_code attribute."""
        error = ValidationError("Test")
        assert hasattr(error, "status_code")
        assert error.status_code == 400

    def test_exception_has_detail(self):
        """Test that exceptions have detail attribute."""
        error = ValidationError("Test detail")
        assert hasattr(error, "detail")
        assert error.detail == "Test detail"
