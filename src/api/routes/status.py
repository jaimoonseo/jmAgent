"""Status and job management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List

from src.api.models import APIResponse
from src.api.security.auth import get_current_user
from src.logging.logger import StructuredLogger

router = APIRouter(tags=["status"])
logger = StructuredLogger(__name__)

# Track background jobs in-memory
_jobs: Dict[str, Dict[str, Any]] = {}


@router.get(
    "/status/jobs",
    response_model=APIResponse,
    summary="List Background Jobs",
    tags=["Status"],
)
async def list_background_jobs(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    List all background jobs.

    Returns a list of currently running and completed background jobs.
    """
    try:
        # Convert jobs dict to list format
        jobs_list = []
        for job_id, job_info in _jobs.items():
            jobs_list.append({
                "id": job_id,
                "status": job_info.get("status", "unknown"),
                "action": job_info.get("action", "unknown"),
                "created_at": job_info.get("created_at"),
                "completed_at": job_info.get("completed_at"),
                "progress": job_info.get("progress", 0),
            })

        response_data = {
            "jobs": jobs_list,
            "total": len(jobs_list),
        }

        logger.info(
            "Background jobs listed",
            extra={
                "user_id": current_user.get("user_id"),
                "job_count": len(jobs_list),
            },
        )

        return APIResponse(success=True, data=response_data)
    except Exception as e:
        logger.error(
            "Error listing background jobs",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to list background jobs")
