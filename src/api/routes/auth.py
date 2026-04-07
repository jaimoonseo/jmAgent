"""Authentication endpoints for jmAgent API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from src.logging.logger import StructuredLogger
from src.api.models import APIResponse
from src.api.security.auth import create_token, JwtSettings

router = APIRouter()
logger = StructuredLogger(__name__)

# In-memory user store for development/testing
# In production, this would be a database
VALID_USERS = {
    "admin": {
        "password": "admin",
        "user_id": "admin",
        "username": "admin",
        "role": "admin",
        "agent_id": "admin-agent",
    }
}


class LoginRequest(BaseModel):
    """Login request model."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "admin",
                "password": "admin",
            }
        }
    }

    username: str = Field(..., description="Username for login")
    password: str = Field(..., description="Password for login")


class UserInfo(BaseModel):
    """User information in login response."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "admin",
                "username": "admin",
                "role": "admin",
            }
        }
    }

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    role: str = Field(..., description="User role")


class LoginResponse(BaseModel):
    """Login response model."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": "admin",
                    "username": "admin",
                    "role": "admin",
                },
                "expires_in": 1800,
            }
        }
    }

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserInfo = Field(..., description="User information")
    expires_in: int = Field(default=1800, description="Token expiration in seconds")


@router.post(
    "/auth/login",
    response_model=APIResponse,
    summary="User Login",
    tags=["Auth"],
    responses={
        200: {"description": "Successful login with JWT token"},
        401: {"description": "Invalid username or password"},
    },
)
async def login(request: LoginRequest) -> APIResponse:
    """
    Login endpoint that returns JWT token for authentication.

    Accepts username and password, validates them, and returns a JWT token
    for use in subsequent API requests.

    **For development/testing:**
    - Username: `admin`
    - Password: `admin`

    Returns:
        APIResponse with access_token, token_type, and user information
    """
    logger.info(
        "Login attempt",
        extra={"username": request.username},
    )

    # Validate credentials
    if request.username not in VALID_USERS:
        logger.warning(
            "Login failed: invalid username",
            extra={"username": request.username},
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    user = VALID_USERS[request.username]
    if user["password"] != request.password:
        logger.warning(
            "Login failed: invalid password",
            extra={"username": request.username},
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    # Create JWT token
    jwt_settings = JwtSettings()
    access_token = create_token(
        user_id=user["user_id"],
        agent_id=user["agent_id"],
        settings=jwt_settings,
    )

    # Build response
    user_info = UserInfo(
        id=user["user_id"],
        username=user["username"],
        role=user["role"],
    )

    login_response = LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_info,
        expires_in=jwt_settings.expiration_minutes * 60,
    )

    logger.info(
        "Login successful",
        extra={
            "username": request.username,
            "user_id": user["user_id"],
            "role": user["role"],
        },
    )

    return APIResponse(
        success=True,
        data=login_response.model_dump(),
    )
