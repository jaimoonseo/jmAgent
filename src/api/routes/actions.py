"""Action endpoints for code generation, refactoring, testing, etc."""

import time
import uuid
import json
from typing import Dict, Optional, AsyncGenerator
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from src.logging.logger import StructuredLogger
from src.api.models import APIResponse
from src.api.exceptions import ValidationError, AuthenticationError, NotFoundError, ServerError
from src.api.schemas.requests import (
    GenerateRequest,
    RefactorRequest,
    TestRequest,
    ExplainRequest,
    FixRequest,
    ChatRequest,
)
from src.api.schemas.responses import (
    GenerateResponse,
    RefactorResponse,
    TestResponse,
    ExplainResponse,
    FixResponse,
    ChatResponse,
    TokenUsage,
)
from src.api.security.auth import (
    verify_token,
    JwtSettings,
    APIKeyValidator,
)
from src.agent import JmAgent

logger = StructuredLogger(__name__)

router = APIRouter()

# Conversation history storage (in-memory for Phase 5, persistent in Phase 6)
conversation_store: Dict[str, list] = {}


def get_agent() -> JmAgent:
    """
    Dependency injection for JmAgent instance.
    In production, this could create a shared instance or manage a pool.

    Returns:
        JmAgent: Configured agent instance
    """
    return JmAgent(
        model="haiku",
        region="us-east-1",
        temperature=0.2,
        max_tokens=4096,
    )


def validate_file_exists(file_path: str, project_root: str = ".") -> Path:
    """
    Validate that a file exists and is readable.

    SECURITY: Prevents path traversal attacks including symlink escapes by:
    - Checking for ".." sequences
    - Checking for absolute paths
    - Resolving symlinks and verifying the real path is within project root

    Args:
        file_path: Relative file path
        project_root: Project root directory

    Returns:
        Path: Absolute path to the file

    Raises:
        ValidationError: If file doesn't exist, is not readable, or attempts path traversal
    """
    # Basic checks for obvious traversal attempts
    if ".." in file_path or file_path.startswith("/"):
        raise ValidationError(f"Invalid file path: {file_path}")

    abs_path = Path(project_root) / file_path

    try:
        # Resolve to absolute path and follow all symlinks
        # This gets the canonical path, preventing symlink escapes
        resolved_path = abs_path.resolve()
        project_root_resolved = Path(project_root).resolve()

        # Verify the resolved path is within project root
        # This prevents symlink attacks like: safe_file.py -> ../../etc/passwd
        try:
            resolved_path.relative_to(project_root_resolved)
        except ValueError:
            raise ValidationError(
                f"File path outside project root: {file_path} resolves to {resolved_path}"
            )

        if not resolved_path.exists():
            raise ValidationError(f"File not found: {file_path}")
        if not resolved_path.is_file():
            raise ValidationError(f"Path is not a file: {file_path}")
        if not resolved_path.stat().st_size <= 1_000_000:  # 1MB limit
            raise ValidationError(f"File is too large (max 1MB): {file_path}")
        # Check readability
        resolved_path.read_bytes()
        return resolved_path
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Cannot read file {file_path}: {str(e)}")


async def get_current_user_flexible(
    request: Request,
) -> dict:
    """
    Flexible auth dependency that tries JWT first, then API key.
    Requires at least one valid authentication method.

    Args:
        request: FastAPI request object

    Returns:
        Dictionary with user info

    Raises:
        HTTPException: If neither auth method is valid
    """
    import os

    # Try JWT from Authorization header first
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        try:
            secret_key = os.getenv("JMAGENT_API_JWT_SECRET_KEY")
            if secret_key:
                settings = JwtSettings(secret_key=secret_key)
            else:
                settings = JwtSettings()
            payload = verify_token(token, settings=settings)
            return payload
        except Exception as e:
            logger.debug(f"JWT verification failed: {str(e)}")
            pass  # Try API key next

    # Try API key from x-api-key header
    api_key = request.headers.get("x-api-key")
    if api_key:
        try:
            validator = APIKeyValidator()
            if validator.validate(api_key):
                return {
                    "user_id": "api_user",
                    "agent_id": "api_agent",
                    "auth_type": "api_key",
                }
        except Exception:
            pass

    # No valid auth found
    raise HTTPException(status_code=403, detail="Authentication required")


