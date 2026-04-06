"""Unit tests for action endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.schemas.requests import (
    GenerateRequest,
    RefactorRequest,
    TestRequest,
    ExplainRequest,
    FixRequest,
    ChatRequest,
)
from src.models.response import GenerateResponse as AgentGenerateResponse


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
def api_key():
    """Return a test API key."""
    return "test-api-key-12345"


def get_auth_headers(token: str) -> dict:
    """Get authorization headers with Bearer token."""
    return {"Authorization": f"Bearer {token}"}


def get_api_key_headers(api_key: str) -> dict:
    """Get authorization headers with API key."""
    return {"x-api-key": api_key}


class TestGenerateEndpoint:
    """Tests for POST /api/v1/actions/generate endpoint."""

    def test_generate_basic_request(self, client, auth_token):
        """Test basic generate request."""
        payload = {
            "prompt": "Create a FastAPI endpoint",
        }
        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.generate = AsyncMock(
                return_value=AgentGenerateResponse(
                    code="def hello(): pass",
                    language="python",
                    tokens_used={"input_tokens": 50, "output_tokens": 100},
                )
            )
            mock_agent_class.return_value = mock_agent

            response = client.post(
                "/api/v1/actions/generate",
                json=payload,
                headers=get_auth_headers(auth_token),
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "generated_code" in data["data"]
        assert data["data"]["model_used"] == "haiku"

    def test_generate_with_custom_model(self, client, auth_token):
        """Test generate with custom model selection."""
        payload = {
            "prompt": "Create a FastAPI endpoint",
            "model": "sonnet",
            "max_tokens": 2048,
        }
        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.generate = AsyncMock(
                return_value=AgentGenerateResponse(
                    code="def hello(): pass",
                    language="python",
                    tokens_used={"input_tokens": 50, "output_tokens": 100},
                )
            )
            mock_agent_class.return_value = mock_agent

            response = client.post(
                "/api/v1/actions/generate",
                json=payload,
                headers=get_auth_headers(auth_token),
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["model_used"] == "sonnet"

    def test_generate_with_custom_temperature(self, client, auth_token):
        """Test generate with custom temperature."""
        payload = {
            "prompt": "Create a FastAPI endpoint",
            "temperature": 0.7,
        }
        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.generate = AsyncMock(
                return_value=AgentGenerateResponse(
                    code="def hello(): pass",
                    language="python",
                    tokens_used={"input_tokens": 50, "output_tokens": 100},
                )
            )
            mock_agent_class.return_value = mock_agent

            response = client.post(
                "/api/v1/actions/generate",
                json=payload,
                headers=get_auth_headers(auth_token),
            )

        assert response.status_code == 200

    def test_generate_missing_prompt(self, client, auth_token):
        """Test generate without required prompt parameter."""
        payload = {}
        response = client.post(
            "/api/v1/actions/generate",
            json=payload,
            headers=get_auth_headers(auth_token),
        )
        assert response.status_code == 422  # Validation error

    def test_generate_empty_prompt(self, client, auth_token):
        """Test generate with empty prompt."""
        payload = {"prompt": ""}
        response = client.post(
            "/api/v1/actions/generate",
            json=payload,
            headers=get_auth_headers(auth_token),
        )
        assert response.status_code == 422  # Validation error

    def test_generate_invalid_model(self, client, auth_token):
        """Test generate with invalid model choice."""
        payload = {
            "prompt": "Create a FastAPI endpoint",
            "model": "gpt4",
        }
        response = client.post(
            "/api/v1/actions/generate",
            json=payload,
            headers=get_auth_headers(auth_token),
        )
        assert response.status_code == 422  # Validation error

    def test_generate_without_auth(self, client):
        """Test generate without authentication."""
        payload = {"prompt": "Create a FastAPI endpoint"}
        response = client.post(
            "/api/v1/actions/generate",
            json=payload,
        )
        assert response.status_code == 403  # Forbidden


class TestRefactorEndpoint:
    """Tests for POST /api/v1/actions/refactor endpoint."""

    def test_refactor_basic_request(self, client, auth_token, tmp_path):
        """Test basic refactor request."""
        # Create a temporary file
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    print('hello')")

        # Patch file path validation to use tmp_path
        payload = {
            "file_path": "test.py",
            "requirements": "Add type hints",
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            with patch(
                "src.api.routes.actions.validate_file_exists"
            ) as mock_validate:
                mock_validate.return_value = test_file
                mock_agent = AsyncMock()
                mock_agent.refactor = AsyncMock(
                    return_value=AgentGenerateResponse(
                        code="def hello() -> None:\n    print('hello')",
                        language="python",
                        tokens_used={"input_tokens": 60, "output_tokens": 80},
                    )
                )
                mock_agent_class.return_value = mock_agent

                response = client.post(
                    "/api/v1/actions/refactor",
                    json=payload,
                    headers=get_auth_headers(auth_token),
                )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "refactored_code" in data["data"]

    def test_refactor_missing_file_path(self, client, auth_token):
        """Test refactor without file_path."""
        payload = {"requirements": "Add type hints"}
        response = client.post(
            "/api/v1/actions/refactor",
            json=payload,
            headers=get_auth_headers(auth_token),
        )
        assert response.status_code == 422  # Validation error

    def test_refactor_missing_requirements(self, client, auth_token):
        """Test refactor without requirements."""
        payload = {"file_path": "src/utils.py"}
        response = client.post(
            "/api/v1/actions/refactor",
            json=payload,
            headers=get_auth_headers(auth_token),
        )
        assert response.status_code == 422  # Validation error

    def test_refactor_invalid_file_path(self, client, auth_token):
        """Test refactor with dangerous file path."""
        payload = {
            "file_path": "../../../etc/passwd",
            "requirements": "Add type hints",
        }
        response = client.post(
            "/api/v1/actions/refactor",
            json=payload,
            headers=get_auth_headers(auth_token),
        )
        assert response.status_code == 422  # Validation error

    def test_refactor_nonexistent_file(self, client, auth_token):
        """Test refactor with nonexistent file."""
        payload = {
            "file_path": "nonexistent.py",
            "requirements": "Add type hints",
        }

        with patch("src.api.routes.actions.validate_file_exists") as mock_validate:
            from src.api.exceptions import ValidationError
            mock_validate.side_effect = ValidationError("File not found")

            response = client.post(
                "/api/v1/actions/refactor",
                json=payload,
                headers=get_auth_headers(auth_token),
            )

        assert response.status_code == 400


class TestTestEndpoint:
    """Tests for POST /api/v1/actions/test endpoint."""

    def test_test_basic_request(self, client, auth_token, tmp_path):
        """Test basic test generation request."""
        # Create a temporary file
        test_file = tmp_path / "app.py"
        test_file.write_text("def add(a, b):\n    return a + b")

        payload = {
            "file_path": "app.py",
            "framework": "pytest",
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            with patch(
                "src.api.routes.actions.validate_file_exists"
            ) as mock_validate:
                mock_validate.return_value = test_file
                mock_agent = AsyncMock()
                mock_agent.add_tests = AsyncMock(
                    return_value=AgentGenerateResponse(
                        code="def test_add():\n    assert add(1, 2) == 3",
                        language="python",
                        tokens_used={"input_tokens": 50, "output_tokens": 120},
                    )
                )
                mock_agent_class.return_value = mock_agent

                response = client.post(
                    "/api/v1/actions/test",
                    json=payload,
                    headers=get_auth_headers(auth_token),
                )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "test_code" in data["data"]
        assert "coverage_estimate" in data["data"]

    def test_test_with_vitest_framework(self, client, auth_token, tmp_path):
        """Test test generation with vitest framework."""
        test_file = tmp_path / "utils.js"
        test_file.write_text("export const add = (a, b) => a + b;")

        payload = {
            "file_path": "utils.js",
            "framework": "vitest",
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            with patch(
                "src.api.routes.actions.validate_file_exists"
            ) as mock_validate:
                mock_validate.return_value = test_file
                mock_agent = AsyncMock()
                mock_agent.add_tests = AsyncMock(
                    return_value=AgentGenerateResponse(
                        code="test('add', () => { expect(add(1, 2)).toBe(3); })",
                        language="javascript",
                        tokens_used={"input_tokens": 45, "output_tokens": 90},
                    )
                )
                mock_agent_class.return_value = mock_agent

                response = client.post(
                    "/api/v1/actions/test",
                    json=payload,
                    headers=get_auth_headers(auth_token),
                )

        assert response.status_code == 200

    def test_test_with_jest_framework(self, client, auth_token, tmp_path):
        """Test test generation with jest framework."""
        test_file = tmp_path / "helper.js"
        test_file.write_text("const mul = (a, b) => a * b;")

        payload = {
            "file_path": "helper.js",
            "framework": "jest",
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            with patch(
                "src.api.routes.actions.validate_file_exists"
            ) as mock_validate:
                mock_validate.return_value = test_file
                mock_agent = AsyncMock()
                mock_agent.add_tests = AsyncMock(
                    return_value=AgentGenerateResponse(
                        code="test('mul', () => { expect(mul(2, 3)).toBe(6); })",
                        language="javascript",
                        tokens_used={"input_tokens": 45, "output_tokens": 85},
                    )
                )
                mock_agent_class.return_value = mock_agent

                response = client.post(
                    "/api/v1/actions/test",
                    json=payload,
                    headers=get_auth_headers(auth_token),
                )

        assert response.status_code == 200

    def test_test_missing_framework(self, client, auth_token):
        """Test test generation without framework."""
        payload = {"file_path": "app.py"}
        response = client.post(
            "/api/v1/actions/test",
            json=payload,
            headers=get_auth_headers(auth_token),
        )
        assert response.status_code == 422  # Validation error

    def test_test_invalid_framework(self, client, auth_token):
        """Test test generation with invalid framework."""
        payload = {
            "file_path": "app.py",
            "framework": "unittest",
        }
        response = client.post(
            "/api/v1/actions/test",
            json=payload,
            headers=get_auth_headers(auth_token),
        )
        assert response.status_code == 422  # Validation error


class TestExplainEndpoint:
    """Tests for POST /api/v1/actions/explain endpoint."""

    def test_explain_basic_request(self, client, auth_token, tmp_path):
        """Test basic explain request."""
        test_file = tmp_path / "auth.py"
        test_file.write_text("import jwt\n\ndef verify_token(token):\n    return jwt.decode(token, 'secret')")

        payload = {
            "file_path": "auth.py",
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            with patch(
                "src.api.routes.actions.validate_file_exists"
            ) as mock_validate:
                mock_validate.return_value = test_file
                mock_agent = AsyncMock()
                mock_agent._call_bedrock = AsyncMock(
                    return_value=MagicMock(
                        content="This code verifies JWT tokens, authentication, security",
                        usage={"input_tokens": 55, "output_tokens": 200},
                    )
                )
                mock_agent_class.return_value = mock_agent

                response = client.post(
                    "/api/v1/actions/explain",
                    json=payload,
                    headers=get_auth_headers(auth_token),
                )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "explanation" in data["data"]
        assert "key_concepts" in data["data"]

    def test_explain_with_focus_area(self, client, auth_token, tmp_path):
        """Test explain with focus area."""
        test_file = tmp_path / "db.py"
        test_file.write_text("def query_users(): pass")

        payload = {
            "file_path": "db.py",
            "focus_area": "database queries",
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            with patch(
                "src.api.routes.actions.validate_file_exists"
            ) as mock_validate:
                mock_validate.return_value = test_file
                mock_agent = AsyncMock()
                mock_agent._call_bedrock = AsyncMock(
                    return_value=MagicMock(
                        content="This focuses on database, queries, performance",
                        usage={"input_tokens": 50, "output_tokens": 150},
                    )
                )
                mock_agent_class.return_value = mock_agent

                response = client.post(
                    "/api/v1/actions/explain",
                    json=payload,
                    headers=get_auth_headers(auth_token),
                )

        assert response.status_code == 200

    def test_explain_with_korean_language(self, client, auth_token, tmp_path):
        """Test explain with Korean language."""
        test_file = tmp_path / "api.py"
        test_file.write_text("@app.get('/users')")

        payload = {
            "file_path": "api.py",
            "language": "korean",
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            with patch(
                "src.api.routes.actions.validate_file_exists"
            ) as mock_validate:
                mock_validate.return_value = test_file
                mock_agent = AsyncMock()
                mock_agent._call_bedrock = AsyncMock(
                    return_value=MagicMock(
                        content="API, 엔드포인트, 사용자",
                        usage={"input_tokens": 50, "output_tokens": 100},
                    )
                )
                mock_agent_class.return_value = mock_agent

                response = client.post(
                    "/api/v1/actions/explain",
                    json=payload,
                    headers=get_auth_headers(auth_token),
                )

        assert response.status_code == 200


class TestFixEndpoint:
    """Tests for POST /api/v1/actions/fix endpoint."""

    def test_fix_basic_request(self, client, auth_token, tmp_path):
        """Test basic fix request."""
        test_file = tmp_path / "app.py"
        test_file.write_text("def process(data):\n    return data['key']")

        payload = {
            "file_path": "app.py",
            "error_message": "TypeError: 'NoneType' object is not subscriptable",
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            with patch(
                "src.api.routes.actions.validate_file_exists"
            ) as mock_validate:
                mock_validate.return_value = test_file
                mock_agent = AsyncMock()
                mock_agent._call_bedrock = AsyncMock(
                    return_value=MagicMock(
                        content="def process(data):\n    if data:\n        return data.get('key')",
                        usage={"input_tokens": 65, "output_tokens": 110},
                    )
                )
                mock_agent_class.return_value = mock_agent

                response = client.post(
                    "/api/v1/actions/fix",
                    json=payload,
                    headers=get_auth_headers(auth_token),
                )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "fixed_code" in data["data"]
        assert "fix_summary" in data["data"]

    def test_fix_missing_error_message(self, client, auth_token):
        """Test fix without error_message."""
        payload = {"file_path": "app.py"}
        response = client.post(
            "/api/v1/actions/fix",
            json=payload,
            headers=get_auth_headers(auth_token),
        )
        assert response.status_code == 422  # Validation error


class TestChatEndpoint:
    """Tests for POST /api/v1/actions/chat endpoint."""

    def test_chat_basic_request(self, client, auth_token):
        """Test basic chat request."""
        payload = {
            "message": "How do I implement error handling in FastAPI?",
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent._call_bedrock = AsyncMock(
                return_value=MagicMock(
                    content="You can use try/except blocks...",
                    usage={"input_tokens": 40, "output_tokens": 180},
                )
            )
            mock_agent_class.return_value = mock_agent

            response = client.post(
                "/api/v1/actions/chat",
                json=payload,
                headers=get_auth_headers(auth_token),
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "response" in data["data"]
        assert "conversation_id" in data["data"]

    def test_chat_with_conversation_id(self, client, auth_token):
        """Test chat with existing conversation_id."""
        conversation_id = "550e8400-e29b-41d4-a716-446655440000"
        payload = {
            "message": "Tell me more",
            "conversation_id": conversation_id,
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent._call_bedrock = AsyncMock(
                return_value=MagicMock(
                    content="Here's more information...",
                    usage={"input_tokens": 35, "output_tokens": 160},
                )
            )
            mock_agent_class.return_value = mock_agent

            response = client.post(
                "/api/v1/actions/chat",
                json=payload,
                headers=get_auth_headers(auth_token),
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["conversation_id"] == conversation_id

    def test_chat_missing_message(self, client, auth_token):
        """Test chat without message."""
        payload = {}
        response = client.post(
            "/api/v1/actions/chat",
            json=payload,
            headers=get_auth_headers(auth_token),
        )
        assert response.status_code == 422  # Validation error

    def test_chat_empty_message(self, client, auth_token):
        """Test chat with empty message."""
        payload = {"message": ""}
        response = client.post(
            "/api/v1/actions/chat",
            json=payload,
            headers=get_auth_headers(auth_token),
        )
        assert response.status_code == 422  # Validation error


class TestAuthenticationRequirement:
    """Tests for authentication requirement on action endpoints."""

    def test_all_endpoints_require_auth(self, client):
        """Test that all action endpoints require authentication."""
        endpoints = [
            ("/api/v1/actions/generate", {"prompt": "test"}),
            ("/api/v1/actions/refactor", {"file_path": "test.py", "requirements": "test"}),
            ("/api/v1/actions/test", {"file_path": "test.py", "framework": "pytest"}),
            ("/api/v1/actions/explain", {"file_path": "test.py"}),
            ("/api/v1/actions/fix", {"file_path": "test.py", "error_message": "error"}),
            ("/api/v1/actions/chat", {"message": "hello"}),
        ]

        for endpoint, payload in endpoints:
            response = client.post(endpoint, json=payload)
            # Should return 403 or 401 (depending on whether Bearer default exists)
            assert response.status_code in [401, 403, 422]


class TestResponseFormat:
    """Tests for response format consistency."""

    def test_generate_response_format(self, client, auth_token):
        """Test generate response includes all required fields."""
        payload = {"prompt": "test"}

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.generate = AsyncMock(
                return_value=AgentGenerateResponse(
                    code="test",
                    language="python",
                    tokens_used={"input_tokens": 10, "output_tokens": 20},
                )
            )
            mock_agent_class.return_value = mock_agent

            response = client.post(
                "/api/v1/actions/generate",
                json=payload,
                headers=get_auth_headers(auth_token),
            )

        data = response.json()
        assert "success" in data
        assert "data" in data
        assert "timestamp" in data
        assert isinstance(data["data"]["tokens_used"], dict)
        assert "input" in data["data"]["tokens_used"]
        assert "output" in data["data"]["tokens_used"]
        assert isinstance(data["data"]["execution_time"], float)
