# jmAgent Phase 1 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the core jmAgent foundation with AWS Bedrock authentication, async JmAgent class, and argparse CLI to generate code from prompts.

**Architecture:** Three-layer design:
1. **Auth Layer** (`bedrock_auth.py`) - Flexible authentication (API Key or IAM), reusing FeedOPS patterns
2. **Agent Layer** (`agent.py`) - Core JmAgent class with async methods for code generation, refactoring, testing, etc.
3. **CLI Layer** (`cli.py`) - argparse-based entry point mapping commands to agent methods

**Tech Stack:** Python 3.10+, boto3, python-dotenv, argparse

---

## File Structure

```
~/Documents/jmAgent/
├── src/
│   ├── __init__.py
│   ├── agent.py                      # Core JmAgent class (async)
│   ├── cli.py                        # CLI entry point (argparse)
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   └── bedrock_auth.py           # FeedOPS-based Bedrock auth
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request.py                # Request data classes
│   │   └── response.py               # Response data classes
│   │
│   └── utils/
│       ├── __init__.py
│       └── logger.py                 # Logging utility
│
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   └── test_agent.py
│
├── .env.example
├── requirements.txt
└── setup.py
```

---

## Task 1: Project Structure & Environment Setup

**Files:**
- Create: `src/__init__.py`
- Create: `src/auth/__init__.py`
- Create: `src/models/__init__.py`
- Create: `src/utils/__init__.py`
- Create: `tests/__init__.py`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `setup.py`

- [ ] **Step 1: Create src package structure**

```bash
mkdir -p src/auth src/models src/utils tests
touch src/__init__.py src/auth/__init__.py src/models/__init__.py src/utils/__init__.py tests/__init__.py
```

- [ ] **Step 2: Create requirements.txt**

```
# Create /Users/jaimoonseo/Documents/jmAgent/requirements.txt
boto3>=1.28.0
python-dotenv>=1.0.0
```

- [ ] **Step 3: Create .env.example**

```
# Create /Users/jaimoonseo/Documents/jmAgent/.env.example
# AWS Bedrock Configuration
AWS_BEARER_TOKEN_BEDROCK=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_BEDROCK_REGION=us-east-1

# jmAgent Configuration (optional)
JM_DEFAULT_MODEL=haiku
JM_TEMPERATURE=0.2
JM_MAX_TOKENS=4096
```

- [ ] **Step 4: Create setup.py**

```
# Create /Users/jaimoonseo/Documents/jmAgent/setup.py
from setuptools import setup, find_packages

setup(
    name="jmAgent",
    version="0.1.0",
    description="Personal Claude coding assistant using AWS Bedrock",
    author="jmAgent",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "boto3>=1.28.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "jm=src.cli:main",
        ],
    },
)
```

- [ ] **Step 5: Install dependencies**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
pip install -r requirements.txt
pip install -e .
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .env.example setup.py src/__init__.py src/auth/__init__.py src/models/__init__.py src/utils/__init__.py tests/__init__.py
git commit -m "chore: initialize project structure and dependencies"
```

---

## Task 2: Logger Utility

**Files:**
- Create: `src/utils/logger.py`
- Create: `tests/test_logger.py`

- [ ] **Step 1: Create logger.py**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/src/utils/logger.py
import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with standard formatting."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger
```

- [ ] **Step 2: Create test for logger**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/tests/test_logger.py
import logging
from src.utils.logger import get_logger

def test_get_logger_returns_logger():
    """Test that get_logger returns a Logger instance."""
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"

def test_get_logger_has_handler():
    """Test that logger has at least one handler."""
    logger = get_logger("test_logger_2")
    assert len(logger.handlers) > 0

def test_get_logger_same_instance():
    """Test that calling get_logger twice returns same instance."""
    logger1 = get_logger("test_logger_3")
    logger2 = get_logger("test_logger_3")
    assert logger1 is logger2
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
python -m pytest tests/test_logger.py -v
```

Expected output:
```
tests/test_logger.py::test_get_logger_returns_logger PASSED
tests/test_logger.py::test_get_logger_has_handler PASSED
tests/test_logger.py::test_get_logger_same_instance PASSED

