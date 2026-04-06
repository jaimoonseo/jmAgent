"""Request models for action endpoints."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class ModelChoice(str, Enum):
    """Available Claude models."""

    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"


class TestFramework(str, Enum):
    """Supported test frameworks."""

    PYTEST = "pytest"
    VITEST = "vitest"
    JEST = "jest"


class ExplainLanguage(str, Enum):
    """Supported explanation languages."""

    ENGLISH = "english"
    KOREAN = "korean"


class GenerateRequest(BaseModel):
    """Request model for /api/v1/actions/generate endpoint."""

    prompt: str = Field(..., min_length=1, description="Code generation prompt")
    model: ModelChoice = Field(default=ModelChoice.HAIKU, description="Claude model to use")
    max_tokens: int = Field(default=4096, ge=256, le=4096, description="Maximum output tokens")
    temperature: float = Field(default=0.2, ge=0.0, le=1.0, description="Sampling temperature")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Create a FastAPI GET endpoint that returns user data",
                "model": "haiku",
                "max_tokens": 2048,
                "temperature": 0.2,
            }
        }


class RefactorRequest(BaseModel):
    """Request model for /api/v1/actions/refactor endpoint."""

    file_path: str = Field(..., min_length=1, description="Path to file to refactor (relative to project root)")
    requirements: str = Field(..., min_length=1, description="Refactoring requirements (e.g., 'add type hints')")
    model: ModelChoice = Field(default=ModelChoice.HAIKU, description="Claude model to use")

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Validate file path doesn't contain dangerous patterns."""
        if ".." in v or v.startswith("/"):
            raise ValueError("File path must be relative and cannot contain '..'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "src/utils.py",
                "requirements": "Add comprehensive type hints to all functions",
                "model": "haiku",
            }
        }


class TestRequest(BaseModel):
    """Request model for /api/v1/actions/test endpoint."""

    file_path: str = Field(..., min_length=1, description="Path to file to test (relative to project root)")
    framework: TestFramework = Field(..., description="Test framework to use")
    model: ModelChoice = Field(default=ModelChoice.HAIKU, description="Claude model to use")

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Validate file path doesn't contain dangerous patterns."""
        if ".." in v or v.startswith("/"):
            raise ValueError("File path must be relative and cannot contain '..'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "src/services/auth.py",
                "framework": "pytest",
                "model": "haiku",
            }
        }


class ExplainRequest(BaseModel):
    """Request model for /api/v1/actions/explain endpoint."""

    file_path: str = Field(..., min_length=1, description="Path to file to explain (relative to project root)")
    focus_area: Optional[str] = Field(None, description="Specific area to focus on (e.g., 'authentication', 'database')")
    language: ExplainLanguage = Field(default=ExplainLanguage.ENGLISH, description="Language for explanation")

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Validate file path doesn't contain dangerous patterns."""
        if ".." in v or v.startswith("/"):
            raise ValueError("File path must be relative and cannot contain '..'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "src/models/user.py",
                "focus_area": "database relationships",
                "language": "korean",
            }
        }


class FixRequest(BaseModel):
    """Request model for /api/v1/actions/fix endpoint."""

    file_path: str = Field(..., min_length=1, description="Path to file to fix (relative to project root)")
    error_message: str = Field(..., min_length=1, description="Error message or description (e.g., 'TypeError: NoneType')")
    model: ModelChoice = Field(default=ModelChoice.HAIKU, description="Claude model to use")

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Validate file path doesn't contain dangerous patterns."""
        if ".." in v or v.startswith("/"):
            raise ValueError("File path must be relative and cannot contain '..'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "src/app.py",
                "error_message": "TypeError: 'NoneType' object is not subscriptable at line 42",
                "model": "haiku",
            }
        }


class ChatRequest(BaseModel):
    """Request model for /api/v1/actions/chat endpoint."""

    message: str = Field(..., min_length=1, description="Chat message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID (UUID format, generates new if not provided)")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "How do I implement error handling in FastAPI?",
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }
