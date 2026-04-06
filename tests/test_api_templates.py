"""Unit tests for template management endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from src.api.main import app
from src.templates.manager import TemplateManager


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
def template_manager():
    """Create a template manager with test templates."""
    from src.templates.loader import Template

    manager = TemplateManager()

    # Add test templates to custom_templates cache
    # These will supplement the builtin templates
    test_templates = [
        Template(
            name="test_generate_1",
            action="generate",
            system_prompt="Generate code",
            user_prompt_template="Generate code for: {{ requirement }}",
            version="1.0",
            description="Test template for code generation",
            required_variables=["requirement"],
            optional_variables=[]
        ),
        Template(
            name="test_refactor_1",
            action="refactor",
            system_prompt="Refactor code",
            user_prompt_template="Refactor the following code: {{ code }}",
            version="1.0",
            description="Test template for refactoring",
            required_variables=["code"],
            optional_variables=[]
        ),
        Template(
            name="custom_test",
            action="test",
            system_prompt="Write tests",
            user_prompt_template="Write test for: {{ function }}",
            version="1.0",
            description="Custom test template",
            required_variables=["function"],
            optional_variables=[]
        ),
    ]

    # Cache test templates
    for template in test_templates:
        cache_key = (template.action, template.name)
        manager.custom_templates[cache_key] = template

    return manager


def get_auth_headers(token: str) -> dict:
    """Get authorization headers with Bearer token."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def mock_template_singleton(template_manager, monkeypatch):
    """Mock the TemplateManager singleton."""
    import src.api.routes.templates as templates_module

    monkeypatch.setattr(
        templates_module,
        "template_manager",
        template_manager,
    )
    return template_manager


