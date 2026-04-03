import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.agent import JmAgent, MODELS
from src.models.response import BedrockResponse


@pytest.mark.asyncio
async def test_full_generate_flow():
    """Integration test: full code generation flow."""
    with patch("src.agent.build_bedrock_runtime") as mock_build:
        mock_client = MagicMock()
        mock_build.return_value = mock_client

        agent = JmAgent(model="haiku")

        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            mock_bedrock.return_value = BedrockResponse(
                content="def hello():\n    return 'world'",
                stop_reason="end_turn",
                usage={"input_tokens": 50, "output_tokens": 20}
            )

            result = await agent.generate(
                prompt="Create a hello function",
                language="Python"
            )

            assert "def hello" in result.code
            assert result.language == "Python"
            assert result.tokens_used["input_tokens"] == 50
            mock_bedrock.assert_called_once()


@pytest.mark.asyncio
async def test_generate_with_file_context():
    """Integration test: generate with file context."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "existing code"

            with patch.object(
                agent,
                "_call_bedrock",
                new_callable=AsyncMock
            ) as mock_bedrock:
                mock_bedrock.return_value = BedrockResponse(
                    content="new code",
                    stop_reason="end_turn",
                    usage={"input_tokens": 100, "output_tokens": 50}
                )

                result = await agent.generate(
                    prompt="Create similar code",
                    context_files=["main.py"]
                )

                assert result.code == "new code"


def test_agent_initialization_and_model_selection():
    """Test agent can be initialized with all model options."""
    with patch("src.agent.build_bedrock_runtime"):
        for model in ["haiku", "sonnet", "opus"]:
            agent = JmAgent(model=model)
            assert agent.model == model
            assert agent.model_id is not None
            assert agent.model_id == MODELS[model]


@pytest.mark.asyncio
async def test_refactor_integration():
    """Integration test: full refactoring flow."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent(model="sonnet")

        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            mock_bedrock.return_value = BedrockResponse(
                content="def hello() -> str:\n    return 'world'",
                stop_reason="end_turn",
                usage={"input_tokens": 75, "output_tokens": 30}
            )

            original_code = "def hello():\n    return 'world'"
            result = await agent.refactor(
                code=original_code,
                requirements="Add type hints",
                language="Python"
            )

            assert "-> str" in result.code
            assert result.language == "Python"
            assert result.tokens_used["input_tokens"] == 75


@pytest.mark.asyncio
async def test_add_tests_integration():
    """Integration test: test generation."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            mock_bedrock.return_value = BedrockResponse(
                content="def test_hello():\n    assert hello() == 'world'",
                stop_reason="end_turn",
                usage={"input_tokens": 60, "output_tokens": 25}
            )

            code = "def hello():\n    return 'world'"
            result = await agent.add_tests(
                code=code,
                test_framework="pytest",
                target_coverage=0.8
            )

            assert "test_hello" in result.code
            assert "assert" in result.code


@pytest.mark.asyncio
async def test_explain_integration():
    """Integration test: code explanation."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            mock_bedrock.return_value = BedrockResponse(
                content="This function returns the string 'world'.",
                stop_reason="end_turn",
                usage={"input_tokens": 50, "output_tokens": 15}
            )

            code = "def hello():\n    return 'world'"
            result = await agent.explain(code, language="Python")

            assert "world" in result
            assert "string" in result


