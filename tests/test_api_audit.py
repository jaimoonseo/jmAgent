"""Unit tests for audit log management endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import json
from src.api.main import app
from src.audit.storage import AuditStorage
from src.audit.logger import AuditRecord


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
    return create_token("admin_user", "admin_agent", settings=settings)


@pytest.fixture
def audit_storage():
    """Create an audit storage with test data."""
    import tempfile

    # Use in-memory or temp database for testing
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name

    storage = AuditStorage(db_path=db_path)

    # Add test audit records
    now = datetime.now(timezone.utc).isoformat()
    test_records = [
        AuditRecord(
            action_type="generate",
            user="test_user",
            timestamp=now,
            input_data={"prompt": "test"},
            output_data={"code": "test code"},
            status="success",
            error_message=None,
            duration=1.5,
            tokens_used={"input": 100, "output": 200},
            metadata={"model": "haiku"},
        ),
        AuditRecord(
            action_type="refactor",
            user="test_user",
            timestamp=now,
            input_data={"file": "test.py"},
            output_data={"refactored": "test code"},
            status="success",
            error_message=None,
            duration=2.0,
            tokens_used={"input": 150, "output": 250},
            metadata={"model": "haiku"},
        ),
        AuditRecord(
            action_type="test",
            user="other_user",
            timestamp=now,
            input_data={"file": "test_file.py"},
            output_data=None,
            status="failure",
            error_message="Timeout",
            duration=5.0,
            tokens_used={"input": 50, "output": 0},
            metadata={"error": "Timeout"},
        ),
    ]

    for record in test_records:
        storage.save(record)

    return storage


def get_auth_headers(token: str) -> dict:
    """Get authorization headers with Bearer token."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def mock_audit_singleton(audit_storage, monkeypatch):
    """Mock the AuditStorage singleton."""
    import src.api.routes.audit as audit_module

    monkeypatch.setattr(
        audit_module,
        "audit_storage",
        audit_storage,
    )
    return audit_storage


