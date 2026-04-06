"""API middleware for request/response handling."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from src.logging.logger import StructuredLogger
from src.api.security.rate_limiter import RateLimiter
import time
from typing import Callable

logger = StructuredLogger(__name__)

# Global rate limiter instance
_rate_limiter = RateLimiter()


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


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Add security headers to response."""
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Add HSTS header in production (can be configured)
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting per IP address."""

    def __init__(self, app, limit_per_minute: int = 100):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            limit_per_minute: Requests allowed per minute per IP
        """
        super().__init__(app)
        self.limit_per_minute = limit_per_minute

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Check rate limit and process request."""
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        identifier = f"ip:{client_ip}"

        # Check rate limit (100 requests per minute = ~1.67 per second)
        if not _rate_limiter.check_rate_limit(
            identifier,
            limit=self.limit_per_minute,
            window=60,
        ):
            logger.warning(
                "Rate limit exceeded",
                extra={"client_ip": client_ip},
            )

            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Rate limit exceeded",
                    "error_code": "RATE_LIMIT",
                },
            )

        response = await call_next(request)
        return response
