"""FastAPI application factory and setup."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
import logging

from src.logging.logger import StructuredLogger
from src.api.config import settings
from src.api.exceptions import APIException
from src.api.middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware, SecurityHeadersMiddleware, RateLimitMiddleware
from src.api.routes import health

# Configure logger
logger = StructuredLogger(__name__)


def create_app() -> FastAPI:
    """
    Factory function to create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    # Create FastAPI app
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description=settings.api_description,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    # Add custom middleware (order matters - added in reverse)
    app.add_middleware(SecurityHeadersMiddleware)
    if settings.rate_limit_enabled:
        app.add_middleware(RateLimitMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # Register exception handlers
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        """Handle custom API exceptions."""
        logger.error(
            "API Exception",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
                "error_code": exc.error_code,
                "detail": exc.detail,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail,
                "error_code": exc.error_code,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        errors = exc.errors()
        error_details = [
            {"field": str(e["loc"]), "message": e["msg"]} for e in errors
        ]

        logger.warning(
            "Validation Error",
            extra={
                "path": request.url.path,
                "errors": error_details,
            },
        )

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": "Validation failed",
                "error_code": "VALIDATION_ERROR",
                "details": error_details,
            },
        )

    # Register routes
    app.include_router(health.router, prefix="/api/v1", tags=["health"])

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Handle application startup."""
        logger.info(
            "jmAgent API Starting",
            extra={
                "version": settings.api_version,
                "host": settings.host,
                "port": settings.port,
                "debug": settings.debug,
            },
        )

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Handle application shutdown."""
        logger.info("jmAgent API Shutting Down")

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
