"""Integration tests for action endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from fastapi.testclient import TestClient
from src.api.main import app
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


def get_auth_headers(token: str) -> dict:
    """Get authorization headers with Bearer token."""
    return {"Authorization": f"Bearer {token}"}


class TestGenerateIntegration:
    """Integration tests for generate action."""

    def test_generate_full_flow(self, client, auth_token):
        """Test complete generate flow."""
        payload = {
            "prompt": "Create a FastAPI endpoint that returns user data",
            "model": "haiku",
            "max_tokens": 1024,
            "temperature": 0.3,
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.generate = AsyncMock(
                return_value=AgentGenerateResponse(
                    code="@app.get('/users/{user_id}')\nasync def get_user(user_id: int): return {'id': user_id}",
                    language="python",
                    tokens_used={"input_tokens": 100, "output_tokens": 200},
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

        # Verify response structure
        assert data["success"] is True
        assert data["data"]["generated_code"] is not None
        assert data["data"]["model_used"] == "haiku"
        assert data["data"]["tokens_used"]["input"] == 100
        assert data["data"]["tokens_used"]["output"] == 200
        assert data["data"]["execution_time"] > 0
        assert "timestamp" in data

    def test_generate_tracks_metrics(self, client, auth_token):
        """Test that generate tracks execution metrics."""
        payload = {"prompt": "test"}

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.generate = AsyncMock(
                return_value=AgentGenerateResponse(
                    code="test",
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

        data = response.json()
        assert isinstance(data["data"]["execution_time"], float)
        assert data["data"]["execution_time"] >= 0


class TestRefactorIntegration:
    """Integration tests for refactor action."""

    def test_refactor_full_flow(self, client, auth_token, tmp_path):
        """Test complete refactor flow."""
        # Create test file
        test_file = tmp_path / "legacy.py"
        test_file.write_text("def process_data(data):\n    result = []\n    for item in data:\n        result.append(item * 2)\n    return result")

        payload = {
            "file_path": "legacy.py",
            "requirements": "Add type hints and use list comprehension",
            "model": "haiku",
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            with patch(
                "src.api.routes.actions.validate_file_exists"
            ) as mock_validate:
                mock_validate.return_value = test_file
                mock_agent = AsyncMock()
                mock_agent.refactor = AsyncMock(
                    return_value=AgentGenerateResponse(
                        code="def process_data(data: list) -> list:\n    return [item * 2 for item in data]",
                        language="python",
                        tokens_used={"input_tokens": 120, "output_tokens": 80},
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
        assert "changes_summary" in data["data"]


class TestTestIntegration:
    """Integration tests for test action."""

    def test_test_generation_full_flow(self, client, auth_token, tmp_path):
        """Test complete test generation flow."""
        # Create test file
        test_file = tmp_path / "math.py"
        test_file.write_text("def add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b")

        payload = {
            "file_path": "math.py",
            "framework": "pytest",
            "model": "haiku",
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            with patch(
                "src.api.routes.actions.validate_file_exists"
            ) as mock_validate:
                mock_validate.return_value = test_file
                mock_agent = AsyncMock()
                mock_agent.add_tests = AsyncMock(
                    return_value=AgentGenerateResponse(
                        code="import pytest\n\ndef test_add():\n    assert add(1, 2) == 3\n\ndef test_multiply():\n    assert multiply(2, 3) == 6",
                        language="python",
                        tokens_used={"input_tokens": 100, "output_tokens": 150},
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


class TestExplainIntegration:
    """Integration tests for explain action."""

    def test_explain_full_flow(self, client, auth_token, tmp_path):
        """Test complete explain flow."""
        # Create test file
        test_file = tmp_path / "middleware.py"
        test_file.write_text("from fastapi import FastAPI, Request\n\napp = FastAPI()\n\n@app.middleware('http')\nasync def add_headers(request: Request, call_next):\n    response = await call_next(request)\n    response.headers['X-Custom'] = 'value'\n    return response")

        payload = {
            "file_path": "middleware.py",
            "focus_area": "middleware pattern",
            "language": "english",
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            with patch(
                "src.api.routes.actions.validate_file_exists"
            ) as mock_validate:
                mock_validate.return_value = test_file
                mock_agent = AsyncMock()
                mock_agent._call_bedrock = AsyncMock(
                    return_value=MagicMock(
                        content="This middleware pattern intercepts HTTP requests, allows request processing, middleware, interceptors, request lifecycle",
                        usage={"input_tokens": 80, "output_tokens": 220},
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
        assert isinstance(data["data"]["key_concepts"], list)


class TestFixIntegration:
    """Integration tests for fix action."""

    def test_fix_full_flow(self, client, auth_token, tmp_path):
        """Test complete fix flow."""
        # Create test file with bug
        test_file = tmp_path / "buggy.py"
        test_file.write_text("def get_value(d):\n    return d['key']\n\nresult = get_value(None)")

        payload = {
            "file_path": "buggy.py",
            "error_message": "TypeError: 'NoneType' object is not subscriptable",
            "model": "haiku",
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            with patch(
                "src.api.routes.actions.validate_file_exists"
            ) as mock_validate:
                mock_validate.return_value = test_file
                mock_agent = AsyncMock()
                mock_agent._call_bedrock = AsyncMock(
                    return_value=MagicMock(
                        content="def get_value(d):\n    if d is None:\n        return None\n    return d.get('key')",
                        usage={"input_tokens": 90, "output_tokens": 130},
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


class TestChatIntegration:
    """Integration tests for chat action."""

    def test_chat_creates_conversation(self, client, auth_token):
        """Test that chat creates a new conversation."""
        payload = {
            "message": "How do I handle errors in FastAPI?",
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent._call_bedrock = AsyncMock(
                return_value=MagicMock(
                    content="You can use try/except blocks or the HTTPException class",
                    usage={"input_tokens": 45, "output_tokens": 200},
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
        assert "conversation_id" in data["data"]
        # Verify it's a valid UUID
        conversation_id = data["data"]["conversation_id"]
        try:
            uuid.UUID(conversation_id)
        except ValueError:
            pytest.fail(f"Invalid UUID: {conversation_id}")

    def test_chat_maintains_conversation_history(self, client, auth_token):
        """Test that chat maintains conversation history."""
        conversation_id = str(uuid.uuid4())

        # First message
        payload1 = {
            "message": "What is Python?",
            "conversation_id": conversation_id,
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent._call_bedrock = AsyncMock(
                return_value=MagicMock(
                    content="Python is a programming language",
                    usage={"input_tokens": 30, "output_tokens": 100},
                )
            )
            mock_agent_class.return_value = mock_agent

            response1 = client.post(
                "/api/v1/actions/chat",
                json=payload1,
                headers=get_auth_headers(auth_token),
            )

        assert response1.status_code == 200

        # Second message (should have history)
        payload2 = {
            "message": "What are its features?",
            "conversation_id": conversation_id,
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent._call_bedrock = AsyncMock(
                return_value=MagicMock(
                    content="Python has many features like dynamic typing and libraries",
                    usage={"input_tokens": 50, "output_tokens": 150},
                )
            )
            mock_agent_class.return_value = mock_agent

            response2 = client.post(
                "/api/v1/actions/chat",
                json=payload2,
                headers=get_auth_headers(auth_token),
            )

        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["data"]["conversation_id"] == conversation_id


class TestErrorHandling:
    """Tests for error handling in action endpoints."""

    def test_file_not_found_error(self, client, auth_token):
        """Test proper error handling when file is not found."""
        payload = {
            "file_path": "nonexistent_file.py",
            "requirements": "add type hints",
        }

        with patch(
            "src.api.routes.actions.validate_file_exists"
        ) as mock_validate:
            from src.api.exceptions import ValidationError
            mock_validate.side_effect = ValidationError("File not found: nonexistent_file.py")

            response = client.post(
                "/api/v1/actions/refactor",
                json=payload,
                headers=get_auth_headers(auth_token),
            )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error_code" in data

    def test_bedrock_failure_handling(self, client, auth_token):
        """Test proper error handling when Bedrock fails."""
        payload = {"prompt": "test"}

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.generate = AsyncMock(
                side_effect=Exception("Bedrock service unavailable")
            )
            mock_agent_class.return_value = mock_agent

            response = client.post(
                "/api/v1/actions/generate",
                json=payload,
                headers=get_auth_headers(auth_token),
            )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False


class TestRateLimiting:
    """Tests for rate limiting on action endpoints."""

    def test_multiple_rapid_requests(self, client, auth_token):
        """Test that multiple rapid requests are handled."""
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

            # Make multiple requests
            for i in range(3):
                response = client.post(
                    "/api/v1/actions/generate",
                    json=payload,
                    headers=get_auth_headers(auth_token),
                )
                assert response.status_code == 200


class TestTokenUsageTracking:
    """Tests for token usage tracking in responses."""

    def test_generate_tracks_token_usage(self, client, auth_token):
        """Test that generate tracks token usage correctly."""
        payload = {"prompt": "test"}

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.generate = AsyncMock(
                return_value=AgentGenerateResponse(
                    code="test",
                    language="python",
                    tokens_used={"input_tokens": 75, "output_tokens": 250},
                )
            )
            mock_agent_class.return_value = mock_agent

            response = client.post(
                "/api/v1/actions/generate",
                json=payload,
                headers=get_auth_headers(auth_token),
            )

        data = response.json()
        assert data["data"]["tokens_used"]["input"] == 75
        assert data["data"]["tokens_used"]["output"] == 250
        assert data["data"]["tokens_used"]["input"] + data["data"]["tokens_used"]["output"] > 0

    def test_refactor_tracks_token_usage(self, client, auth_token, tmp_path):
        """Test that refactor tracks token usage correctly."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo(): pass")

        payload = {
            "file_path": "test.py",
            "requirements": "improve",
        }

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            with patch(
                "src.api.routes.actions.validate_file_exists"
            ) as mock_validate:
                mock_validate.return_value = test_file
                mock_agent = AsyncMock()
                mock_agent.refactor = AsyncMock(
                    return_value=AgentGenerateResponse(
                        code="def foo() -> None: pass",
                        language="python",
                        tokens_used={"input_tokens": 100, "output_tokens": 80},
                    )
                )
                mock_agent_class.return_value = mock_agent

                response = client.post(
                    "/api/v1/actions/refactor",
                    json=payload,
                    headers=get_auth_headers(auth_token),
                )

        data = response.json()
        assert data["data"]["tokens_used"]["input"] == 100
        assert data["data"]["tokens_used"]["output"] == 80