@router.post(
    "/agent/generate",
    response_model=APIResponse,
    summary="Generate Code",
    tags=["Actions"],
)
async def generate(
    request: GenerateRequest,
    current_user: dict = Depends(get_current_user_flexible),
    agent: JmAgent = Depends(get_agent),
) -> APIResponse:
    """
    Generate code based on a prompt.

    Request:
        - prompt: Code generation prompt (required)
        - model: Claude model (optional, default: haiku)
        - max_tokens: Maximum output tokens (optional, default: 4096)
        - temperature: Sampling temperature (optional, default: 0.2)

    Response:
        - generated_code: Generated code
        - model_used: Model used for generation
        - tokens_used: Token usage breakdown
        - execution_time: Execution time in seconds
        - success: Whether the action succeeded
    """
    start_time = time.time()

    try:
        logger.info(
            "Generate action started",
            extra={
                "user_id": current_user.get("user_id"),
                "model": request.model.value,
            },
        )

        # Update agent model and parameters
        agent.model = request.model.value
        agent.max_tokens = request.max_tokens
        agent.temperature = request.temperature

        # Call agent
        response = await agent.generate(prompt=request.prompt)

        execution_time = time.time() - start_time

        result = GenerateResponse(
            generated_code=response.code,
            model_used=request.model.value,
            tokens_used=TokenUsage(
                input=response.tokens_used.get("input_tokens", 0),
                output=response.tokens_used.get("output_tokens", 0),
            ),
            execution_time=execution_time,
            success=True,
        )

        logger.info(
            "Generate action completed",
            extra={
                "user_id": current_user.get("user_id"),
                "execution_time": execution_time,
                "tokens": response.tokens_used,
            },
        )

        return APIResponse(success=True, data=result)

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(
            "Generate action failed",
            extra={
                "user_id": current_user.get("user_id"),
                "error": str(e),
                "execution_time": execution_time,
            },
        )
        raise ServerError(f"Code generation failed: {str(e)}")


@router.post(
    "/agent/refactor",
    response_model=APIResponse,
    summary="Refactor Code",
    tags=["Actions"],
)
async def refactor(
    request: RefactorRequest,
    current_user: dict = Depends(get_current_user_flexible),
    agent: JmAgent = Depends(get_agent),
) -> APIResponse:
    """
    Refactor code based on requirements.

    Request:
        - file_path: Path to file to refactor (required, relative to project root)
        - requirements: Refactoring requirements (required)
        - model: Claude model (optional, default: haiku)

    Response:
        - refactored_code: Refactored code
        - changes_summary: Summary of changes
        - tokens_used: Token usage breakdown
        - execution_time: Execution time in seconds
        - success: Whether the action succeeded
    """
    start_time = time.time()

    try:
        logger.info(
            "Refactor action started",
            extra={
                "user_id": current_user.get("user_id"),
                "file_path": request.file_path,
            },
        )

        # Validate file exists and read it
        file_path = validate_file_exists(request.file_path)
        code_content = file_path.read_text()

        # Update agent model
        agent.model = request.model.value

        # Call agent
        response = await agent.refactor(
            code=code_content,
            requirements=request.requirements,
        )

        execution_time = time.time() - start_time

        result = RefactorResponse(
            refactored_code=response.code,
            changes_summary=f"Refactored {request.file_path} with requirements: {request.requirements}",
            tokens_used=TokenUsage(
                input=response.tokens_used.get("input_tokens", 0),
                output=response.tokens_used.get("output_tokens", 0),
            ),
            execution_time=execution_time,
            success=True,
        )

        logger.info(
            "Refactor action completed",
            extra={
                "user_id": current_user.get("user_id"),
                "file_path": request.file_path,
                "execution_time": execution_time,
            },
        )

        return APIResponse(success=True, data=result)

    except ValidationError:
        raise
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(
            "Refactor action failed",
            extra={
                "user_id": current_user.get("user_id"),
                "file_path": request.file_path,
                "error": str(e),
            },
        )
        raise ServerError(f"Refactoring failed: {str(e)}")