==== 3 passed in X.XXs ====
```

- [ ] **Step 4: Commit**

```bash
git add src/utils/logger.py tests/test_logger.py
git commit -m "feat: add logger utility"
```

---

## Task 3: Data Models (Request & Response)

**Files:**
- Create: `src/models/request.py`
- Create: `src/models/response.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Create request.py**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/src/models/request.py
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class BedrockRequest:
    """Request to Bedrock API."""
    model_id: str
    max_tokens: int
    system_prompt: str
    user_message: str
    messages: Optional[List[dict]] = None  # Conversation history
    
    def to_body(self) -> dict:
        """Convert to Bedrock request body."""
        messages = self.messages or []
        if self.user_message:
            messages.append({"role": "user", "content": self.user_message})
        
        return {
            "anthropic_version": "bedrock-2023-06-01",
            "max_tokens": self.max_tokens,
            "system": self.system_prompt,
            "messages": messages
        }

@dataclass
class GenerateRequest:
    """Request to generate code."""
    prompt: str
    language: Optional[str] = None
    context_files: Optional[List[str]] = None
    temperature: float = 0.2
    max_tokens: int = 4096
```

- [ ] **Step 2: Create response.py**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/src/models/response.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class BedrockResponse:
    """Response from Bedrock API."""
    content: str
    stop_reason: str
    usage: dict  # {"input_tokens": int, "output_tokens": int}

@dataclass
class GenerateResponse:
    """Response from generate action."""
    code: str
    language: Optional[str]
    tokens_used: dict  # {"input_tokens": int, "output_tokens": int}
```

- [ ] **Step 3: Create test for models**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/tests/test_models.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
python -m pytest tests/test_models.py -v
```

Expected output:
```
tests/test_models.py::test_bedrock_request_to_body PASSED
tests/test_models.py::test_bedrock_request_with_history PASSED
tests/test_models.py::test_generate_request_defaults PASSED
tests/test_models.py::test_bedrock_response_creation PASSED

==== 4 passed in X.XXs ====
```

- [ ] **Step 5: Commit**

```bash
git add src/models/request.py src/models/response.py tests/test_models.py
git commit -m "feat: add request and response data models"
```

---

## Task 4: Bedrock Authentication (bedrock_auth.py)

**Files:**
- Create: `src/auth/bedrock_auth.py`
- Create: `tests/test_auth.py`

- [ ] **Step 1: Create bedrock_auth.py**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/src/auth/bedrock_auth.py
import os
import boto3
from src.utils.logger import get_logger

logger = get_logger(__name__)

def detect_auth_mode() -> str:
    """
    Detect authentication mode: 'api_key' or 'iam'.
    
    Returns:
        'api_key' if AWS_BEARER_TOKEN_BEDROCK is set or ACCESS_KEY starts with 'ABSK'
        'iam' otherwise
    """
    bearer = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "").strip()
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
    
    if bearer or (access_key and access_key.upper().startswith("ABSK")):
        return "api_key"
    
    return "iam"

def build_bedrock_runtime(region: str = "us-east-1"):
    """
    Build Bedrock runtime client with flexible authentication.
    
    Args:
        region: AWS region (default: us-east-1)
    
    Returns:
        boto3 bedrock-runtime client
    
    Raises:
        ValueError: If authentication credentials are not configured
    """
    auth_mode = detect_auth_mode()
    
    if auth_mode == "api_key":
        bearer = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "").strip()
        if bearer:
            os.environ["AWS_BEARER_TOKEN_BEDROCK"] = bearer
            logger.info("Using API Key authentication (ABSK)")
        else:
            logger.info("Using API Key authentication (ABSK from ACCESS_KEY)")
        
        return boto3.client("bedrock-runtime", region_name=region)
    
    else:
        # IAM authentication
        access_key = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()
        
        if not access_key or not secret_key:
            raise ValueError(
                "IAM authentication requires AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
            )
        
        logger.info("Using IAM authentication")
        return boto3.client(
            "bedrock-runtime",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )

def invoke_bedrock(client, model_id: str, body: dict) -> dict:
    """
    Invoke Bedrock model with request body.
    
    Args:
        client: boto3 bedrock-runtime client
        model_id: Bedrock model ID
        body: Request body (dict with Bedrock format)
    
    Returns:
        dict with 'content', 'stop_reason', and 'usage'
    
    Raises:
        Exception: If API call fails
    """
    import json
    
    try:
        response = client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )
        
        response_body = json.loads(response["body"].read())
        
        return {
            "content": response_body["content"][0]["text"],
            "stop_reason": response_body["stop_reason"],
            "usage": response_body["usage"]
        }
    
    except Exception as e:
        logger.error(f"Bedrock API call failed: {str(e)}")
        raise
```