class TestResponseConsistency:
    """Tests for consistent response format across endpoints."""

    def test_all_responses_have_consistent_structure(self, client, auth_token, tmp_path):
        """Test that all endpoint responses follow the same structure."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")

        endpoints = [
            ("generate", {"prompt": "test"}),
            ("refactor", {"file_path": "test.py", "requirements": "test"}),
            ("test", {"file_path": "test.py", "framework": "pytest"}),
            ("explain", {"file_path": "test.py"}),
            ("fix", {"file_path": "test.py", "error_message": "error"}),
            ("chat", {"message": "hello"}),
        ]

        with patch("src.api.routes.actions.JmAgent") as mock_agent_class:
            with patch(
                "src.api.routes.actions.validate_file_exists"
            ) as mock_validate:
                mock_validate.return_value = test_file

                for endpoint_name, payload in endpoints:
                    mock_agent = AsyncMock()

                    if endpoint_name == "generate":
                        mock_agent.generate = AsyncMock(
                            return_value=AgentGenerateResponse(
                                code="test",
                                language="python",
                                tokens_used={"input_tokens": 10, "output_tokens": 20},
                            )
                        )
                    elif endpoint_name == "refactor":
                        mock_agent.refactor = AsyncMock(
                            return_value=AgentGenerateResponse(
                                code="test",
                                language="python",
                                tokens_used={"input_tokens": 10, "output_tokens": 20},
                            )
                        )
                    elif endpoint_name == "test":
                        mock_agent.add_tests = AsyncMock(
                            return_value=AgentGenerateResponse(
                                code="test",
                                language="python",
                                tokens_used={"input_tokens": 10, "output_tokens": 20},
                            )
                        )
                    else:
                        mock_agent._call_bedrock = AsyncMock(
                            return_value=MagicMock(
                                content="test",
                                usage={"input_tokens": 10, "output_tokens": 20},
                            )
                        )

                    mock_agent_class.return_value = mock_agent

                    response = client.post(
                        f"/api/v1/actions/{endpoint_name}",
                        json=payload,
                        headers=get_auth_headers(auth_token),
                    )

                    assert response.status_code == 200
                    data = response.json()

                    # Check consistent structure
                    assert "success" in data
                    assert "data" in data
                    assert "timestamp" in data
                    assert data["success"] is True
                    assert isinstance(data["data"]["execution_time"], float)
