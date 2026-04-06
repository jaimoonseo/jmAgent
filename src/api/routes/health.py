"""Health check endpoints."""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import time
import psutil
import os

from src.api.models import HealthCheck, HealthStatus, HealthComponent, StatusResponse, APIResponse
from src.logging.logger import StructuredLogger

router = APIRouter()
logger = StructuredLogger(__name__)

# Track startup time for uptime calculation
START_TIME = time.time()


def get_uptime() -> float:
    """Get server uptime in seconds."""
    return time.time() - START_TIME


def check_bedrock_available() -> bool:
    """Check if Bedrock is available (stub for now)."""
    # In production, this would actually test the Bedrock connection
    return True


def check_cache_available() -> bool:
    """Check if cache is available (stub for now)."""
    # In production, this would check Redis or in-memory cache
    return True


def check_database_available() -> bool:
    """Check if database is available (stub for now)."""
    # In production, this would check the database connection
    return True


@router.get(
    "/health",
    response_model=APIResponse,
    summary="Server Health Check",
    tags=["Health"],
)
async def health_check():
    """
    Check overall server health status.

    Returns health status of the server and its components.
    """
    uptime = get_uptime()

    # Check individual components
    bedrock_available = check_bedrock_available()
    cache_available = check_cache_available()
    database_available = check_database_available()

    # Determine overall status
    all_healthy = bedrock_available and cache_available and database_available
    overall_status = HealthStatus.HEALTHY if all_healthy else HealthStatus.DEGRADED

    # Build component list
    components = [
        HealthComponent(
            name="bedrock",
            status=HealthStatus.HEALTHY if bedrock_available else HealthStatus.UNHEALTHY,
            details={"available": bedrock_available},
        ),
        HealthComponent(
            name="cache",
            status=HealthStatus.HEALTHY if cache_available else HealthStatus.UNHEALTHY,
            details={"available": cache_available},
        ),
        HealthComponent(
            name="database",
            status=HealthStatus.HEALTHY if database_available else HealthStatus.UNHEALTHY,
            details={"available": database_available},
        ),
    ]

    health_data = HealthCheck(
        status=overall_status,
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=uptime,
        components=components,
    )

    logger.info(
        "Health check passed",
        extra={
            "uptime_seconds": uptime,
            "status": overall_status,
            "bedrock_available": bedrock_available,
            "cache_available": cache_available,
            "database_available": database_available,
        },
    )

    return APIResponse(success=True, data=health_data)


@router.get(
    "/status",
    response_model=APIResponse,
    summary="Server Status",
    tags=["Health"],
)
async def status():
    """
    Check server status.

    Returns basic server information and operational status.
    """
    status_data = StatusResponse(
        version="1.0.0",
        api_version="v1",
        status="operational",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    logger.info("Status check completed")

    return APIResponse(success=True, data=status_data)


@router.get(
    "/ready",
    response_model=APIResponse,
    summary="Readiness Check",
    tags=["Health"],
)
async def readiness_check():
    """
    Check if the server is ready to handle requests.

    Performs more detailed checks than /health.
    """
    uptime = get_uptime()

    # Check all critical components
    bedrock_available = check_bedrock_available()
    cache_available = check_cache_available()
    database_available = check_database_available()

    # All components must be ready
    if not (bedrock_available and cache_available and database_available):
        logger.warning(
            "Server not ready",
            extra={
                "bedrock": bedrock_available,
                "cache": cache_available,
                "database": database_available,
            },
        )
        raise HTTPException(status_code=503, detail="Service not ready")

    logger.info("Readiness check passed")

    return APIResponse(
        success=True,
        data={
            "ready": True,
            "uptime_seconds": uptime,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