@router.post(
    "/agent/test",
    response_model=APIResponse,
    summary="Generate Tests",
    tags=["Actions"],
)
async def test(
    request: TestRequest,
    current_user: dict = Depends(get_current_user_flexible),
    agent: JmAgent = Depends(get_agent),
) -> APIResponse:
    """
    Generate tests for code.

    Request:
        - file_path: Path to file to test (required, relative to project root)
        - framework: Test framework to use (required: pytest, vitest, jest)
        - model: Claude model (optional, default: haiku)

    Response:
        - test_code: Generated test code
        - coverage_estimate: Estimated code coverage
        - tokens_used: Token usage breakdown
        - execution_time: Execution time in seconds
        - success: Whether the action succeeded
    """
    start_time = time.time()

    try:
        logger.info(
            "Test action started",
            extra={
                "user_id": current_user.get("user_id"),
                "file_path": request.file_path,
                "framework": request.framework.value,
            },
        )

        # Validate file exists and read it
        file_path = validate_file_exists(request.file_path)
        code_content = file_path.read_text()

        # Update agent model
        agent.model = request.model.value

        # Call agent
        response = await agent.add_tests(
            code=code_content,
            test_framework=request.framework.value,
        )

        execution_time = time.time() - start_time

        result = TestResponse(
            test_code=response.code,
            coverage_estimate="80%",  # Placeholder
            tokens_used=TokenUsage(
                input=response.tokens_used.get("input_tokens", 0),
                output=response.tokens_used.get("output_tokens", 0),
            ),
            execution_time=execution_time,
            success=True,
        )

        logger.info(
            "Test action completed",
            extra={
                "user_id": current_user.get("user_id"),
                "file_path": request.file_path,
                "execution_time": execution_time,
            },
        )

        return APIResponse(success=True, data=result)

    except ValidationError:
        raise
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(
            "Test action failed",
            extra={
                "user_id": current_user.get("user_id"),
                "file_path": request.file_path,
                "error": str(e),
            },
        )
        raise ServerError(f"Test generation failed: {str(e)}")


@router.post(
    "/agent/explain",
    response_model=APIResponse,
    summary="Explain Code",
    tags=["Actions"],
)
async def explain(
    request: ExplainRequest,
    current_user: dict = Depends(get_current_user_flexible),
    agent: JmAgent = Depends(get_agent),
) -> APIResponse:
    """
    Explain code and identify key concepts.

    Request:
        - file_path: Path to file to explain (required, relative to project root)
        - focus_area: Specific area to focus on (optional)
        - language: Explanation language (optional, default: english)

    Response:
        - explanation: Code explanation
        - key_concepts: List of key concepts
        - tokens_used: Token usage breakdown
        - execution_time: Execution time in seconds
        - success: Whether the action succeeded
    """
    start_time = time.time()

    try:
        logger.info(
            "Explain action started",
            extra={
                "user_id": current_user.get("user_id"),
                "file_path": request.file_path,
                "language": request.language.value,
            },
        )

        # Validate file exists and read it
        file_path = validate_file_exists(request.file_path)
        code_content = file_path.read_text()

        # Build prompt
        prompt = f"Explain this code:\n\n{code_content}"
        if request.focus_area:
            prompt += f"\n\nFocus on: {request.focus_area}"
        if request.language != "english":
            prompt += f"\n\nProvide explanation in {request.language.value}."

        # Call agent
        response = await agent._call_bedrock("explain", prompt)

        execution_time = time.time() - start_time

        # Extract key concepts (simple approach: split by common keywords)
        key_concepts = [
            concept.strip()
            for concept in response.content.split(",")[:5]  # First 5 concepts
        ]

        result = ExplainResponse(
            explanation=response.content,
            key_concepts=key_concepts,
            tokens_used=TokenUsage(
                input=response.usage.get("input_tokens", 0),
                output=response.usage.get("output_tokens", 0),
            ),
            execution_time=execution_time,
            success=True,
        )

        logger.info(
            "Explain action completed",
            extra={
                "user_id": current_user.get("user_id"),
                "file_path": request.file_path,
                "execution_time": execution_time,
            },
        )

        return APIResponse(success=True, data=result)

    except ValidationError:
        raise
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(
            "Explain action failed",
            extra={
                "user_id": current_user.get("user_id"),
                "file_path": request.file_path,
                "error": str(e),
            },
        )
        raise ServerError(f"Code explanation failed: {str(e)}")