@pytest.mark.asyncio
async def test_fix_bug_integration():
    """Integration test: bug fixing."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            mock_bedrock.return_value = BedrockResponse(
                content="def divide(a, b):\n    if b == 0:\n        raise ValueError('Cannot divide by zero')\n    return a / b",
                stop_reason="end_turn",
                usage={"input_tokens": 80, "output_tokens": 40}
            )

            buggy_code = "def divide(a, b):\n    return a / b"
            result = await agent.fix_bug(
                code=buggy_code,
                error_message="ZeroDivisionError: division by zero"
            )

            assert "if b == 0" in result.code
            assert "ValueError" in result.code


@pytest.mark.asyncio
async def test_chat_integration_single_turn():
    """Integration test: single turn chat."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            mock_bedrock.return_value = BedrockResponse(
                content="I can help you with that!",
                stop_reason="end_turn",
                usage={"input_tokens": 50, "output_tokens": 10}
            )

            response = await agent.chat("Can you help me?")

            assert response == "I can help you with that!"
            assert len(agent.conversation_history) == 2
            assert agent.conversation_history[0]["role"] == "user"
            assert agent.conversation_history[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_chat_integration_multi_turn():
    """Integration test: multi-turn conversation with history."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            # First turn
            mock_bedrock.return_value = BedrockResponse(
                content="Sure, I can help you with Python!",
                stop_reason="end_turn",
                usage={"input_tokens": 50, "output_tokens": 10}
            )

            response1 = await agent.chat("Help me with Python")
            assert response1 == "Sure, I can help you with Python!"
            assert len(agent.conversation_history) == 2

            # Second turn - verifies history is maintained
            mock_bedrock.return_value = BedrockResponse(
                content="Here's a simple example: def hello(): return 'world'",
                stop_reason="end_turn",
                usage={"input_tokens": 100, "output_tokens": 20}
            )

            response2 = await agent.chat("Show me an example")
            assert "example" in response2.lower()
            assert len(agent.conversation_history) == 4


@pytest.mark.asyncio
async def test_reset_history_integration():
    """Integration test: reset conversation history."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        agent.conversation_history = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "response"}
        ]

        agent.reset_history()
        assert agent.conversation_history == []


@pytest.mark.asyncio
async def test_multiple_operations_sequence():
    """Integration test: sequence of different operations."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent(model="haiku")

        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            # Generate
            mock_bedrock.return_value = BedrockResponse(
                content="def add(a, b):\n    return a + b",
                stop_reason="end_turn",
                usage={"input_tokens": 50, "output_tokens": 20}
            )

            gen_result = await agent.generate("Create an add function")
            assert "def add" in gen_result.code

            # Refactor
            mock_bedrock.return_value = BedrockResponse(
                content="def add(a: int, b: int) -> int:\n    return a + b",
                stop_reason="end_turn",
                usage={"input_tokens": 75, "output_tokens": 30}
            )

            ref_result = await agent.refactor(
                code=gen_result.code,
                requirements="Add type hints"
            )
            assert "-> int" in ref_result.code

            # Test generation
            mock_bedrock.return_value = BedrockResponse(
                content="def test_add():\n    assert add(2, 3) == 5",
                stop_reason="end_turn",
                usage={"input_tokens": 60, "output_tokens": 25}
            )

            test_result = await agent.add_tests(ref_result.code)
            assert "test_add" in test_result.code


@pytest.mark.asyncio
async def test_context_files_parameter():
    """Integration test: context_files parameter is passed correctly."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock
        ) as mock_bedrock:
            mock_bedrock.return_value = BedrockResponse(
                content="generated code",
                stop_reason="end_turn",
                usage={"input_tokens": 100, "output_tokens": 50}
            )

            context_files = ["util.py", "helper.py"]
            await agent.generate(
                prompt="Generate based on context",
                context_files=context_files
            )

            # Verify the prompt includes context files reference
            call_args = mock_bedrock.call_args
            assert call_args is not None
            prompt_arg = call_args[0][1]  # Second positional argument
            assert "util.py" in prompt_arg or "helper.py" in prompt_arg


@pytest.mark.asyncio
async def test_error_handling_in_bedrock_call():
    """Integration test: error handling for Bedrock calls."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()

        with patch.object(
            agent,
            "_call_bedrock",
            new_callable=AsyncMock,
            side_effect=Exception("Bedrock API error")
        ):
            with pytest.raises(Exception):
                await agent.generate("Test prompt")


def test_agent_configuration_persistence():
    """Test that agent configuration persists across operations."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent(
            model="sonnet",
            temperature=0.7,
            max_tokens=2048
        )

        assert agent.model == "sonnet"
        assert agent.temperature == 0.7
        assert agent.max_tokens == 2048
