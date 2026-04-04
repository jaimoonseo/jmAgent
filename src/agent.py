import asyncio
import os
import time
from pathlib import Path
from typing import Optional, List, Callable, Dict
from src.auth.bedrock_auth import build_bedrock_runtime, invoke_bedrock, invoke_bedrock_streaming
from src.models.request import BedrockRequest, GenerateRequest
from src.models.response import BedrockResponse, GenerateResponse
from src.utils.logger import get_logger
from src.prompts.context_loader import ProjectContext, load_project_context, load_multiple_files
from src.prompts.context_enhancer import ContextEnhancer
from src.streaming.stream_handler import StreamCollector
from src.formatting.formatter import CodeFormatter
from src.monitoring.metrics import MetricsCollector

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
        project_context: Optional[ProjectContext] = None,
    ):
        """
        Initialize JmAgent.

        Args:
            model: Model name ('haiku', 'sonnet', 'opus')
            region: AWS region
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum output tokens
            project_context: Optional project context for improved code generation
        """
        self.model = model
        self.model_id = MODELS.get(model, MODELS["haiku"])
        self.region = region
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = build_bedrock_runtime(region)
        self.conversation_history: List[dict] = []
        self.project_context = project_context
        self.formatter = CodeFormatter()
        self.metrics = MetricsCollector()

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
        start_time = time.time()

        try:
            # Enhance prompt with project context if available
            if self.project_context:
                enhancer = ContextEnhancer(self.project_context)
                if action == "generate":
                    prompt = enhancer.enhance_generate_prompt(prompt)
                elif action == "refactor":
                    prompt = enhancer.enhance_refactor_prompt(prompt)
                elif action == "test":
                    prompt = enhancer.enhance_test_prompt(prompt)
                elif action == "explain":
                    prompt = enhancer.enhance_explain_prompt(prompt)
                elif action == "fix":
                    prompt = enhancer.enhance_fix_prompt(prompt)

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

            # Record metric
            response_time = time.time() - start_time
            self.metrics.record_metric(
                action_type=action,
                response_time=response_time,
                input_tokens=response.usage.get("input_tokens", 0),
                output_tokens=response.usage.get("output_tokens", 0),
                success=True
            )

            return response

        except Exception as e:
            # Record failed metric
            response_time = time.time() - start_time
            self.metrics.record_metric(
                action_type=action,
                response_time=response_time,
                input_tokens=0,
                output_tokens=0,
                success=False,
                error=str(e)
            )
            raise

    async def generate(
        self,
        prompt: str,
        language: Optional[str] = None,
        context_files: Optional[List[str]] = None,
        format_code: bool = False,
    ) -> GenerateResponse:
        """
        Generate code based on prompt.

        Args:
            prompt: Code generation prompt
            language: Programming language (optional)
            context_files: List of file paths for context (optional)
            format_code: Whether to format the generated code (default: False)

        Returns:
            GenerateResponse with generated code
        """
        full_prompt = prompt
        if language:
            full_prompt = f"Generate code in {language}:\n{prompt}"
        if context_files:
            full_prompt += f"\n\nConsider the style of these files: {', '.join(context_files)}"

        response = await self._call_bedrock("generate", full_prompt)

        code = response.content
        if format_code:
            code = self.formatter.format(code, language=language)

        return GenerateResponse(
            code=code,
            language=language,
            tokens_used=response.usage
        )

    async def generate_streaming(
        self,
        prompt: str,
        language: Optional[str] = None,
        context_files: Optional[List[str]] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
        format_code: bool = False,
    ) -> GenerateResponse:
        """
        Generate code with streaming output and optional callback for chunks.

        Args:
            prompt: Code generation prompt
            language: Programming language (optional)
            context_files: List of file paths for context (optional)
            on_chunk: Optional callback function called with each text chunk
            format_code: Whether to format the generated code (default: False)

        Returns:
            GenerateResponse with complete generated code
        """
        full_prompt = prompt
        if language:
            full_prompt = f"Generate code in {language}:\n{prompt}"
        if context_files:
            full_prompt += f"\n\nConsider the style of these files: {', '.join(context_files)}"

        # Enhance prompt with project context if available
        if self.project_context:
            enhancer = ContextEnhancer(self.project_context)
            full_prompt = enhancer.enhance_generate_prompt(full_prompt)

        system_prompt = SYSTEM_PROMPTS.get("generate", SYSTEM_PROMPTS["chat"])

        bedrock_request = BedrockRequest(
            model_id=self.model_id,
            max_tokens=self.max_tokens,
            system_prompt=system_prompt,
            user_message=full_prompt,
            messages=[]
        )

        body = bedrock_request.to_body()

        # Stream from Bedrock and collect events
        collector = StreamCollector()
        loop = asyncio.get_event_loop()

        try:
            # Run streaming in thread pool
            await loop.run_in_executor(
                None,
                self._stream_and_collect,
                body,
                collector,
                on_chunk
            )
        except Exception as e:
            logger.error(f"Streaming call failed: {str(e)}")
            raise

        # Finalize and return response
        code = collector.finalize()

        # Format code if requested
        if format_code:
            code = self.formatter.format(code, language=language)

        # For now, we estimate tokens (would need actual token counting for accuracy)
        stats = collector.handler.get_stats()
        estimated_usage = {
            "input_tokens": 100,  # Placeholder - would use real token count
            "output_tokens": stats["token_count"]
        }

        return GenerateResponse(
            code=code,
            language=language,
            tokens_used=estimated_usage
        )

    def _stream_and_collect(
        self,
        body: dict,
        collector: StreamCollector,
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> None:
        """
        Helper method to stream from Bedrock and collect events.
        Runs in thread pool since streaming is blocking.

        Args:
            body: Request body for Bedrock
            collector: StreamCollector to accumulate events
            on_chunk: Optional callback for each chunk
        """
        try:
            for event in invoke_bedrock_streaming(self.client, self.model_id, body):
                collector.add_event(event)

                # Call the callback if provided and we got text
                if on_chunk:
                    text = collector.handler.get_buffer()
                    # Only callback with new content (simplified - calls every time)
                    # Real implementation might track last sent position
                    if text:
                        on_chunk(text)

        except Exception as e:
            logger.error(f"Error during streaming: {str(e)}")
            raise

    async def refactor(
        self,
        code: str,
        requirements: str,
        language: Optional[str] = None,
        format_code: bool = False,
    ) -> GenerateResponse:
        """
        Refactor code based on requirements.

        Args:
            code: Code to refactor
            requirements: Refactoring requirements
            language: Programming language (optional)
            format_code: Whether to format the refactored code (default: False)

        Returns:
            GenerateResponse with refactored code
        """
        full_prompt = f"Refactor this code:\n\n{code}\n\nRequirements: {requirements}"
        if language:
            full_prompt = f"{full_prompt}\n\nLanguage: {language}"

        response = await self._call_bedrock("refactor", full_prompt)

        refactored_code = response.content
        if format_code:
            refactored_code = self.formatter.format(refactored_code, language=language)

        return GenerateResponse(
            code=refactored_code,
            language=language,
            tokens_used=response.usage
        )

    async def refactor_multiple(
        self,
        file_paths: List[str],
        requirements: str,
        language: Optional[str] = None,
        format_code: bool = False,
    ) -> Dict[str, GenerateResponse]:
        """
        Refactor multiple files together.

        Args:
            file_paths: List of file paths to refactor
            requirements: Refactoring requirements
            language: Programming language (optional)
            format_code: Whether to format the refactored code (default: False)

        Returns:
            Dict mapping file_path -> GenerateResponse with refactored code
        """
        # Load all files as context
        files_context = load_multiple_files(file_paths)

        full_prompt = f"Refactor these files:\n\n{files_context}\n\nRequirements: {requirements}"
        if language:
            full_prompt = f"{full_prompt}\n\nLanguage: {language}"

        response = await self._call_bedrock("refactor", full_prompt)

        # Parse response to extract per-file code
        # Look for "## File: <filename>" markers
        result = {}
        content = response.content
        lines = content.split("\n")
        current_file = None
        current_code = []

        for line in lines:
            if line.startswith("## File:"):
                # Save previous file if any
                if current_file and current_code:
                    refactored = "\n".join(current_code).strip()
                    if format_code:
                        refactored = self.formatter.format(refactored, language=language)
                    result[current_file] = GenerateResponse(
                        code=refactored,
                        language=language,
                        tokens_used=response.usage
                    )

                # Extract new filename
                # Format: "## File: filename.py" or "## File: filename.py (size bytes)"
                filename = line.replace("## File:", "").strip()
                # Remove size info if present
                if "(" in filename:
                    filename = filename[:filename.index("(")].strip()
                current_file = filename
                current_code = []
            elif current_file:
                # Skip code block markers
                if line.strip() not in ("```", "```python", "```javascript", "```typescript"):
                    current_code.append(line)

        # Save last file
        if current_file and current_code:
            refactored = "\n".join(current_code).strip()
            if format_code:
                refactored = self.formatter.format(refactored, language=language)
            result[current_file] = GenerateResponse(
                code=refactored,
                language=language,
                tokens_used=response.usage
            )

        # If no files were parsed, return empty dict or wrap entire response
        if not result and file_paths:
            result[file_paths[0]] = GenerateResponse(
                code=response.content,
                language=language,
                tokens_used=response.usage
            )

        return result

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

    async def test_multiple(
        self,
        file_paths: List[str],
        test_framework: str = "pytest",
        target_coverage: float = 0.8,
    ) -> GenerateResponse:
        """
        Generate tests for multiple files together.

        Args:
            file_paths: List of file paths to test
            test_framework: Test framework (pytest, jest, vitest)
            target_coverage: Target code coverage (0.0-1.0)

        Returns:
            GenerateResponse with test code covering all files
        """
        # Load all files as context
        files_context = load_multiple_files(file_paths)

        full_prompt = f"Generate {test_framework} tests for these files with {target_coverage*100}% coverage:\n\n{files_context}"

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

    def get_metrics(self) -> MetricsCollector:
        """
        Get the metrics collector instance.

        Returns:
            MetricsCollector instance
        """
        return self.metrics

    def get_metrics_summary(self) -> Dict:
        """
        Get a summary of all collected metrics.

        Returns:
            Dictionary with metrics summary
        """
        return self.metrics.get_all_stats()

    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        self.metrics.clear()
        logger.info("Metrics cleared")
