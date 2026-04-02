from src.models.request import BedrockRequest, GenerateRequest
from src.models.response import BedrockResponse, GenerateResponse

def test_bedrock_request_to_body():
    """Test BedrockRequest.to_body() creates correct structure."""
    req = BedrockRequest(
        model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
        max_tokens=1024,
        system_prompt="You are a helpful assistant.",
        user_message="Hello"
    )
    body = req.to_body()

    assert body["anthropic_version"] == "bedrock-2023-06-01"
    assert body["max_tokens"] == 1024
    assert body["system"] == "You are a helpful assistant."
    assert len(body["messages"]) == 1
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][0]["content"] == "Hello"

def test_bedrock_request_with_history():
    """Test BedrockRequest.to_body() with conversation history."""
    history = [
        {"role": "user", "content": "First message"},
        {"role": "assistant", "content": "First response"}
    ]
    req = BedrockRequest(
        model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
        max_tokens=1024,
        system_prompt="You are helpful.",
        user_message="Second message",
        messages=history
    )
    body = req.to_body()

    assert len(body["messages"]) == 3
    assert body["messages"][2]["role"] == "user"
    assert body["messages"][2]["content"] == "Second message"

def test_generate_request_defaults():
    """Test GenerateRequest defaults."""
    req = GenerateRequest(prompt="Create a function")

    assert req.prompt == "Create a function"
    assert req.language is None
    assert req.temperature == 0.2
    assert req.max_tokens == 4096

def test_bedrock_response_creation():
    """Test BedrockResponse creation."""
    resp = BedrockResponse(
        content="Generated code",
        stop_reason="end_turn",
        usage={"input_tokens": 100, "output_tokens": 200}
    )

    assert resp.content == "Generated code"
    assert resp.stop_reason == "end_turn"
    assert resp.usage["input_tokens"] == 100
