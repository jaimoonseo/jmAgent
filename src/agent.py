import asyncio
import os
from typing import Optional, List
from src.auth.bedrock_auth import build_bedrock_runtime, invoke_bedrock
from src.models.request import BedrockRequest, GenerateRequest
from src.models.response import BedrockResponse, GenerateResponse
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Model ID mappings - Supports both inference profiles and on-demand models
MODELS = {
    "haiku": os.getenv("AWS_BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0"),
    "sonnet": "us.anthropic.claude-sonnet-4-6-20250514-v1:0",
    "opus": "us.anthropic.claude-opus-4-6-20250514-v1:0",
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
