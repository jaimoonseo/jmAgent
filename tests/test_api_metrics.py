"""Unit tests for metrics management endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime
from src.api.main import app
from src.monitoring.metrics import MetricsCollector


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
def metrics_collector():
    """Create a metrics collector with test data."""
    collector = MetricsCollector()
    # Add some test metrics
    collector.record_metric(
        action_type="generate",
        response_time=1.5,
        input_tokens=100,
        output_tokens=200,
        success=True,
    )
    collector.record_metric(
        action_type="generate",
        response_time=2.0,
        input_tokens=150,
        output_tokens=250,
        success=True,
    )
    collector.record_metric(
        action_type="refactor",
        response_time=1.2,
        input_tokens=200,
        output_tokens=150,
        success=True,
    )
    collector.record_metric(
        action_type="test",
        response_time=0.8,
        input_tokens=50,
        output_tokens=300,
        success=False,
        error="Timeout",
    )
    return collector


def get_auth_headers(token: str) -> dict:
    """Get authorization headers with Bearer token."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def mock_metrics_singleton(metrics_collector, monkeypatch):
    """Mock the MetricsCollector singleton."""
    import src.api.routes.metrics as metrics_module

    monkeypatch.setattr(
        metrics_module,
        "metrics_collector",
        metrics_collector,
    )
    return metrics_collector


