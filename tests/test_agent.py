import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.agent import JmAgent, MODELS

@pytest.fixture
def agent():
    """Create a JmAgent instance with mocked Bedrock client."""
    with patch("src.agent.build_bedrock_runtime"):
        return JmAgent(model="haiku")

def test_agent_initialization(agent):
    """Test JmAgent initialization."""
    assert agent.model == "haiku"
    assert agent.model_id == MODELS["haiku"]
    assert agent.temperature == 0.2
    assert agent.max_tokens == 4096
    assert agent.conversation_history == []

def test_agent_model_selection():
    """Test model selection."""
    with patch("src.agent.build_bedrock_runtime"):
        agent_sonnet = JmAgent(model="sonnet")
        assert agent_sonnet.model_id == MODELS["sonnet"]

        agent_opus = JmAgent(model="opus")
        assert agent_opus.model_id == MODELS["opus"]

@pytest.mark.asyncio
async def test_generate():
    """Test code generation."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        # Mock Bedrock response
        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            from src.models.response import BedrockResponse
            mock_bedrock.return_value = BedrockResponse(
                content="def hello():\n    return 'world'",
                stop_reason="end_turn",
                usage={"input_tokens": 50, "output_tokens": 20}
            )

            result = await agent.generate("Create a hello function")

            assert "def hello" in result.code
            assert result.language is None
            assert result.tokens_used["input_tokens"] == 50

@pytest.mark.asyncio
async def test_generate_with_language():
    """Test code generation with language specified."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            from src.models.response import BedrockResponse
            mock_bedrock.return_value = BedrockResponse(
                content="func hello() { return 'world' }",
                stop_reason="end_turn",
                usage={"input_tokens": 50, "output_tokens": 20}
            )

            result = await agent.generate(
                "Create a hello function",
                language="JavaScript"
            )

            assert result.language == "JavaScript"
            mock_bedrock.assert_called_once()

@pytest.mark.asyncio
async def test_chat_maintains_history():
    """Test chat maintains conversation history."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            from src.models.response import BedrockResponse

            # First message
            mock_bedrock.return_value = BedrockResponse(
                content="I can help with that",
                stop_reason="end_turn",
                usage={"input_tokens": 50, "output_tokens": 20}
            )

            response1 = await agent.chat("Can you help me?")
            assert response1 == "I can help with that"
            assert len(agent.conversation_history) == 2
            assert agent.conversation_history[0]["role"] == "user"
            assert agent.conversation_history[1]["role"] == "assistant"

            # Second message
            mock_bedrock.return_value = BedrockResponse(
                content="Sure, here's some code",
                stop_reason="end_turn",
                usage={"input_tokens": 100, "output_tokens": 50}
            )

            response2 = await agent.chat("Show me an example")
            assert response2 == "Sure, here's some code"
            assert len(agent.conversation_history) == 4

def test_reset_history(agent):
    """Test resetting conversation history."""
    agent.conversation_history = [
        {"role": "user", "content": "test"},
        {"role": "assistant", "content": "response"}
    ]

    agent.reset_history()
    assert agent.conversation_history == []

@pytest.mark.asyncio
async def test_explain():
    """Test code explanation."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            from src.models.response import BedrockResponse
            mock_bedrock.return_value = BedrockResponse(
                content="This function returns 'world'",
                stop_reason="end_turn",
                usage={"input_tokens": 50, "output_tokens": 20}
            )

            code = "def hello():\n    return 'world'"
            result = await agent.explain(code)

            assert "returns 'world'" in result

@pytest.mark.asyncio
async def test_refactor():
    """Test code refactoring."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            from src.models.response import BedrockResponse
            mock_bedrock.return_value = BedrockResponse(
                content="def hello() -> str:\n    return 'world'",
                stop_reason="end_turn",
                usage={"input_tokens": 50, "output_tokens": 20}
            )

            code = "def hello():\n    return 'world'"
            result = await agent.refactor(code, "Add type hints")

            assert "-> str" in result.code


@pytest.mark.asyncio
async def test_generate_with_formatting():
    """Test code generation with formatting enabled."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        # Mock Bedrock response
        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            from src.models.response import BedrockResponse
            mock_bedrock.return_value = BedrockResponse(
                content="def hello():\n    return 'world'",
                stop_reason="end_turn",
                usage={"input_tokens": 50, "output_tokens": 20}
            )

            # Mock formatter to verify it's called
            with patch.object(
                agent.formatter,
                "format",
                return_value="def hello():\n    return 'world'"
            ) as mock_format:
                result = await agent.generate(
                    "Create a hello function",
                    language="python",
                    format_code=True
                )

                # Verify formatter was called
                mock_format.assert_called_once()
                assert "def hello" in result.code


@pytest.mark.asyncio
async def test_refactor_with_formatting():
    """Test code refactoring with formatting enabled."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        # Mock Bedrock response
        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            from src.models.response import BedrockResponse
            mock_bedrock.return_value = BedrockResponse(
                content="def hello():\n    return 'world'",
                stop_reason="end_turn",
                usage={"input_tokens": 50, "output_tokens": 20}
            )

            # Mock formatter to verify it's called
            with patch.object(
                agent.formatter,
                "format",
                return_value="def hello():\n    return 'world'"
            ) as mock_format:
                result = await agent.refactor(
                    code="def hello():return 'world'",
                    requirements="add formatting",
                    language="python",
                    format_code=True
                )

                # Verify formatter was called
                mock_format.assert_called_once()
                assert "def hello" in result.code


@pytest.mark.asyncio
async def test_generate_without_formatting():
    """Test that formatting is not applied when format_code=False."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        # Mock Bedrock response
        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            from src.models.response import BedrockResponse
            mock_bedrock.return_value = BedrockResponse(
                content="def hello():return 'world'",
                stop_reason="end_turn",
                usage={"input_tokens": 50, "output_tokens": 20}
            )

            # Mock formatter to verify it's NOT called
            with patch.object(
                agent.formatter,
                "format",
            ) as mock_format:
                result = await agent.generate(
                    "Create a hello function",
                    format_code=False
                )

                # Verify formatter was NOT called
                mock_format.assert_not_called()
                assert result.code == "def hello():return 'world'"
