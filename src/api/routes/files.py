"""File management endpoints for reading and writing project files."""

import os
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel, Field

from src.logging.logger import StructuredLogger
from src.api.models import APIResponse
from src.api.security.auth import verify_token, JwtSettings, APIKeyValidator

logger = StructuredLogger(__name__)
router = APIRouter()

# Store project root in memory (in production, use database or config)
project_root: Optional[Path] = None


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


class FileInfo(BaseModel):
    """Information about a file or directory."""
    name: str = Field(..., description="File or directory name")
    path: str = Field(..., description="Relative path from project root")
    type: str = Field(..., description="'file' or 'directory'")
    size: Optional[int] = Field(None, description="File size in bytes")


class FileListResponse(BaseModel):
    """Response for file listing."""
    path: str = Field(..., description="Current directory path")
    files: List[FileInfo] = Field(..., description="Files and directories")


class FileReadRequest(BaseModel):
    """Request to read a file."""
    path: str = Field(..., description="Relative file path from project root")


class FileReadResponse(BaseModel):
    """Response when reading a file."""
    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content")
    size: int = Field(..., description="File size in bytes")


class FileWriteRequest(BaseModel):
    """Request to write a file."""
    path: str = Field(..., description="Relative file path from project root")
    content: str = Field(..., description="File content to write")
    create_dirs: bool = Field(default=True, description="Create parent directories if needed")


class FileWriteResponse(BaseModel):
    """Response when writing a file."""
    path: str = Field(..., description="File path written")
    success: bool = Field(..., description="Whether write was successful")
    size: int = Field(..., description="File size after write")


class SetProjectRootRequest(BaseModel):
    """Request to set project root."""
    path: str = Field(..., description="Absolute path to project root")


def get_project_root() -> Path:
    """Get current project root."""
    global project_root
    if project_root is None:
        # Default to current working directory
        project_root = Path.cwd()
    return project_root


def validate_path(relative_path: str, project_root_path: Path) -> Path:
    """
    Validate file path to prevent directory traversal attacks.

    SECURITY: Prevents path traversal attacks by:
    - Checking for ".." sequences
    - Checking for absolute paths
    - Resolving symlinks and verifying the real path is within project root
    """
    if ".." in relative_path or relative_path.startswith("/"):
        raise HTTPException(status_code=400, detail=f"Invalid file path: {relative_path}")

    file_path = project_root_path / relative_path

    try:
        # Resolve to absolute path and follow all symlinks
        resolved_path = file_path.resolve()
        project_root_resolved = project_root_path.resolve()

        # Verify the resolved path is within project root
        try:
            resolved_path.relative_to(project_root_resolved)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"File path outside project root: {relative_path}"
            )

        return resolved_path
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=400, detail=f"Invalid file path: {str(e)}")


@router.post(
    "/files/set-project-root",
    response_model=APIResponse,
    summary="Set Project Root",
    tags=["Files"],
)
async def set_project_root(
    request: SetProjectRootRequest,
    current_user: dict = Depends(get_current_user_flexible),
) -> APIResponse:
    """
    Set the project root directory for file operations.

    Args:
        request: SetProjectRootRequest with path to project root

    Returns:
        APIResponse with success status
    """
    global project_root

    try:
        # Trim whitespace from path
        path_str = request.path.strip()
        path = Path(path_str)
        if not path.exists():
            raise HTTPException(status_code=400, detail=f"Path does not exist: {path_str}")
        if not path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {path_str}")

        project_root = path
        logger.info(
            "Project root set",
            extra={
                "user_id": current_user.get("user_id"),
                "project_root": str(path),
            },
        )

        return APIResponse(
            success=True,
            data={"project_root": str(path)},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to set project root",
            extra={
                "user_id": current_user.get("user_id"),
                "error": str(e),
            },
        )
        raise HTTPException(status_code=400, detail=f"Failed to set project root: {str(e)}")