class TestMetricsSummaryEndpoint:
    """Tests for GET /api/v1/metrics/summary endpoint."""

    def test_get_metrics_summary_success(self, client, auth_token):
        """Test successful retrieval of metrics summary."""
        response = client.get(
            "/api/v1/metrics/summary",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        summary = data["data"]

        assert "total_requests" in summary
        assert "avg_response_time" in summary
        assert "total_tokens_used" in summary
        assert "success_rate" in summary
        assert "last_updated" in summary

        assert summary["total_requests"] == 4
        assert summary["success_rate"] == 0.75  # 3 successes out of 4
        assert isinstance(summary["total_tokens_used"], int)

    def test_get_metrics_summary_without_auth(self, client):
        """Test that metrics summary requires authentication."""
        response = client.get("/api/v1/metrics/summary")
        assert response.status_code == 401

    def test_get_metrics_summary_with_empty_metrics(self, client, auth_token):
        """Test metrics summary with no metrics recorded."""
        # Clear metrics
        from src.api.routes import metrics as metrics_module

        metrics_module.metrics_collector.clear()

        response = client.get(
            "/api/v1/metrics/summary",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        summary = data["data"]
        assert summary["total_requests"] == 0


class TestMetricsByActionEndpoint:
    """Tests for GET /api/v1/metrics/by-action endpoint."""

    def test_get_metrics_by_action_success(self, client, auth_token):
        """Test successful retrieval of per-action metrics."""
        response = client.get(
            "/api/v1/metrics/by-action",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "actions" in data["data"]

        actions = data["data"]["actions"]
        assert "generate" in actions
        assert "refactor" in actions
        assert "test" in actions

        # Check generate metrics
        generate = actions["generate"]
        assert generate["count"] == 2
        assert generate["success_count"] == 2
        assert generate["failure_count"] == 0
        assert generate["success_rate"] == 1.0
        assert "avg_response_time" in generate
        assert "total_tokens" in generate

    def test_get_metrics_by_action_without_auth(self, client):
        """Test that endpoint requires authentication."""
        response = client.get("/api/v1/metrics/by-action")
        assert response.status_code == 401

    def test_get_metrics_by_action_includes_all_actions(self, client, auth_token):
        """Test that all action types are included."""
        response = client.get(
            "/api/v1/metrics/by-action",
            headers=get_auth_headers(auth_token),
        )

        actions = response.json()["data"]["actions"]
        assert len(actions) >= 3  # At least generate, refactor, test


class TestMetricsCostEndpoint:
    """Tests for GET /api/v1/metrics/cost endpoint."""

    def test_get_metrics_cost_success(self, client, auth_token):
        """Test successful retrieval of cost estimation."""
        response = client.get(
            "/api/v1/metrics/cost",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_cost" in data["data"]
        assert "by_action" in data["data"]

        cost_data = data["data"]
        assert isinstance(cost_data["total_cost"], (int, float))
        assert cost_data["total_cost"] >= 0
        assert isinstance(cost_data["by_action"], dict)

    def test_get_metrics_cost_without_auth(self, client):
        """Test that cost endpoint requires authentication."""
        response = client.get("/api/v1/metrics/cost")
        assert response.status_code == 401

    def test_get_metrics_cost_calculation(self, client, auth_token):
        """Test that cost is calculated based on tokens."""
        response = client.get(
            "/api/v1/metrics/cost",
            headers=get_auth_headers(auth_token),
        )

        cost_data = response.json()["data"]
        # Cost should be proportional to tokens used
        # Haiku: 0.08/1M input, 0.24/1M output
        assert cost_data["total_cost"] > 0


class TestMetricsHistoryEndpoint:
    """Tests for GET /api/v1/metrics/history endpoint."""

    def test_get_metrics_history_success(self, client, auth_token):
        """Test successful retrieval of metrics history."""
        response = client.get(
            "/api/v1/metrics/history",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "metrics" in data["data"]
        assert "total" in data["data"]
        assert "limit" in data["data"]
        assert "offset" in data["data"]

        metrics = data["data"]["metrics"]
        assert len(metrics) <= 20  # Default limit

    def test_get_metrics_history_pagination(self, client, auth_token):
        """Test metrics history pagination."""
        # Default limit=20, offset=0
        response1 = client.get(
            "/api/v1/metrics/history",
            headers=get_auth_headers(auth_token),
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["data"]["limit"] == 20
        assert data1["data"]["offset"] == 0

        # Custom pagination
        response2 = client.get(
            "/api/v1/metrics/history?limit=2&offset=1",
            headers=get_auth_headers(auth_token),
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["data"]["limit"] == 2
        assert data2["data"]["offset"] == 1

    def test_get_metrics_history_limit_validation(self, client, auth_token):
        """Test that limit parameter is validated."""
        # Limit > 100 should be capped
        response = client.get(
            "/api/v1/metrics/history?limit=150",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["limit"] <= 100  # Max limit

    def test_get_metrics_history_without_auth(self, client):
        """Test that history endpoint requires authentication."""
        response = client.get("/api/v1/metrics/history")
        assert response.status_code == 401

    def test_get_metrics_history_content(self, client, auth_token):
        """Test that history contains expected fields."""
        response = client.get(
            "/api/v1/metrics/history",
            headers=get_auth_headers(auth_token),
        )

        metrics = response.json()["data"]["metrics"]
        if metrics:
            metric = metrics[0]
            assert "timestamp" in metric
            assert "action_type" in metric
            assert "response_time" in metric
            assert "input_tokens" in metric
            assert "output_tokens" in metric
            assert "total_tokens" in metric
            assert "success" in metric


class TestResetMetricsEndpoint:
    """Tests for POST /api/v1/metrics/reset endpoint."""

    def test_reset_metrics_success(self, client, auth_token):
        """Test successful reset of all metrics."""
        response = client.post(
            "/api/v1/metrics/reset",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["reset"] is True
        assert data["data"]["cleared_count"] > 0

    def test_reset_metrics_without_auth(self, client):
        """Test that reset requires authentication."""
        response = client.post("/api/v1/metrics/reset")
        assert response.status_code == 401

    def test_reset_metrics_clears_data(self, client, auth_token):
        """Test that reset actually clears metrics."""
        # Reset metrics
        reset_response = client.post(
            "/api/v1/metrics/reset",
            headers=get_auth_headers(auth_token),
        )
        assert reset_response.status_code == 200

        # Check that summary shows zero requests
        summary_response = client.get(
            "/api/v1/metrics/summary",
            headers=get_auth_headers(auth_token),
        )
        assert summary_response.status_code == 200
        summary = summary_response.json()["data"]
        assert summary["total_requests"] == 0


class TestMetricsIntegration:
    """Integration tests for metrics endpoints."""

    def test_metrics_consistency(self, client, auth_token):
        """Test consistency between different metrics endpoints."""
        # Get summary
        summary_response = client.get(
            "/api/v1/metrics/summary",
            headers=get_auth_headers(auth_token),
        )
        summary = summary_response.json()["data"]

        # Get by-action
        by_action_response = client.get(
            "/api/v1/metrics/by-action",
            headers=get_auth_headers(auth_token),
        )
        by_action = by_action_response.json()["data"]

        # Get history
        history_response = client.get(
            "/api/v1/metrics/history",
            headers=get_auth_headers(auth_token),
        )
        history = history_response.json()["data"]

        # Verify consistency
        total_from_actions = sum(a["count"] for a in by_action["actions"].values())
        assert summary["total_requests"] == total_from_actions
        assert history["total"] == summary["total_requests"]

    def test_metrics_response_format(self, client, auth_token):
        """Test that metrics responses have correct format."""
        response = client.get(
            "/api/v1/metrics/summary",
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