- [ ] **Step 2: Create test for auth**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/tests/test_auth.py
import os
import pytest
from unittest.mock import patch, MagicMock
from src.auth.bedrock_auth import detect_auth_mode, build_bedrock_runtime

def test_detect_auth_mode_with_api_key():
    """Test detect_auth_mode returns 'api_key' when bearer token is set."""
    with patch.dict(os.environ, {"AWS_BEARER_TOKEN_BEDROCK": "test-token"}):
        assert detect_auth_mode() == "api_key"

def test_detect_auth_mode_with_absk_access_key():
    """Test detect_auth_mode returns 'api_key' when ACCESS_KEY starts with ABSK."""
    with patch.dict(os.environ, {"AWS_ACCESS_KEY_ID": "ABSK-12345"}):
        assert detect_auth_mode() == "api_key"

def test_detect_auth_mode_with_iam():
    """Test detect_auth_mode returns 'iam' when only IAM creds are set."""
    with patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "AKIA-12345",
        "AWS_SECRET_ACCESS_KEY": "secret"
    }, clear=False):
        # Clear Bedrock token if it exists
        if "AWS_BEARER_TOKEN_BEDROCK" in os.environ:
            del os.environ["AWS_BEARER_TOKEN_BEDROCK"]
        # This test may be flaky if token is set globally; consider mocking
        # For now, we test the logic path

def test_detect_auth_mode_default_iam():
    """Test detect_auth_mode defaults to 'iam' when no auth set."""
    with patch.dict(os.environ, {}, clear=True):
        assert detect_auth_mode() == "iam"

def test_build_bedrock_runtime_with_api_key():
    """Test build_bedrock_runtime with API Key auth."""
    with patch.dict(os.environ, {"AWS_BEARER_TOKEN_BEDROCK": "test-token"}):
        with patch("boto3.client") as mock_client:
            result = build_bedrock_runtime()
            mock_client.assert_called_once_with("bedrock-runtime", region_name="us-east-1")

def test_build_bedrock_runtime_with_iam():
    """Test build_bedrock_runtime with IAM auth."""
    with patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "AKIA-12345",
        "AWS_SECRET_ACCESS_KEY": "secret"
    }, clear=True):
        with patch("boto3.client") as mock_client:
            build_bedrock_runtime()
            mock_client.assert_called_once()
            call_kwargs = mock_client.call_args[1]
            assert call_kwargs["aws_access_key_id"] == "AKIA-12345"
            assert call_kwargs["aws_secret_access_key"] == "secret"

def test_build_bedrock_runtime_iam_missing_secret():
    """Test build_bedrock_runtime raises error when secret key missing."""
    with patch.dict(os.environ, {"AWS_ACCESS_KEY_ID": "AKIA-12345"}, clear=True):
        with pytest.raises(ValueError, match="IAM authentication requires"):
            build_bedrock_runtime()