@router.post(
    "/agent/fix",
    response_model=APIResponse,
    summary="Fix Bug",
    tags=["Actions"],
)
async def fix(
    request: FixRequest,
    current_user: dict = Depends(get_current_user_flexible),
    agent: JmAgent = Depends(get_agent),
) -> APIResponse:
    """
    Fix a bug in code based on error message.

    Request:
        - file_path: Path to file to fix (required, relative to project root)
        - error_message: Error message or description (required)
        - model: Claude model (optional, default: haiku)

    Response:
        - fixed_code: Fixed code
        - fix_summary: Summary of the bug and fix
        - tokens_used: Token usage breakdown
        - execution_time: Execution time in seconds
        - success: Whether the action succeeded
    """
    start_time = time.time()

    try:
        logger.info(
            "Fix action started",
            extra={
                "user_id": current_user.get("user_id"),
                "file_path": request.file_path,
            },
        )

        # Validate file exists and read it
        file_path = validate_file_exists(request.file_path)
        code_content = file_path.read_text()

        # Update agent model
        agent.model = request.model.value

        # Build prompt
        prompt = f"Fix this code:\n\n{code_content}\n\nError: {request.error_message}"

        # Call agent
        response = await agent._call_bedrock("fix", prompt)

        execution_time = time.time() - start_time

        result = FixResponse(
            fixed_code=response.content,
            fix_summary=f"Fixed error in {request.file_path}: {request.error_message}",
            tokens_used=TokenUsage(
                input=response.usage.get("input_tokens", 0),
                output=response.usage.get("output_tokens", 0),
            ),
            execution_time=execution_time,
            success=True,
        )

        logger.info(
            "Fix action completed",
            extra={
                "user_id": current_user.get("user_id"),
                "file_path": request.file_path,
                "execution_time": execution_time,
            },
        )

        return APIResponse(success=True, data=result)

    except ValidationError:
        raise
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(
            "Fix action failed",
            extra={
                "user_id": current_user.get("user_id"),
                "file_path": request.file_path,
                "error": str(e),
            },
        )
        raise ServerError(f"Bug fixing failed: {str(e)}")


@router.post(
    "/agent/chat",
    response_model=APIResponse,
    summary="Chat",
    tags=["Actions"],
)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user_flexible),
    agent: JmAgent = Depends(get_agent),
) -> APIResponse:
    """
    Interactive chat with the coding assistant.

    Request:
        - message: Chat message (required)
        - conversation_id: Conversation ID (optional, generates new if not provided)

    Response:
        - response: Chat response
        - conversation_id: Conversation ID (UUID)
        - tokens_used: Token usage breakdown
        - execution_time: Execution time in seconds
        - success: Whether the action succeeded
    """
    start_time = time.time()

    try:
        # Generate or use existing conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())

        logger.info(
            "Chat action started",
            extra={
                "user_id": current_user.get("user_id"),
                "conversation_id": conversation_id,
            },
        )

        # Initialize conversation if new
        if conversation_id not in conversation_store:
            conversation_store[conversation_id] = []

        # Add user message to history
        conversation_store[conversation_id].append({
            "role": "user",
            "content": request.message,
        })

        # Update agent conversation history
        agent.conversation_history = conversation_store[conversation_id].copy()

        # Call agent
        response = await agent._call_bedrock("chat", request.message, use_history=True)

        # Add assistant response to history
        conversation_store[conversation_id].append({
            "role": "assistant",
            "content": response.content,
        })

        execution_time = time.time() - start_time

        result = ChatResponse(
            response=response.content,
            conversation_id=conversation_id,
            tokens_used=TokenUsage(
                input=response.usage.get("input_tokens", 0),
                output=response.usage.get("output_tokens", 0),
            ),
            execution_time=execution_time,
            success=True,
        )

        logger.info(
            "Chat action completed",
            extra={
                "user_id": current_user.get("user_id"),
                "conversation_id": conversation_id,
                "execution_time": execution_time,
            },
        )

        return APIResponse(success=True, data=result)

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(
            "Chat action failed",
            extra={
                "user_id": current_user.get("user_id"),
                "error": str(e),
            },
        )
        raise ServerError(f"Chat failed: {str(e)}")


