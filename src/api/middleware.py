"""API middleware for request/response handling."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from src.logging.logger import StructuredLogger
import time
from typing import Callable

logger = StructuredLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Log request and response details."""
        start_time = time.time()
        request_id = request.headers.get("x-request-id", "unknown")

        # Log incoming request
        logger.info(
            "API Request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query) if request.url.query else None,
            },
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log outgoing response
            logger.info(
                "API Response",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": round(process_time * 1000, 2),
                    "path": request.url.path,
                },
            )

            # Add custom headers
            response.headers["x-request-id"] = request_id
            response.headers["x-process-time"] = str(process_time)

            return response

        except Exception as exc:
            process_time = time.time() - start_time

            logger.error(
                "API Request Failed",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "duration_ms": round(process_time * 1000, 2),
                    "error": str(exc),
                },
            )

            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle and standardize error responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Handle exceptions and return standardized error responses."""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(
                "Unhandled Exception",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Internal server error",
                    "error_code": "SERVER_ERROR",
                },
            )