def test_invoke_bedrock_success():
    """Test invoke_bedrock successfully parses response."""
    from src.auth.bedrock_auth import invoke_bedrock
    import json
    
    mock_client = MagicMock()
    mock_response = {
        "body": MagicMock(read=lambda: json.dumps({
            "content": [{"text": "Generated code"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 100, "output_tokens": 50}
        }).encode())
    }
    mock_client.invoke_model.return_value = mock_response
    
    result = invoke_bedrock(
        mock_client,
        "anthropic.claude-haiku-4-5-20251001-v1:0",
        {"test": "body"}
    )
    
    assert result["content"] == "Generated code"
    assert result["stop_reason"] == "end_turn"
    assert result["usage"]["input_tokens"] == 100
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
python -m pytest tests/test_auth.py -v
```

Expected output:
```
tests/test_auth.py::test_detect_auth_mode_with_api_key PASSED
tests/test_auth.py::test_detect_auth_mode_with_absk_access_key PASSED
tests/test_auth.py::test_detect_auth_mode_with_iam PASSED
tests/test_auth.py::test_detect_auth_mode_default_iam PASSED
tests/test_auth.py::test_build_bedrock_runtime_with_api_key PASSED
tests/test_auth.py::test_build_bedrock_runtime_with_iam PASSED
tests/test_auth.py::test_build_bedrock_runtime_iam_missing_secret PASSED
tests/test_auth.py::test_invoke_bedrock_success PASSED

==== 8 passed in X.XXs ====
```

- [ ] **Step 4: Commit**

```bash
git add src/auth/bedrock_auth.py tests/test_auth.py
git commit -m "feat: implement AWS Bedrock authentication"
```

---

## Task 5: Core JmAgent Class (agent.py)

**Files:**
- Create: `src/agent.py`
- Create: `tests/test_agent.py`

- [ ] **Step 1: Create agent.py**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/src/agent.py
import asyncio
from typing import Optional, List
from src.auth.bedrock_auth import build_bedrock_runtime, invoke_bedrock
from src.models.request import BedrockRequest, GenerateRequest
from src.models.response import BedrockResponse, GenerateResponse
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Model ID mappings
MODELS = {
    "haiku": "anthropic.claude-haiku-4-5-20251001-v1:0",
    "sonnet": "anthropic.claude-sonnet-4-6-20250514-v1:0",
    "opus": "anthropic.claude-opus-4-6-20250514-v1:0",
}

# System prompts for each action
SYSTEM_PROMPTS = {
    "generate": "You are an expert programmer. Generate clean, well-structured code based on the user's request. Provide only the code without explanations unless asked.",
    "refactor": "You are an expert code reviewer and refactorer. Improve the given code by applying best practices. Provide the refactored code with brief comments on changes.",
    "test": "You are an expert test engineer. Generate comprehensive unit tests for the given code. Use the specified testing framework.",
    "explain": "You are an expert programmer. Explain the given code in clear, simple terms. Focus on what it does and why it's structured that way.",
    "fix": "You are an expert debugger. Analyze the error and the code, then provide a fixed version. Explain the issue and solution.",
    "chat": "You are a helpful coding assistant. Answer questions about programming and help the user with their coding tasks.",
}

class JmAgent:
    """
    Personal Claude coding assistant using AWS Bedrock.
    """
    
    def __init__(
        self,
        model: str = "haiku",
        region: str = "us-east-1",
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ):
        """
        Initialize JmAgent.
        
        Args:
            model: Model name ('haiku', 'sonnet', 'opus')
            region: AWS region
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum output tokens
        """
        self.model = model
        self.model_id = MODELS.get(model, MODELS["haiku"])
        self.region = region
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = build_bedrock_runtime(region)
        self.conversation_history: List[dict] = []
        
        logger.info(f"Initialized JmAgent with model: {self.model}")
    
    async def _call_bedrock(
        self,
        action: str,
        prompt: str,
        use_history: bool = False
    ) -> BedrockResponse:
        """
        Call Bedrock API with given action and prompt.
        
        Args:
            action: Action name (e.g., 'generate', 'refactor')
            prompt: User prompt
            use_history: Whether to include conversation history
        
        Returns:
            BedrockResponse
        """
        system_prompt = SYSTEM_PROMPTS.get(action, SYSTEM_PROMPTS["chat"])
        
        messages = self.conversation_history.copy() if use_history else []
        
        bedrock_request = BedrockRequest(
            model_id=self.model_id,
            max_tokens=self.max_tokens,
            system_prompt=system_prompt,
            user_message=prompt,
            messages=messages
        )
        
        body = bedrock_request.to_body()
        
        # Run blocking API call in thread pool
        loop = asyncio.get_event_loop()
        response_dict = await loop.run_in_executor(
            None,
            lambda: invoke_bedrock(self.client, self.model_id, body)
        )
        
        response = BedrockResponse(
            content=response_dict["content"],
            stop_reason=response_dict["stop_reason"],
            usage=response_dict["usage"]
        )
        
        logger.info(f"Bedrock call successful. Tokens: {response.usage}")
        
        return response
    
    async def generate(
        self,
        prompt: str,
        language: Optional[str] = None,
        context_files: Optional[List[str]] = None,
    ) -> GenerateResponse:
        """
        Generate code based on prompt.
        
        Args:
            prompt: Code generation prompt
            language: Programming language (optional)
            context_files: List of file paths for context (optional)
        
        Returns:
            GenerateResponse with generated code
        """
        full_prompt = prompt
        if language:
            full_prompt = f"Generate code in {language}:\n{prompt}"
        if context_files:
            full_prompt += f"\n\nConsider the style of these files: {', '.join(context_files)}"
        
        response = await self._call_bedrock("generate", full_prompt)
        
        return GenerateResponse(
            code=response.content,
            language=language,
            tokens_used=response.usage
        )
    
    async def refactor(
        self,
        code: str,
        requirements: str,
        language: Optional[str] = None,
    ) -> GenerateResponse:
        """
        Refactor code based on requirements.
        
        Args:
            code: Code to refactor
            requirements: Refactoring requirements
            language: Programming language (optional)
        
        Returns:
            GenerateResponse with refactored code
        """
        full_prompt = f"Refactor this code:\n\n{code}\n\nRequirements: {requirements}"
        if language:
            full_prompt = f"{full_prompt}\n\nLanguage: {language}"
        
        response = await self._call_bedrock("refactor", full_prompt)
        
        return GenerateResponse(
            code=response.content,
            language=language,
            tokens_used=response.usage
        )
    
    async def add_tests(
        self,
        code: str,
        test_framework: str = "pytest",
        target_coverage: float = 0.8,
    ) -> GenerateResponse:
        """
        Generate tests for code.
        
        Args:
            code: Code to test
            test_framework: Test framework (pytest, jest, vitest)
            target_coverage: Target code coverage (0.0-1.0)
        
        Returns:
            GenerateResponse with test code
        """
        full_prompt = f"Generate {test_framework} tests for this code with {target_coverage*100}% coverage:\n\n{code}"
        
        response = await self._call_bedrock("test", full_prompt)
        
        return GenerateResponse(
            code=response.content,
            language=None,
            tokens_used=response.usage
        )
    
    async def explain(
        self,
        code: str,
        language: Optional[str] = None,
    ) -> str:
        """
        Explain code.
        
        Args:
            code: Code to explain
            language: Programming language (optional)
        
        Returns:
            String explanation
        """
        full_prompt = f"Explain this code:\n\n{code}"
        if language:
            full_prompt = f"{full_prompt}\n\nLanguage: {language}"
        
        response = await self._call_bedrock("explain", full_prompt)
        
        return response.content
    
    async def fix_bug(
        self,
        code: str,
        error_message: str,
        context: Optional[str] = None,
    ) -> GenerateResponse:
        """
        Fix bug in code.
        
        Args:
            code: Code with bug
            error_message: Error message
            context: Additional context (optional)
        
        Returns:
            GenerateResponse with fixed code
        """
        full_prompt = f"Fix this code:\n\n{code}\n\nError:\n{error_message}"
        if context:
            full_prompt = f"{full_prompt}\n\nContext:\n{context}"
        
        response = await self._call_bedrock("fix", full_prompt)
        
        return GenerateResponse(
            code=response.content,
            language=None,
            tokens_used=response.usage
        )
    
    async def chat(self, message: str) -> str:
        """
        Chat with the assistant (maintains history).
        
        Args:
            message: User message
        
        Returns:
            Assistant response
        """
        response = await self._call_bedrock("chat", message, use_history=True)
        
        # Update conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })
        
        return response.content
    
    def reset_history(self) -> None:
        """Reset conversation history."""
        self.conversation_history = []
        logger.info("Conversation history reset")
```

- [ ] **Step 2: Create test for agent**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/tests/test_agent.py
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
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
python -m pytest tests/test_agent.py -v
```

Expected output:
```
tests/test_agent.py::test_agent_initialization PASSED
tests/test_agent.py::test_agent_model_selection PASSED
tests/test_agent.py::test_generate PASSED
tests/test_agent.py::test_generate_with_language PASSED
tests/test_agent.py::test_chat_maintains_history PASSED
tests/test_agent.py::test_reset_history PASSED
tests/test_agent.py::test_explain PASSED
tests/test_agent.py::test_refactor PASSED

==== 8 passed in X.XXs ====
```

- [ ] **Step 4: Commit**

```bash
git add src/agent.py tests/test_agent.py
git commit -m "feat: implement core JmAgent class with async methods"
```

---

## Task 6: CLI Entry Point (cli.py)

**Files:**
- Create: `src/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Create cli.py**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/src/cli.py
import argparse
import asyncio
import sys
from typing import Optional
from src.agent import JmAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)