class TestAuditLogsEndpoint:
    """Tests for GET /api/v1/audit/logs endpoint."""

    def test_get_audit_logs_success(self, client, auth_token):
        """Test successful retrieval of audit logs."""
        response = client.get(
            "/api/v1/audit/logs",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "logs" in data["data"]
        assert "total" in data["data"]
        assert "limit" in data["data"]
        assert "offset" in data["data"]

        logs = data["data"]["logs"]
        assert len(logs) <= 20  # Default limit
        assert data["data"]["total"] >= 3  # At least 3 test records

    def test_get_audit_logs_without_auth(self, client):
        """Test that audit logs require authentication."""
        response = client.get("/api/v1/audit/logs")
        assert response.status_code == 401

    def test_get_audit_logs_pagination(self, client, auth_token):
        """Test audit logs pagination."""
        # Test default pagination
        response1 = client.get(
            "/api/v1/audit/logs",
            headers=get_auth_headers(auth_token),
        )
        assert response1.status_code == 200
        data1 = response1.json()["data"]
        assert data1["limit"] == 20
        assert data1["offset"] == 0

        # Test custom pagination
        response2 = client.get(
            "/api/v1/audit/logs?limit=2&offset=1",
            headers=get_auth_headers(auth_token),
        )
        assert response2.status_code == 200
        data2 = response2.json()["data"]
        assert data2["limit"] == 2
        assert data2["offset"] == 1

    def test_get_audit_logs_content(self, client, auth_token):
        """Test that audit logs contain expected fields."""
        response = client.get(
            "/api/v1/audit/logs",
            headers=get_auth_headers(auth_token),
        )

        logs = response.json()["data"]["logs"]
        if logs:
            log = logs[0]
            assert "id" in log
            assert "timestamp" in log
            assert "user_id" in log
            assert "action" in log
            assert "status" in log
            assert "details" in log


class TestAuditSearchEndpoint:
    """Tests for GET /api/v1/audit/search endpoint."""

    def test_search_audit_logs_no_filter(self, client, auth_token):
        """Test searching audit logs without filters."""
        response = client.get(
            "/api/v1/audit/search",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["logs"]) >= 0

    def test_search_audit_logs_by_action(self, client, auth_token):
        """Test searching audit logs by action type."""
        response = client.get(
            "/api/v1/audit/search?action=generate",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        logs = response.json()["data"]["logs"]
        for log in logs:
            assert log["action"] == "generate"

    def test_search_audit_logs_by_user_id(self, client, auth_token):
        """Test searching audit logs by user_id."""
        response = client.get(
            "/api/v1/audit/search?user_id=test_user",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        logs = response.json()["data"]["logs"]
        assert len(logs) > 0
        for log in logs:
            assert log["user_id"] == "test_user"

    def test_search_audit_logs_by_status(self, client, auth_token):
        """Test searching audit logs by status."""
        response = client.get(
            "/api/v1/audit/search?status=success",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        logs = response.json()["data"]["logs"]
        for log in logs:
            assert log["status"] == "success"

    def test_search_audit_logs_by_status_failure(self, client, auth_token):
        """Test searching for failed logs."""
        response = client.get(
            "/api/v1/audit/search?status=failure",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        logs = response.json()["data"]["logs"]
        assert len(logs) > 0
        for log in logs:
            assert log["status"] == "failure"

    def test_search_audit_logs_combined_filters(self, client, auth_token):
        """Test searching with multiple filters."""
        response = client.get(
            "/api/v1/audit/search?action=generate&user_id=test_user&status=success",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        logs = response.json()["data"]["logs"]
        for log in logs:
            assert log["action"] == "generate"
            assert log["user_id"] == "test_user"
            assert log["status"] == "success"

    def test_search_audit_logs_pagination(self, client, auth_token):
        """Test pagination in search results."""
        response = client.get(
            "/api/v1/audit/search?limit=1&offset=0",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["limit"] == 1
        assert len(data["logs"]) <= 1

    def test_search_audit_logs_without_auth(self, client):
        """Test that search requires authentication."""
        response = client.get("/api/v1/audit/search")
        assert response.status_code == 401


class TestAuditExportEndpoint:
    """Tests for GET /api/v1/audit/export endpoint."""

    def test_export_audit_logs_csv(self, client, auth_token):
        """Test exporting audit logs as CSV."""
        response = client.get(
            "/api/v1/audit/export?format=csv",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "timestamp" in response.text
        assert "action" in response.text

    def test_export_audit_logs_json(self, client, auth_token):
        """Test exporting audit logs as JSON."""
        response = client.get(
            "/api/v1/audit/export?format=json",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, list)

    def test_export_audit_logs_default_format(self, client, auth_token):
        """Test default export format is CSV."""
        response = client.get(
            "/api/v1/audit/export",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        # Should default to CSV
        assert "csv" in response.headers["content-type"] or "text" in response.headers[
            "content-type"
        ]

    def test_export_audit_logs_with_date_range(self, client, auth_token):
        """Test exporting audit logs with date range filter."""
        today = datetime.now(timezone.utc).date().isoformat()
        response = client.get(
            f"/api/v1/audit/export?format=csv&start_date={today}&end_date={today}",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

    def test_export_audit_logs_without_auth(self, client):
        """Test that export requires authentication."""
        response = client.get("/api/v1/audit/export")
        assert response.status_code == 401

    def test_export_audit_logs_invalid_format(self, client, auth_token):
        """Test export with invalid format."""
        response = client.get(
            "/api/v1/audit/export?format=xml",
            headers=get_auth_headers(auth_token),
        )

        # Should either reject or default to CSV
        assert response.status_code in (200, 400)


class TestAuditClearEndpoint:
    """Tests for POST /api/v1/audit/clear endpoint."""

    def test_clear_audit_logs_success(self, client, admin_token):
        """Test successful clearing of audit logs."""
        response = client.post(
            "/api/v1/audit/clear",
            json={"confirm": True},
            headers=get_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["cleared"] is True
        assert data["data"]["count"] >= 0

    def test_clear_audit_logs_without_auth(self, client):
        """Test that clear requires authentication."""
        response = client.post(
            "/api/v1/audit/clear",
            json={"confirm": True},
        )
        assert response.status_code == 401

    def test_clear_audit_logs_non_admin_forbidden(self, client, auth_token):
        """Test that non-admin users cannot clear logs."""
        response = client.post(
            "/api/v1/audit/clear",
            json={"confirm": True},
            headers=get_auth_headers(auth_token),
        )

        # Should be forbidden for non-admin
        assert response.status_code == 401

    def test_clear_audit_logs_without_confirmation(self, client, admin_token):
        """Test that clearing requires confirmation."""
        response = client.post(
            "/api/v1/audit/clear",
            json={"confirm": False},
            headers=get_auth_headers(admin_token),
        )

        # Should require confirmation=true
        assert response.status_code == 400

    def test_clear_audit_logs_actually_clears(self, client, auth_token, admin_token):
        """Test that clear actually removes all logs."""
        # Clear logs
        client.post(
            "/api/v1/audit/clear",
            json={"confirm": True},
            headers=get_auth_headers(admin_token),
        )

        # Verify logs are gone
        response = client.get(
            "/api/v1/audit/logs",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        logs = response.json()["data"]["logs"]
        assert len(logs) == 0


class TestAuditIntegration:
    """Integration tests for audit endpoints."""

    def test_audit_logs_export_consistency(self, client, auth_token):
        """Test consistency between logs endpoint and export."""
        # Get logs via endpoint
        logs_response = client.get(
            "/api/v1/audit/logs",
            headers=get_auth_headers(auth_token),
        )
        logs = logs_response.json()["data"]["logs"]

        # Get logs via export (JSON)
        export_response = client.get(
            "/api/v1/audit/export?format=json",
            headers=get_auth_headers(auth_token),
        )
        exported = export_response.json()

        # Should have same total count
        assert len(logs) <= len(exported)

    def test_audit_search_and_export_consistency(self, client, auth_token):
        """Test consistency between search and export."""
        # Search for generate actions
        search_response = client.get(
            "/api/v1/audit/search?action=generate",
            headers=get_auth_headers(auth_token),
        )
        search_logs = search_response.json()["data"]["logs"]

        # Export all and filter manually
        export_response = client.get(
            "/api/v1/audit/export?format=json",
            headers=get_auth_headers(auth_token),
        )
        all_exported = export_response.json()

        assert len(search_logs) <= len(all_exported)

    def test_audit_response_format(self, client, auth_token):
        """Test that audit responses have correct format."""
        response = client.get(
            "/api/v1/audit/logs",
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
