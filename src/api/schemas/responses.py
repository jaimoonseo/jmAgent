"""Response models for action endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime, timezone


class TokenUsage(BaseModel):
    """Token usage metrics."""

    input: int = Field(..., ge=0, description="Input tokens used")
    output: int = Field(..., ge=0, description="Output tokens used")


class GenerateResponse(BaseModel):
    """Response model for /api/v1/actions/generate endpoint."""

    generated_code: str = Field(..., description="Generated code")
    model_used: str = Field(..., description="Model used for generation")
    tokens_used: TokenUsage = Field(..., description="Token usage breakdown")
    execution_time: float = Field(..., ge=0, description="Execution time in seconds")
    success: bool = Field(..., description="Whether the action succeeded")

    class Config:
        json_schema_extra = {
            "example": {
                "generated_code": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/users/{user_id}')\nasync def get_user(user_id: int):\n    return {'user_id': user_id}",
                "model_used": "haiku",
                "tokens_used": {"input": 45, "output": 120},
                "execution_time": 1.23,
                "success": True,
            }
        }


class RefactorResponse(BaseModel):
    """Response model for /api/v1/actions/refactor endpoint."""

    refactored_code: str = Field(..., description="Refactored code")
    changes_summary: str = Field(..., description="Summary of changes made")
    tokens_used: TokenUsage = Field(..., description="Token usage breakdown")
    execution_time: float = Field(..., ge=0, description="Execution time in seconds")
    success: bool = Field(..., description="Whether the action succeeded")

    class Config:
        json_schema_extra = {
            "example": {
                "refactored_code": "def process_data(items: list[str]) -> dict[str, int]:\n    ...",
                "changes_summary": "Added type hints to function signature and improved variable naming",
                "tokens_used": {"input": 50, "output": 100},
                "execution_time": 0.98,
                "success": True,
            }
        }


class TestResponse(BaseModel):
    """Response model for /api/v1/actions/test endpoint."""

    test_code: str = Field(..., description="Generated test code")
    coverage_estimate: str = Field(..., description="Estimated code coverage (e.g., '80%')")
    tokens_used: TokenUsage = Field(..., description="Token usage breakdown")
    execution_time: float = Field(..., ge=0, description="Execution time in seconds")
    success: bool = Field(..., description="Whether the action succeeded")

    class Config:
        json_schema_extra = {
            "example": {
                "test_code": "import pytest\n\ndef test_process_data():\n    ...",
                "coverage_estimate": "85%",
                "tokens_used": {"input": 60, "output": 150},
                "execution_time": 1.45,
                "success": True,
            }
        }


class ExplainResponse(BaseModel):
    """Response model for /api/v1/actions/explain endpoint."""

    explanation: str = Field(..., description="Code explanation")
    key_concepts: List[str] = Field(..., description="Key concepts mentioned in the explanation")
    tokens_used: TokenUsage = Field(..., description="Token usage breakdown")
    execution_time: float = Field(..., ge=0, description="Execution time in seconds")
    success: bool = Field(..., description="Whether the action succeeded")

    class Config:
        json_schema_extra = {
            "example": {
                "explanation": "This code implements a user authentication system using JWT tokens...",
                "key_concepts": ["JWT", "Authentication", "Token validation", "User sessions"],
                "tokens_used": {"input": 55, "output": 200},
                "execution_time": 0.87,
                "success": True,
            }
        }


class FixResponse(BaseModel):
    """Response model for /api/v1/actions/fix endpoint."""

    fixed_code: str = Field(..., description="Fixed code")
    fix_summary: str = Field(..., description="Summary of the bug and fix")
    tokens_used: TokenUsage = Field(..., description="Token usage breakdown")
    execution_time: float = Field(..., ge=0, description="Execution time in seconds")
    success: bool = Field(..., description="Whether the action succeeded")

    class Config:
        json_schema_extra = {
            "example": {
                "fixed_code": "def get_user(user_id: int) -> Optional[dict]:\n    if user_id is None:\n        return None\n    ...",
                "fix_summary": "Fixed NoneType error by adding None check at line 42",
                "tokens_used": {"input": 65, "output": 110},
                "execution_time": 1.05,
                "success": True,
            }
        }


class ChatResponse(BaseModel):
    """Response model for /api/v1/actions/chat endpoint."""

    response: str = Field(..., description="Chat response from the assistant")
    conversation_id: str = Field(..., description="Conversation ID (UUID)")
    tokens_used: TokenUsage = Field(..., description="Token usage breakdown")
    execution_time: float = Field(..., ge=0, description="Execution time in seconds")
    success: bool = Field(..., description="Whether the action succeeded")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "In FastAPI, you can use try/except blocks with HTTPException...",
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "tokens_used": {"input": 40, "output": 180},
                "execution_time": 0.76,
                "success": True,
            }
        }