@router.get(
    "/files/list",
    response_model=APIResponse,
    summary="List Files in Directory",
    tags=["Files"],
)
async def list_files(
    path: str = "",
    current_user: dict = Depends(get_current_user_flexible),
) -> APIResponse:
    """
    List files and directories in a given path.

    Args:
        path: Relative path from project root (empty string for root)

    Returns:
        APIResponse with list of files and directories
    """
    try:
        root = get_project_root()
        dir_path = validate_path(path or ".", root)

        if not dir_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")

        files: List[FileInfo] = []

        # List directory contents
        for item in sorted(dir_path.iterdir()):
            try:
                relative_path = str(item.relative_to(root))

                if item.is_dir():
                    files.append(FileInfo(
                        name=item.name,
                        path=relative_path,
                        type="directory",
                    ))
                else:
                    files.append(FileInfo(
                        name=item.name,
                        path=relative_path,
                        type="file",
                        size=item.stat().st_size,
                    ))
            except Exception as e:
                logger.warning(f"Failed to list item {item}: {e}")
                continue

        logger.info(
            "Files listed",
            extra={
                "user_id": current_user.get("user_id"),
                "path": path,
                "count": len(files),
            },
        )

        return APIResponse(
            success=True,
            data=FileListResponse(path=path or "/", files=files),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to list files",
            extra={
                "user_id": current_user.get("user_id"),
                "path": path,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.post(
    "/files/read",
    response_model=APIResponse,
    summary="Read File",
    tags=["Files"],
)
async def read_file(
    request: FileReadRequest,
    current_user: dict = Depends(get_current_user_flexible),
) -> APIResponse:
    """
    Read file content.

    Args:
        request: FileReadRequest with file path

    Returns:
        APIResponse with file content
    """
    try:
        root = get_project_root()
        file_path = validate_path(request.path, root)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.path}")
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail=f"Path is not a file: {request.path}")

        # Check file size (limit to 10MB)
        size = file_path.stat().st_size
        if size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        content = file_path.read_text(encoding="utf-8")

        logger.info(
            "File read",
            extra={
                "user_id": current_user.get("user_id"),
                "path": request.path,
                "size": size,
            },
        )

        return APIResponse(
            success=True,
            data=FileReadResponse(
                path=request.path,
                content=content,
                size=size,
            ),
        )
    except HTTPException:
        raise
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not valid UTF-8 text")
    except Exception as e:
        logger.error(
            "Failed to read file",
            extra={
                "user_id": current_user.get("user_id"),
                "path": request.path,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.post(
    "/files/write",
    response_model=APIResponse,
    summary="Write File",
    tags=["Files"],
)
async def write_file(
    request: FileWriteRequest,
    current_user: dict = Depends(get_current_user_flexible),
) -> APIResponse:
    """
    Write content to a file (creates or overwrites).

    Args:
        request: FileWriteRequest with file path and content

    Returns:
        APIResponse with success status
    """
    try:
        root = get_project_root()
        file_path = validate_path(request.path, root)

        # Create parent directories if needed
        if request.create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        elif not file_path.parent.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Parent directory does not exist: {request.path}"
            )

        # Write file
        file_path.write_text(request.content, encoding="utf-8")
        size = file_path.stat().st_size

        logger.info(
            "File written",
            extra={
                "user_id": current_user.get("user_id"),
                "path": request.path,
                "size": size,
                "created": not file_path.exists(),
            },
        )

        return APIResponse(
            success=True,
            data=FileWriteResponse(
                path=request.path,
                success=True,
                size=size,
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to write file",
            extra={
                "user_id": current_user.get("user_id"),
                "path": request.path,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")


@router.get(
    "/files/browse",
    response_model=APIResponse,
    summary="Browse Directory Tree",
    tags=["Files"],
)
async def browse_directory(
    path: str = "~",
    current_user: dict = Depends(get_current_user_flexible),
) -> APIResponse:
    """
    Browse directory tree for project selection.
    
    Args:
        path: Directory path to list (~ for home)
    
    Returns:
        APIResponse with directory structure
    """
    try:
        # Expand home directory
        if path == "~" or path.startswith("~/"):
            expanded_path = os.path.expanduser(path)
        else:
            expanded_path = path
        
        dir_path = Path(expanded_path)
        
        if not dir_path.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")
        
        if not dir_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")
        
        directories: List[FileInfo] = []
        
        # List only directories
        for item in sorted(dir_path.iterdir()):
            try:
                if item.is_dir() and not item.name.startswith("."):
                    directories.append(FileInfo(
                        name=item.name,
                        path=str(item),
                        type="directory",
                    ))
            except (PermissionError, OSError):
                pass
        
        return APIResponse(
            success=True,
            data={
                "path": str(dir_path),
                "files": [d.dict() for d in directories],
            },
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to browse directory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to browse directory: {str(e)}")