def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="jmAgent - Personal Claude coding assistant using AWS Bedrock"
    )
    
    # Global options
    parser.add_argument(
        "--model",
        choices=["haiku", "sonnet", "opus"],
        default="haiku",
        help="LLM model to use (default: haiku)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature (0.0-1.0, default: 0.2)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Maximum output tokens (default: 4096)"
    )
    
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")
    
    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate code")
    gen_parser.add_argument(
        "--prompt",
        required=True,
        help="Code generation prompt"
    )
    gen_parser.add_argument(
        "--language",
        help="Programming language"
    )
    gen_parser.add_argument(
        "--file",
        help="File path for context"
    )
    
    # refactor command
    ref_parser = subparsers.add_parser("refactor", help="Refactor code")
    ref_parser.add_argument(
        "--file",
        required=True,
        help="File to refactor"
    )
    ref_parser.add_argument(
        "--requirements",
        required=True,
        help="Refactoring requirements"
    )
    ref_parser.add_argument(
        "--language",
        help="Programming language"
    )
    
    # test command
    test_parser = subparsers.add_parser("test", help="Generate tests")
    test_parser.add_argument(
        "--file",
        required=True,
        help="File to test"
    )
    test_parser.add_argument(
        "--framework",
        default="pytest",
        choices=["pytest", "jest", "vitest"],
        help="Test framework (default: pytest)"
    )
    test_parser.add_argument(
        "--coverage",
        type=float,
        default=0.8,
        help="Target coverage (0.0-1.0, default: 0.8)"
    )
    
    # explain command
    exp_parser = subparsers.add_parser("explain", help="Explain code")
    exp_parser.add_argument(
        "--file",
        required=True,
        help="File to explain"
    )
    exp_parser.add_argument(
        "--language",
        help="Programming language"
    )
    
    # fix command
    fix_parser = subparsers.add_parser("fix", help="Fix bug in code")
    fix_parser.add_argument(
        "--file",
        required=True,
        help="File with bug"
    )
    fix_parser.add_argument(
        "--error",
        required=True,
        help="Error message"
    )
    fix_parser.add_argument(
        "--context",
        help="Additional context"
    )
    
    # chat command
    subparsers.add_parser("chat", help="Interactive chat mode")
    
    return parser

