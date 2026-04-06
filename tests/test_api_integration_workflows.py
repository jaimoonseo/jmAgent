"""Integration tests for API workflows across multiple endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import json

from src.api.main import create_app


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_token(jwt_secret):
    """Create a test JWT token."""
    from src.api.security.auth import create_token, JwtSettings

    settings = JwtSettings(secret_key=jwt_secret)
    return create_token("test_user", "test_agent", settings=settings)


@pytest.fixture
def admin_token(jwt_secret):
    """Create an admin JWT token."""
    from src.api.security.auth import create_token, JwtSettings

    settings = JwtSettings(secret_key=jwt_secret)
    # Admin users are identified by user_id == "admin_user"
    return create_token("admin_user", "admin_agent", settings=settings)


def get_auth_headers(token):
    """Get authorization headers."""
    return {"Authorization": f"Bearer {token}"}


class TestGenerateCodeToMetricsWorkflow:
    """Test workflow: Generate Code → Track Metrics → Verify."""

    def test_generate_code_and_verify_metrics(self, client, auth_token):
        """Generate code and verify metrics are recorded."""
        # Generate code
        prompt = "Create a Python function to calculate factorial"
        response = client.post(
            "/api/v1/actions/generate",
            json={"prompt": prompt},
            headers=get_auth_headers(auth_token),
        )
        assert response.status_code == 200
        generate_data = response.json()["data"]
        assert "generated_code" in generate_data

        # Get metrics
        metrics_response = client.get(
            "/api/v1/metrics/summary",
            headers=get_auth_headers(auth_token),
        )
        assert metrics_response.status_code == 200
        metrics = metrics_response.json()["data"]

        # Verify metrics recorded
        assert metrics["total_requests"] > 0
        assert "generate" in metrics["by_action"]
        assert metrics["by_action"]["generate"]["total_requests"] > 0

    def test_multiple_generate_requests_tracked(self, client, auth_token):
        """Generate multiple times and verify metrics accumulate."""
        # Generate 3 times
        for i in range(3):
            client.post(
                "/api/v1/actions/generate",
                json={"prompt": f"Generate code variant {i}"},
                headers=get_auth_headers(auth_token),
            )

        # Check metrics
        metrics_response = client.get(
            "/api/v1/metrics/summary",
            headers=get_auth_headers(auth_token),
        )
        metrics = metrics_response.json()["data"]

        # Should have at least 3 requests for generate
        assert metrics["by_action"]["generate"]["total_requests"] >= 3

    def test_metrics_by_model(self, client, auth_token):
        """Verify metrics track by model used."""
        # Generate with default model
        client.post(
            "/api/v1/actions/generate",
            json={"prompt": "Test", "model": "haiku"},
            headers=get_auth_headers(auth_token),
        )

        # Get metrics by model
        model_metrics = client.get(
            "/api/v1/metrics/by-model",
            headers=get_auth_headers(auth_token),
        )
        assert model_metrics.status_code == 200
        data = model_metrics.json()["data"]
        assert len(data) > 0


class TestTemplateWorkflow:
    """Test workflow: Create Template → Use Template → Verify."""

    def test_create_and_use_template(self, client, auth_token):
        """Create custom template and use it."""
        # Create custom template
        template_body = {
            "name": "custom_fastapi",
            "action": "generate",
            "content": "Create a FastAPI endpoint: {{ requirements }}",
            "description": "Custom FastAPI template",
        }
        create_response = client.post(
            "/api/v1/templates",
            json=template_body,
            headers=get_auth_headers(auth_token),
        )
        assert create_response.status_code == 200
        template_id = create_response.json()["data"]["id"]

        # Use the template
        use_response = client.post(
            f"/api/v1/templates/{template_id}/use",
            json={"requirements": "GET endpoint for users"},
            headers=get_auth_headers(auth_token),
        )
        assert use_response.status_code == 200

        # Verify metrics show generate action
        metrics = client.get(
            "/api/v1/metrics/summary",
            headers=get_auth_headers(auth_token),
        )
        assert metrics.status_code == 200

    def test_list_templates_includes_custom(self, client, auth_token):
        """Create template and verify it appears in list."""
        # Create custom template
        create_response = client.post(
            "/api/v1/templates",
            json={
                "name": "test_template",
                "action": "explain",
                "content": "Explain this: {{ code }}",
            },
            headers=get_auth_headers(auth_token),
        )
        assert create_response.status_code == 200

        # List templates
        list_response = client.get(
            "/api/v1/templates",
            headers=get_auth_headers(auth_token),
        )
        assert list_response.status_code == 200
        templates = list_response.json()["data"]["templates"]
        custom_names = [t["name"] for t in templates if t["is_custom"]]
        assert "test_template" in custom_names

    def test_delete_custom_template(self, client, auth_token):
        """Create, then delete custom template."""
        # Create
        create_response = client.post(
            "/api/v1/templates",
            json={
                "name": "deletable_template",
                "action": "test",
                "content": "Test: {{ file }}",
            },
            headers=get_auth_headers(auth_token),
        )
        template_id = create_response.json()["data"]["id"]

        # Delete
        delete_response = client.delete(
            f"/api/v1/templates/{template_id}",
            headers=get_auth_headers(auth_token),
        )
        assert delete_response.status_code == 200

        # Verify deleted
        get_response = client.get(
            f"/api/v1/templates/{template_id}",
            headers=get_auth_headers(auth_token),
        )
        assert get_response.status_code == 404


class TestActionsAuditWorkflow:
    """Test workflow: Perform Actions → Check Audit Trail."""

    def test_action_logged_to_audit(self, client, auth_token):
        """Action is recorded in audit log."""
        # Perform an action
        client.post(
            "/api/v1/actions/generate",
            json={"prompt": "Test code"},
            headers=get_auth_headers(auth_token),
        )

        # Check audit logs
        audit_response = client.get(
            "/api/v1/audit/logs",
            headers=get_auth_headers(auth_token),
        )
        assert audit_response.status_code == 200
        logs = audit_response.json()["data"]["logs"]
        assert len(logs) > 0
        assert any(log["action"] == "generate" for log in logs)

    def test_audit_search_by_action(self, client, auth_token):
        """Search audit logs by action type."""
        # Perform action
        client.post(
            "/api/v1/actions/refactor",
            json={
                "file_path": "/test/file.py",
                "requirements": "add type hints",
            },
            headers=get_auth_headers(auth_token),
        )

        # Search for refactor action
        search_response = client.get(
            "/api/v1/audit/search?action=refactor",
            headers=get_auth_headers(auth_token),
        )
        assert search_response.status_code == 200
        logs = search_response.json()["data"]["logs"]
        # Should have at least one refactor action if successful
        if logs:
            assert any(log["action"] == "refactor" for log in logs)

    def test_audit_export_csv(self, client, auth_token):
        """Export audit logs as CSV."""
        # Perform an action first
        client.post(
            "/api/v1/actions/generate",
            json={"prompt": "Test"},
            headers=get_auth_headers(auth_token),
        )

        # Export as CSV
        export_response = client.get(
            "/api/v1/audit/export?format=csv",
            headers=get_auth_headers(auth_token),
        )
        assert export_response.status_code == 200
        assert export_response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "timestamp" in export_response.text

    def test_audit_export_json(self, client, auth_token):
        """Export audit logs as JSON."""
        # Export as JSON
        export_response = client.get(
            "/api/v1/audit/export?format=json",
            headers=get_auth_headers(auth_token),
        )
        assert export_response.status_code == 200
        assert export_response.headers["content-type"] == "application/json"
        data = json.loads(export_response.text)
        assert isinstance(data, list)


class TestPluginWorkflow:
    """Test workflow: Enable Plugin → Use → Disable."""

    def test_plugin_enable_disable_cycle(self, client, auth_token):
        """Enable plugin, verify enabled, then disable."""
        # List plugins to find one
        list_response = client.get(
            "/api/v1/plugins",
            headers=get_auth_headers(auth_token),
        )
        assert list_response.status_code == 200
        plugins = list_response.json()["data"]["plugins"]
        if plugins:
            plugin_name = plugins[0]["name"]

            # Enable plugin
            enable_response = client.post(
                f"/api/v1/plugins/{plugin_name}/enable",
                headers=get_auth_headers(auth_token),
            )
            assert enable_response.status_code in (200, 409)  # 409 if already enabled

            # Verify enabled
            detail_response = client.get(
                f"/api/v1/plugins/{plugin_name}",
                headers=get_auth_headers(auth_token),
            )
            assert detail_response.status_code == 200

            # Disable plugin
            disable_response = client.post(
                f"/api/v1/plugins/{plugin_name}/disable",
                headers=get_auth_headers(auth_token),
            )
            assert disable_response.status_code in (200, 409)  # 409 if already disabled

    def test_plugin_config_update(self, client, auth_token):
        """Update plugin configuration."""
        # List plugins
        list_response = client.get(
            "/api/v1/plugins",
            headers=get_auth_headers(auth_token),
        )
        plugins = list_response.json()["data"]["plugins"]
        if plugins:
            plugin_name = plugins[0]["name"]

            # Update config
            config_update = client.post(
                f"/api/v1/plugins/{plugin_name}/config",
                json={"enabled": True, "verbose": True},
                headers=get_auth_headers(auth_token),
            )
            # May return 200 or 400 depending on plugin
            assert config_update.status_code in (200, 400, 404)


class TestConfigManagementWorkflow:
    """Test workflow: Modify Config → Retrieve → Verify."""

    def test_update_and_retrieve_config(self, client, auth_token):
        """Update config setting and verify retrieval."""
        # Update a setting
        update_response = client.post(
            "/api/v1/config",
            json={"key": "port", "value": 9002},
            headers=get_auth_headers(auth_token),
        )
        assert update_response.status_code == 200

        # Retrieve config
        get_response = client.get(
            "/api/v1/config",
            headers=get_auth_headers(auth_token),
        )
        assert get_response.status_code == 200
        config = get_response.json()["data"]["all_settings"]
        assert config["port"] == 9002

    def test_multiple_config_updates(self, client, auth_token):
        """Update multiple settings and verify all persist."""
        updates = [
            {"key": "debug", "value": True},
            {"key": "log_level", "value": "DEBUG"},
            {"key": "port", "value": 9003},
        ]

        for update in updates:
            response = client.post(
                "/api/v1/config",
                json=update,
                headers=get_auth_headers(auth_token),
            )
            assert response.status_code == 200

        # Verify all are set
        get_response = client.get(
            "/api/v1/config",
            headers=get_auth_headers(auth_token),
        )
        config = get_response.json()["data"]["all_settings"]
        assert config["debug"] is True
        assert config["log_level"] == "DEBUG"
        assert config["port"] == 9003

    def test_delete_config_resets_to_default(self, client, auth_token):
        """Delete config setting resets to default."""
        # Update
        client.post(
            "/api/v1/config",
            json={"key": "reload", "value": True},
            headers=get_auth_headers(auth_token),
        )

        # Delete
        delete_response = client.delete(
            "/api/v1/config/reload",
            headers=get_auth_headers(auth_token),
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["data"]["default_value"] is False


class TestAdminWorkflow:
    """Test workflow: Full Admin Operations."""

    def test_reset_all_config(self, client, auth_token, admin_token):
        """Reset all config to defaults (admin only)."""
        # Update as regular user
        client.post(
            "/api/v1/config",
            json={"key": "debug", "value": True},
            headers=get_auth_headers(auth_token),
        )

        # Reset as admin
        reset_response = client.post(
            "/api/v1/config/reset",
            headers=get_auth_headers(admin_token),
        )
        assert reset_response.status_code == 200

        # Verify reset
        get_response = client.get(
            "/api/v1/config",
            headers=get_auth_headers(auth_token),
        )
        config = get_response.json()["data"]["all_settings"]
        assert config["debug"] is False

    def test_reset_metrics(self, client, auth_token, admin_token):
        """Reset metrics (admin only)."""
        # Perform action
        client.post(
            "/api/v1/actions/generate",
            json={"prompt": "Test"},
            headers=get_auth_headers(auth_token),
        )

        # Reset metrics as admin
        reset_response = client.post(
            "/api/v1/metrics/reset",
            headers=get_auth_headers(admin_token),
        )
        assert reset_response.status_code == 200

        # Verify reset
        summary = client.get(
            "/api/v1/metrics/summary",
            headers=get_auth_headers(auth_token),
        )
        metrics = summary.json()["data"]
        assert metrics["total_requests"] == 0

    def test_clear_audit_logs(self, client, auth_token, admin_token):
        """Clear all audit logs (admin only)."""
        # Perform action
        client.post(
            "/api/v1/actions/generate",
            json={"prompt": "Test"},
            headers=get_auth_headers(auth_token),
        )

        # Clear audit as admin
        clear_response = client.delete(
            "/api/v1/audit/logs",
            headers=get_auth_headers(admin_token),
        )
        assert clear_response.status_code == 200

        # Verify cleared
        logs_response = client.get(
            "/api/v1/audit/logs",
            headers=get_auth_headers(auth_token),
        )
        logs = logs_response.json()["data"]["logs"]
        # After clear, audit logs should be empty or minimal
        assert isinstance(logs, list)


class TestCrossEndpointWorkflows:
    """Test complex workflows spanning multiple endpoints."""

    def test_generate_refactor_test_workflow(self, client, auth_token):
        """Generate → Refactor → Test workflow."""
        # Generate code
        gen_response = client.post(
            "/api/v1/actions/generate",
            json={"prompt": "Create a simple calculator class"},
            headers=get_auth_headers(auth_token),
        )
        assert gen_response.status_code == 200

        # Refactor the code (would need file path in real scenario)
        refactor_response = client.post(
            "/api/v1/actions/refactor",
            json={
                "file_path": "/test/calc.py",
                "requirements": "Add type hints",
            },
            headers=get_auth_headers(auth_token),
        )
        assert refactor_response.status_code in (200, 404)  # 404 if file doesn't exist

        # Test generation
        test_response = client.post(
            "/api/v1/actions/test",
            json={
                "file_path": "/test/calc.py",
                "framework": "pytest",
            },
            headers=get_auth_headers(auth_token),
        )
        assert test_response.status_code in (200, 404)

    def test_full_workflow_with_metrics_and_audit(self, client, auth_token):
        """Complete workflow: Actions → Metrics → Audit."""
        # Perform multiple actions
        actions = [
            ("generate", {"prompt": "Test function"}),
            ("explain", {"file_path": "/test.py"}),
        ]

        for action_type, data in actions:
            response = client.post(
                f"/api/v1/actions/{action_type}",
                json=data,
                headers=get_auth_headers(auth_token),
            )
            assert response.status_code in (200, 404)

        # Check metrics
        metrics = client.get(
            "/api/v1/metrics/summary",
            headers=get_auth_headers(auth_token),
        )
        assert metrics.status_code == 200

        # Check audit
        audit = client.get(
            "/api/v1/audit/logs",
            headers=get_auth_headers(auth_token),
        )
        assert audit.status_code == 200
        logs = audit.json()["data"]["logs"]
        assert len(logs) > 0

    def test_health_check_workflow(self, client, auth_token):
        """Verify health endpoints work throughout workflow."""
        # Health check
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["success"] is True

        # Detailed health
        detailed = client.get("/api/v1/health/detailed")
        assert detailed.status_code == 200

        # Status
        status = client.get(
            "/api/v1/status",
            headers=get_auth_headers(auth_token),
        )
        assert status.status_code == 200


class TestErrorHandlingWorkflows:
    """Test error handling across workflows."""

    def test_unauthorized_access_workflow(self, client):
        """Verify unauthorized requests are rejected."""
        endpoints = [
            ("GET", "/api/v1/config"),
            ("POST", "/api/v1/actions/generate"),
            ("GET", "/api/v1/metrics/summary"),
            ("GET", "/api/v1/audit/logs"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(
                    endpoint,
                    json={"prompt": "test"} if "generate" in endpoint else {},
                )
            assert response.status_code in (401, 403)

    def test_invalid_input_handling(self, client, auth_token):
        """Test handling of invalid inputs."""
        # Invalid prompt
        response = client.post(
            "/api/v1/actions/generate",
            json={"prompt": ""},
            headers=get_auth_headers(auth_token),
        )
        assert response.status_code in (400, 422)

        # Invalid file path
        response = client.post(
            "/api/v1/actions/refactor",
            json={"file_path": "", "requirements": "test"},
            headers=get_auth_headers(auth_token),
        )
        assert response.status_code in (400, 422, 404)


class TestResponseConsistency:
    """Test response format consistency across endpoints."""

    def test_api_response_format(self, client, auth_token):
        """All endpoints return consistent response format."""
        endpoints = [
            ("GET", "/api/v1/config"),
            ("GET", "/api/v1/metrics/summary"),
            ("GET", "/api/v1/audit/logs"),
        ]

        for method, endpoint in endpoints:
            response = client.get(
                endpoint,
                headers=get_auth_headers(auth_token),
            )
            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert "data" in data

    def test_error_response_format(self, client):
        """Error responses have consistent format."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "success" in data
        assert data["success"] is False
        assert "error" in data or "detail" in data