@router.post(
    "/agent/chat-stream",
    summary="Chat with Streaming",
    tags=["Actions"],
)
async def chat_stream(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user_flexible),
    agent: JmAgent = Depends(get_agent),
) -> StreamingResponse:
    """
    Interactive chat with streaming response (Server-Sent Events).

    Returns a stream of SSE events with progress and response tokens.

    Event types:
        - progress: Status update
        - token: Response token (streamed)
        - conversation_id: Final conversation ID
        - complete: Final response
    """
    async def generate() -> AsyncGenerator[str, None]:
        start_time = time.time()

        try:
            # Generate or use existing conversation ID
            conversation_id = request.conversation_id or str(uuid.uuid4())

            yield f'data: {json.dumps({"type": "progress", "message": "Initializing conversation..."})}\n\n'

            # Initialize conversation if new
            if conversation_id not in conversation_store:
                conversation_store[conversation_id] = []
                yield f'data: {json.dumps({"type": "progress", "message": "New conversation created"})}\n\n'
            else:
                message_count = len(conversation_store[conversation_id])
                yield f'data: {json.dumps({"type": "progress", "message": f"Loaded {message_count} previous messages"})}\n\n'

            # Add user message to history
            conversation_store[conversation_id].append({
                "role": "user",
                "content": request.message,
            })
            yield f'data: {json.dumps({"type": "progress", "message": "User message added to history"})}\n\n'

            # Update agent conversation history
            agent.conversation_history = conversation_store[conversation_id].copy()
            yield f'data: {json.dumps({"type": "progress", "message": "Calling Claude model..."})}\n\n'

            # Call agent
            response = await agent._call_bedrock("chat", request.message, use_history=True)

            output_tokens = response.usage.get("output_tokens", 0)
            yield f'data: {json.dumps({"type": "progress", "message": f"Received response ({output_tokens} tokens)"})} \n\n'

            # Add assistant response to history
            conversation_store[conversation_id].append({
                "role": "assistant",
                "content": response.content,
            })

            # Stream the response content
            yield f'data: {json.dumps({"type": "token", "content": response.content})}\n\n'

            # Send conversation ID
            yield f'data: {json.dumps({"type": "conversation_id", "conversation_id": conversation_id})}\n\n'

            execution_time = time.time() - start_time
            input_tokens = response.usage.get("input_tokens", 0)
            output_tokens = response.usage.get("output_tokens", 0)
            total_tokens = input_tokens + output_tokens

            # Send completion progress
            yield f'data: {json.dumps({"type": "progress", "message": f"Processing complete in {execution_time:.2f}s"})}\n\n'

            # Send complete response with metadata
            complete_data = {
                "type": "complete",
                "status": "success",
                "response": response.content,
                "execution_time": execution_time,
                "tokens_used": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": total_tokens
                },
                "conversation_id": conversation_id,
                "timestamp": time.time()
            }
            yield f'data: {json.dumps(complete_data)}\n\n'

            logger.info(
                "Chat stream completed successfully",
                extra={
                    "user_id": current_user.get("user_id"),
                    "conversation_id": conversation_id,
                    "execution_time": execution_time,
                    "tokens": {
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": total_tokens
                    },
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "Chat stream failed",
                extra={
                    "user_id": current_user.get("user_id"),
                    "error": str(e),
                    "execution_time": execution_time,
                },
            )
            yield f'data: {json.dumps({"type": "error", "message": str(e)})}\n\n'

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