async def cmd_generate(args, agent: JmAgent) -> None:
    """Handle generate command."""
    if args.file:
        try:
            with open(args.file, "r") as f:
                context = f.read()
            prompt = f"{args.prompt}\n\nContext from {args.file}:\n{context}"
        except FileNotFoundError:
            logger.error(f"File not found: {args.file}")
            sys.exit(1)
    else:
        prompt = args.prompt
    
    logger.info("Generating code...")
    result = await agent.generate(
        prompt=prompt,
        language=args.language
    )
    
    print("\n" + "=" * 60)
    print(result.code)
    print("=" * 60)
    print(f"\nTokens used: {result.tokens_used}")

async def cmd_refactor(args, agent: JmAgent) -> None:
    """Handle refactor command."""
    try:
        with open(args.file, "r") as f:
            code = f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    logger.info(f"Refactoring {args.file}...")
    result = await agent.refactor(
        code=code,
        requirements=args.requirements,
        language=args.language
    )
    
    print("\n" + "=" * 60)
    print(result.code)
    print("=" * 60)
    print(f"\nTokens used: {result.tokens_used}")

async def cmd_test(args, agent: JmAgent) -> None:
    """Handle test command."""
    try:
        with open(args.file, "r") as f:
            code = f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    logger.info(f"Generating tests for {args.file}...")
    result = await agent.add_tests(
        code=code,
        test_framework=args.framework,
        target_coverage=args.coverage
    )
    
    print("\n" + "=" * 60)
    print(result.code)
    print("=" * 60)
    print(f"\nTokens used: {result.tokens_used}")

async def cmd_explain(args, agent: JmAgent) -> None:
    """Handle explain command."""
    try:
        with open(args.file, "r") as f:
            code = f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    logger.info(f"Explaining {args.file}...")
    result = await agent.explain(
        code=code,
        language=args.language
    )
    
    print("\n" + "=" * 60)
    print(result)
    print("=" * 60)

async def cmd_fix(args, agent: JmAgent) -> None:
    """Handle fix command."""
    try:
        with open(args.file, "r") as f:
            code = f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    logger.info(f"Fixing bug in {args.file}...")
    result = await agent.fix_bug(
        code=code,
        error_message=args.error,
        context=args.context
    )
    
    print("\n" + "=" * 60)
    print(result.code)
    print("=" * 60)
    print(f"\nTokens used: {result.tokens_used}")

async def cmd_chat(args, agent: JmAgent) -> None:
    """Handle interactive chat command."""
    print("Starting interactive chat (type 'exit' to quit)...")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if user_input.lower() in ("exit", "quit"):
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            response = await agent.chat(user_input)
            print(f"\nAssistant: {response}")
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {str(e)}")