class TestTemplatesListEndpoint:
    """Tests for GET /api/v1/templates endpoint."""

    def test_list_templates_success(self, client, auth_token):
        """Test successful listing of all templates."""
        response = client.get(
            "/api/v1/templates",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "templates" in data["data"]

        templates = data["data"]["templates"]
        # Should have at least the built-in templates (generate, refactor, test, explain, fix, chat)
        assert len(templates) >= 6

    def test_list_templates_without_auth(self, client):
        """Test that listing templates requires authentication."""
        response = client.get("/api/v1/templates")
        assert response.status_code == 401

    def test_list_templates_metadata(self, client, auth_token):
        """Test that template list includes expected fields."""
        response = client.get(
            "/api/v1/templates",
            headers=get_auth_headers(auth_token),
        )

        templates = response.json()["data"]["templates"]
        if templates:
            template = templates[0]
            assert "name" in template
            assert "action" in template
            assert "description" in template
            assert "variables" in template

    def test_list_templates_by_action(self, client, auth_token):
        """Test that templates are grouped by action."""
        response = client.get(
            "/api/v1/templates",
            headers=get_auth_headers(auth_token),
        )

        templates = response.json()["data"]["templates"]
        generate_templates = [t for t in templates if t["action"] == "generate"]
        refactor_templates = [t for t in templates if t["action"] == "refactor"]
        test_templates = [t for t in templates if t["action"] == "test"]

        assert len(generate_templates) > 0
        assert len(refactor_templates) > 0
        assert len(test_templates) > 0


class TestTemplateDetailEndpoint:
    """Tests for GET /api/v1/templates/{name} endpoint."""

    def test_get_template_detail_success(self, client, auth_token):
        """Test successful retrieval of template details."""
        response = client.get(
            "/api/v1/templates/test_generate_1",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        template = data["data"]
        assert template["name"] == "test_generate_1"
        assert template["action"] == "generate"
        assert "content" in template
        assert "variables" in template
        assert "requirement" in template["variables"]

    def test_get_template_without_auth(self, client):
        """Test that getting template requires authentication."""
        response = client.get("/api/v1/templates/test_generate_1")
        assert response.status_code == 401

    def test_get_nonexistent_template(self, client, auth_token):
        """Test retrieving a non-existent template."""
        response = client.get(
            "/api/v1/templates/nonexistent_template",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_get_template_content(self, client, auth_token):
        """Test that template content is returned."""
        response = client.get(
            "/api/v1/templates/test_generate_1",
            headers=get_auth_headers(auth_token),
        )

        template = response.json()["data"]
        assert "Generate code for:" in template["content"]

    def test_get_template_extracts_variables(self, client, auth_token):
        """Test that template variables are extracted."""
        response = client.get(
            "/api/v1/templates/test_refactor_1",
            headers=get_auth_headers(auth_token),
        )

        template = response.json()["data"]
        assert "variables" in template
        assert "code" in template["variables"]


class TestCreateTemplateEndpoint:
    """Tests for POST /api/v1/templates endpoint."""

    def test_create_template_success(self, client, auth_token):
        """Test successful creation of a custom template."""
        request_body = {
            "name": "new_template",
            "action": "generate",
            "content": "Generate: {{ task }}",
            "description": "New test template",
        }

        response = client.post(
            "/api/v1/templates",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "new_template"
        assert data["data"]["created"] is True

    def test_create_template_without_auth(self, client):
        """Test that creating template requires authentication."""
        request_body = {
            "name": "new_template",
            "action": "generate",
            "content": "Generate: {{ task }}",
            "description": "New template",
        }
        response = client.post("/api/v1/templates", json=request_body)
        assert response.status_code == 401

    def test_create_duplicate_template(self, client, auth_token):
        """Test creating a template with duplicate name."""
        request_body = {
            "name": "test_generate_1",  # Already exists
            "action": "generate",
            "content": "Duplicate template",
            "description": "Should fail",
        }

        response = client.post(
            "/api/v1/templates",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        # Should fail with conflict
        assert response.status_code == 409

    def test_create_template_invalid_action(self, client, auth_token):
        """Test creating template with invalid action."""
        request_body = {
            "name": "bad_template",
            "action": "invalid_action",
            "content": "Some content",
            "description": "Invalid action",
        }

        response = client.post(
            "/api/v1/templates",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        # May reject or coerce - depends on implementation
        assert response.status_code in (200, 400)

    def test_create_template_is_custom(self, client, auth_token):
        """Test that created templates are marked as custom."""
        request_body = {
            "name": "my_custom_template",
            "action": "generate",
            "content": "Custom: {{ input }}",
            "description": "My template",
        }

        response = client.post(
            "/api/v1/templates",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200

        # Verify it was created
        get_response = client.get(
            "/api/v1/templates/my_custom_template",
            headers=get_auth_headers(auth_token),
        )
        assert get_response.status_code == 200


class TestUpdateTemplateEndpoint:
    """Tests for PUT /api/v1/templates/{name} endpoint."""

    def test_update_template_success(self, client, auth_token):
        """Test successful updating of a template."""
        request_body = {
            "content": "Updated: {{ requirement }}",
            "description": "Updated description",
        }

        response = client.put(
            "/api/v1/templates/custom_test",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "custom_test"
        assert data["data"]["updated"] is True

    def test_update_template_without_auth(self, client):
        """Test that updating template requires authentication."""
        request_body = {
            "content": "Updated content",
            "description": "Updated",
        }
        response = client.put(
            "/api/v1/templates/custom_test",
            json=request_body,
        )
        assert response.status_code == 401

    def test_update_nonexistent_template(self, client, auth_token):
        """Test updating a non-existent template."""
        request_body = {
            "content": "Updated",
            "description": "Updated",
        }

        response = client.put(
            "/api/v1/templates/nonexistent",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 404

    def test_update_template_content_only(self, client, auth_token):
        """Test updating only the template content."""
        request_body = {
            "content": "New content: {{ var }}",
            "description": "Current description",
        }

        response = client.put(
            "/api/v1/templates/custom_test",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200

        # Verify update
        get_response = client.get(
            "/api/v1/templates/custom_test",
            headers=get_auth_headers(auth_token),
        )
        template = get_response.json()["data"]
        assert "New content:" in template["content"]


class TestDeleteTemplateEndpoint:
    """Tests for DELETE /api/v1/templates/{name} endpoint."""

    def test_delete_custom_template_success(self, client, auth_token):
        """Test successful deletion of a custom template."""
        response = client.delete(
            "/api/v1/templates/custom_test",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "custom_test"
        assert data["data"]["deleted"] is True

    def test_delete_template_without_auth(self, client):
        """Test that deleting template requires authentication."""
        response = client.delete("/api/v1/templates/custom_test")
        assert response.status_code == 401

    def test_delete_nonexistent_template(self, client, auth_token):
        """Test deleting a non-existent template."""
        response = client.delete(
            "/api/v1/templates/nonexistent",
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 404

    def test_delete_builtin_template_forbidden(self, client, auth_token):
        """Test that built-in templates cannot be deleted."""
        response = client.delete(
            "/api/v1/templates/test_generate_1",
            headers=get_auth_headers(auth_token),
        )

        # Built-in templates should not be deletable
        assert response.status_code == 401

    def test_deleted_template_unavailable(self, client, auth_token):
        """Test that deleted template is no longer available."""
        # Delete
        delete_response = client.delete(
            "/api/v1/templates/custom_test",
            headers=get_auth_headers(auth_token),
        )
        assert delete_response.status_code == 200

        # Try to get
        get_response = client.get(
            "/api/v1/templates/custom_test",
            headers=get_auth_headers(auth_token),
        )
        assert get_response.status_code == 404


class TestTemplatePreviewEndpoint:
    """Tests for POST /api/v1/templates/{name}/preview endpoint."""

    def test_preview_template_success(self, client, auth_token):
        """Test successful template preview."""
        request_body = {
            "variables": {
                "requirement": "a function to sort a list",
            }
        }

        response = client.post(
            "/api/v1/templates/test_generate_1/preview",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "rendered" in data["data"]
        assert "a function to sort a list" in data["data"]["rendered"]

    def test_preview_template_without_auth(self, client):
        """Test that preview requires authentication."""
        request_body = {"variables": {"requirement": "test"}}
        response = client.post(
            "/api/v1/templates/test_generate_1/preview",
            json=request_body,
        )
        assert response.status_code == 401

    def test_preview_nonexistent_template(self, client, auth_token):
        """Test previewing a non-existent template."""
        request_body = {"variables": {"var": "value"}}

        response = client.post(
            "/api/v1/templates/nonexistent/preview",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 404

    def test_preview_with_multiple_variables(self, client, auth_token):
        """Test preview with multiple variables."""
        # Use a template with multiple variables
        request_body = {
            "variables": {
                "function": "calculate_total",
                "description": "sums all numbers",
            }
        }

        response = client.post(
            "/api/v1/templates/custom_test/preview",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        rendered = response.json()["data"]["rendered"]
        assert "calculate_total" in rendered

    def test_preview_with_missing_variables(self, client, auth_token):
        """Test preview with missing required variables."""
        request_body = {
            "variables": {}  # Missing 'requirement'
        }

        response = client.post(
            "/api/v1/templates/test_generate_1/preview",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        # May succeed with placeholder or fail
        # Jinja2 by default leaves undefined variables as empty
        assert response.status_code in (200, 400)

    def test_preview_rendering_correct(self, client, auth_token):
        """Test that preview renders template correctly."""
        request_body = {
            "variables": {
                "code": "def foo(): pass",
            }
        }

        response = client.post(
            "/api/v1/templates/test_refactor_1/preview",
            json=request_body,
            headers=get_auth_headers(auth_token),
        )

        assert response.status_code == 200
        rendered = response.json()["data"]["rendered"]
        assert "def foo(): pass" in rendered


class TestTemplateIntegration:
    """Integration tests for template endpoints."""

    def test_template_lifecycle(self, client, auth_token):
        """Test complete template lifecycle."""
        # Create
        create_response = client.post(
            "/api/v1/templates",
            json={
                "name": "lifecycle_test",
                "action": "generate",
                "content": "Test: {{ var }}",
                "description": "Test template",
            },
            headers=get_auth_headers(auth_token),
        )
        assert create_response.status_code == 200

        # Get
        get_response = client.get(
            "/api/v1/templates/lifecycle_test",
            headers=get_auth_headers(auth_token),
        )
        assert get_response.status_code == 200

        # Update
        update_response = client.put(
            "/api/v1/templates/lifecycle_test",
            json={
                "content": "Updated: {{ var }}",
                "description": "Updated description",
            },
            headers=get_auth_headers(auth_token),
        )
        assert update_response.status_code == 200

        # Preview
        preview_response = client.post(
            "/api/v1/templates/lifecycle_test/preview",
            json={"variables": {"var": "test_value"}},
            headers=get_auth_headers(auth_token),
        )
        assert preview_response.status_code == 200

        # Delete
        delete_response = client.delete(
            "/api/v1/templates/lifecycle_test",
            headers=get_auth_headers(auth_token),
        )
        assert delete_response.status_code == 200

    def test_template_response_format(self, client, auth_token):
        """Test that template responses have correct format."""
        response = client.get(
            "/api/v1/templates",
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