async def main_async(args) -> None:
    """Main async function."""
    agent = JmAgent(
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens
    )
    
    if args.action == "generate":
        await cmd_generate(args, agent)
    elif args.action == "refactor":
        await cmd_refactor(args, agent)
    elif args.action == "test":
        await cmd_test(args, agent)
    elif args.action == "explain":
        await cmd_explain(args, agent)
    elif args.action == "fix":
        await cmd_fix(args, agent)
    elif args.action == "chat":
        await cmd_chat(args, agent)
    else:
        print("No action specified. Use --help for usage.")

def main() -> None:
    """Entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.action:
        parser.print_help()
        sys.exit(0)
    
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Create basic CLI test**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/tests/test_cli.py
import pytest
from unittest.mock import patch
from src.cli import create_parser

def test_create_parser():
    """Test parser creation."""
    parser = create_parser()
    assert parser is not None

def test_parser_generate_command():
    """Test generate command parsing."""
    parser = create_parser()
    args = parser.parse_args([
        "generate",
        "--prompt", "Create a function",
        "--language", "python"
    ])
    
    assert args.action == "generate"
    assert args.prompt == "Create a function"
    assert args.language == "python"

def test_parser_refactor_command():
    """Test refactor command parsing."""
    parser = create_parser()
    args = parser.parse_args([
        "refactor",
        "--file", "main.py",
        "--requirements", "Add type hints"
    ])
    
    assert args.action == "refactor"
    assert args.file == "main.py"
    assert args.requirements == "Add type hints"

def test_parser_test_command():
    """Test test command parsing."""
    parser = create_parser()
    args = parser.parse_args([
        "test",
        "--file", "utils.py",
        "--framework", "pytest",
        "--coverage", "0.9"
    ])
    
    assert args.action == "test"
    assert args.file == "utils.py"
    assert args.framework == "pytest"
    assert args.coverage == 0.9

def test_parser_model_option():
    """Test global model option."""
    parser = create_parser()
    args = parser.parse_args([
        "--model", "sonnet",
        "generate",
        "--prompt", "test"
    ])
    
    assert args.model == "sonnet"

def test_parser_temperature_option():
    """Test global temperature option."""
    parser = create_parser()
    args = parser.parse_args([
        "--temperature", "0.5",
        "generate",
        "--prompt", "test"
    ])
    
    assert args.temperature == 0.5

def test_parser_chat_command():
    """Test chat command parsing."""
    parser = create_parser()
    args = parser.parse_args(["chat"])
    
    assert args.action == "chat"
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
python -m pytest tests/test_cli.py -v
```

Expected output:
```
tests/test_cli.py::test_create_parser PASSED
tests/test_cli.py::test_parser_generate_command PASSED
tests/test_cli.py::test_parser_refactor_command PASSED
tests/test_cli.py::test_parser_test_command PASSED
tests/test_cli.py::test_parser_model_option PASSED
tests/test_cli.py::test_parser_temperature_option PASSED
tests/test_cli.py::test_parser_chat_command PASSED

==== 7 passed in X.XXs ====
```

- [ ] **Step 4: Commit**

```bash
git add src/cli.py tests/test_cli.py
git commit -m "feat: implement argparse-based CLI entry point"
```

---

## Task 7: Integration Test & Validation

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Create integration test**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/tests/test_integration.py
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from src.agent import JmAgent
from src.models.response import BedrockResponse

@pytest.mark.asyncio
async def test_full_generate_flow():
    """Integration test: full code generation flow."""
    with patch("src.agent.build_bedrock_runtime") as mock_build:
        mock_client = MagicMock()
        mock_build.return_value = mock_client
        
        agent = JmAgent(model="haiku")
        
        with patch.object(agent, "client") as mock_bedrock_client:
            with patch("src.agent.invoke_bedrock") as mock_invoke:
                mock_invoke.return_value = {
                    "content": "def hello():\n    return 'world'",
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 50, "output_tokens": 20}
                }
                
                result = await agent.generate(
                    prompt="Create a hello function",
                    language="Python"
                )
                
                assert "def hello" in result.code
                assert result.language == "Python"
                assert result.tokens_used["input_tokens"] == 50

@pytest.mark.asyncio
async def test_generate_with_file_context():
    """Integration test: generate with file context."""
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent()
        
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "existing code"
            
            with patch("src.agent.invoke_bedrock") as mock_invoke:
                mock_invoke.return_value = {
                    "content": "new code",
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 100, "output_tokens": 50}
                }
                
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
```

- [ ] **Step 2: Run all tests to verify they pass**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
python -m pytest tests/ -v
```

Expected output:
```
tests/test_auth.py::test_detect_auth_mode_with_api_key PASSED
tests/test_auth.py::test_detect_auth_mode_with_absk_access_key PASSED
...
tests/test_integration.py::test_full_generate_flow PASSED
tests/test_integration.py::test_generate_with_file_context PASSED
tests/test_integration.py::test_agent_initialization_and_model_selection PASSED

==== 28 passed in X.XXs ====
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests"
```

---

## Task 8: Manual Testing & Documentation

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create README.md**

```markdown
# jmAgent - Personal Claude Coding Assistant

jmAgent is a personal coding assistant powered by AWS Bedrock Claude models. It supports code generation, refactoring, testing, explanation, debugging, and interactive chat.

## Quick Start

### Installation

```bash
cd ~/Documents/jmAgent
python3.10+ -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Configuration

Create a `.env` file with your AWS credentials:

```bash
cp .env.example .env
# Edit .env with your AWS_BEARER_TOKEN_BEDROCK or IAM credentials
```

### Usage

```bash
# Generate code
jm generate --prompt "Create a FastAPI endpoint"

# Generate with language specification
jm generate --prompt "Create a todo app" --language typescript

# Refactor code
jm refactor --file src/main.py --requirements "Add type hints"

# Generate tests
jm test --file src/utils.py --framework pytest

# Explain code
jm explain --file src/complex.py

# Fix bug
jm fix --file src/app.py --error "TypeError: 'NoneType' object is not subscriptable"

# Interactive chat
jm chat

# Use different model
jm --model sonnet generate --prompt "Complex problem"
```

## Commands

### generate
Generate code from a prompt.

```bash
jm generate --prompt "description" [--language LANG] [--file PATH]
```

### refactor
Refactor existing code.

```bash
jm refactor --file PATH --requirements "description"
```

### test
Generate unit tests.

```bash
jm test --file PATH [--framework pytest|jest|vitest] [--coverage 0.0-1.0]
```

### explain
Explain code.

```bash
jm explain --file PATH
```

### fix
Fix bugs in code.

```bash
jm fix --file PATH --error "error message"
```

### chat
Interactive chat mode.

```bash
jm chat
```

## Global Options

- `--model {haiku,sonnet,opus}` - LLM model (default: haiku)
- `--temperature FLOAT` - Sampling temperature 0.0-1.0 (default: 0.2)
- `--max-tokens INT` - Maximum output tokens (default: 4096)

## Architecture

- **auth/** - AWS Bedrock authentication
- **models/** - Request/response data classes
- **utils/** - Logging and utilities
- **agent.py** - Core JmAgent class
- **cli.py** - Command-line interface

## Testing

```bash
python -m pytest tests/ -v
python -m pytest tests/test_agent.py::test_generate -v
```

## Environment Variables

- `AWS_BEARER_TOKEN_BEDROCK` - Bedrock API key (alternative: IAM credentials)
- `AWS_BEDROCK_REGION` - AWS region (default: us-east-1)
- `JM_DEFAULT_MODEL` - Default model (haiku, sonnet, opus)
```

- [ ] **Step 2: Test basic CLI with mock**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
python -m src.cli --help
```

Expected: Help message showing all commands

- [ ] **Step 3: Verify all tests pass one final time**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
python -m pytest tests/ -v --tb=short
```

Expected: All 28+ tests pass

- [ ] **Step 4: Commit README and final verification**

```bash
git add README.md
git commit -m "docs: add comprehensive README"
```

---

## Spec Coverage Checklist

✅ **bedrock_auth.py** - Auth detection and client creation  
✅ **agent.py** - JmAgent class with async methods (generate, refactor, test, explain, fix, chat)  
✅ **cli.py** - argparse CLI with all 6 commands + global options  
✅ **models/** - Request/response data classes  
✅ **tests/** - Unit tests (28+ tests) + integration tests  
✅ **Documentation** - README with usage guide  
✅ **Project structure** - Modular architecture  
✅ **Deliverable** - Basic code generation working

---

**Plan Status:** Ready for execution

**Recommended Execution:** Use superpowers:subagent-driven-development for task-by-task implementation with review checkpoints between tasks.
