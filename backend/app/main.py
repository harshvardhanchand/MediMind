from dotenv import load_dotenv


load_dotenv()

import uuid
import logging
import traceback
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
import uvicorn

from app.core.exceptions import (
    MedicalAppException,
    AuthenticationError,
    ValidationError,
)
from app.middleware.performance import PerformanceMiddleware, metrics_endpoint


from app.api.endpoints import health

from app.api.router import api_router

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.rate_limit import limiter, get_client_ip


class ErrorResponse(BaseModel):
    error: str
    message: str
    correlation_id: str
    details: Optional[Dict[str, Any]] = None


setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info("Starting up MediMind Backend...")

    try:
        logger.info("Environment check:")
        logger.info(
            f"  DATABASE_URL: {' Set' if settings.DATABASE_URL else ' Missing'}"
        )
        logger.info(
            f"  SUPABASE_URL: {' Set' if settings.SUPABASE_URL else ' Missing'}"
        )
        logger.info(f"  ENVIRONMENT: {settings.ENVIRONMENT}")

        logger.info("Testing database connection...")
        from app.db.session import SessionLocal
        from sqlalchemy import text

        db = SessionLocal()
        result = db.execute(text("SELECT 1"))
        logger.info(f" Database query result: {result.fetchone()}")
        db.close()
        logger.info(" Database connection verified")

        logger.info(" Testing ML libraries...")
        try:
            import torch
            import transformers

            logger.info(f"PyTorch {torch.__version__} loaded")
            logger.info(f"Transformers {transformers.__version__} loaded")
            logger.info(f"CUDA available: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                logger.info(f"GPU count: {torch.cuda.device_count()}")
        except Exception as ml_error:
            logger.warning(f"ML libraries issue: {ml_error}")

        logger.info("Application startup completed successfully")

    except Exception as e:
        logger.error(f" Startup failed: {str(e)}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down MediMind Backend...")

    try:

        logger.info(" Application shutdown completed successfully")

    except Exception as e:
        logger.error(f" Shutdown error: {str(e)}", exc_info=True)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Patient Medical Data Hub API",
    version="0.3.0",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/api/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)


@app.middleware("http")
async def add_correlation_id_middleware(request: Request, call_next):
    """Add correlation ID to every request for tracing."""

    correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id

    logger.info(
        f" Request started: {request.method} {request.url.path}",
        extra={
            "structured_data": {
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": get_client_ip(request),
                "user_agent": request.headers.get("User-Agent", "unknown"),
            }
        },
    )

    response = await call_next(request)

    # Ensure correlation_id is properly set
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    response.headers["X-Correlation-ID"] = correlation_id

    return response


limiter.key_func = get_client_ip


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.add_middleware(
    PerformanceMiddleware, enable_detailed_logging=settings.ENVIRONMENT != "production"
)


app.add_middleware(GZipMiddleware, minimum_size=1000)


app.add_middleware(SecurityHeadersMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)


def build_error_response(
    request: Request,
    error_code: str,
    message: str,
    status_code: int,
    log_level: str = "warning",
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Build standardized error response with logging."""

    correlation_id = request.state.correlation_id

    # Structure log data
    log_data = {
        "correlation_id": correlation_id,
        "error_code": error_code,
        "message": message,
        "path": request.url.path,
        "method": request.method,
        "client_ip": get_client_ip(request),
        "status_code": status_code,
    }

    if details:
        log_data["details"] = details

    log_message = f"{error_code}: {message}"
    if log_level == "error":
        logger.error(log_message, extra={"structured_data": log_data}, exc_info=True)
    elif log_level == "warning":
        logger.warning(log_message, extra={"structured_data": log_data})
    else:
        logger.info(log_message, extra={"structured_data": log_data})

    error_response = ErrorResponse(
        error=error_code,
        message=message,
        correlation_id=correlation_id,
        details=details,
    )

    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(),
        headers={"X-Correlation-ID": correlation_id},
    )


@app.exception_handler(MedicalAppException)
async def medical_app_exception_handler(request: Request, exc: MedicalAppException):
    """Handle custom medical app exceptions with structured responses."""
    return build_error_response(
        request=request,
        error_code=exc.error_code.value,
        message=exc.message,
        status_code=exc.status_code,
        log_level="warning",
        details=exc.details,
    )


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors with proper logging."""
    return build_error_response(
        request=request,
        error_code=exc.error_code.value,
        message=exc.message,
        status_code=exc.status_code,
        log_level="warning",
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors with detailed field information."""
    return build_error_response(
        request=request,
        error_code=exc.error_code.value,
        message=exc.message,
        status_code=exc.status_code,
        log_level="info",
        details=exc.details,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions with correlation ID."""
    return build_error_response(
        request=request,
        error_code="HTTP_ERROR",
        message=str(exc.detail),
        status_code=exc.status_code,
        log_level="warning",
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with enhanced logging and error tracking."""

    # In production, don't expose internal error details
    if settings.ENVIRONMENT == "production":
        message = "An unexpected error occurred"
        details = None
    else:
        message = str(exc)
        details = {
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
        }

    return build_error_response(
        request=request,
        error_code="INTERNAL_ERROR",
        message=message,
        status_code=500,
        log_level="error",
        details=details,
    )


app.include_router(api_router, prefix="/api")

app.include_router(health.router, prefix="/api/health", tags=["health"])


@app.get("/metrics", include_in_schema=False)
async def get_metrics(request: Request):
    """Prometheus metrics endpoint."""
    return await metrics_endpoint(request)


@app.get("/api/admin/performance", include_in_schema=False)
async def get_performance_stats(request: Request):
    """Get current performance statistics (admin only)."""
    from app.middleware.performance import get_performance_metrics
    from app.core.auth import get_token_cache_stats

    return JSONResponse(
        {
            "performance": get_performance_metrics(),
            "token_cache": get_token_cache_stats(),
            "correlation_id": getattr(request.state, "correlation_id", "unknown"),
        }
    )


@app.get("/api/admin/ocr-config", include_in_schema=False)
async def get_ocr_validation_config(request: Request):
    """Get current OCR validation configuration (admin only)."""
    from app.utils.ocr_validation import OCRValidationConfig

    config = OCRValidationConfig()
    summary = config.get_config_summary()

    return JSONResponse(
        {
            "active_thresholds": summary["active_thresholds"],
            "absolute_minimum": summary["absolute_minimum"],
            "has_overrides": summary["has_overrides"],
            "environment_overrides": (
                summary["environment_overrides"] if summary["has_overrides"] else {}
            ),
        }
    )


@app.get("/", include_in_schema=False)
async def root():
    """Redirect from root to API documentation"""
    return RedirectResponse(url="/api/docs")


@app.get("/health", include_in_schema=False)
async def health_check():
    """Enhanced health check with system metrics."""
    from app.middleware.performance import get_performance_metrics

    try:

        from app.db.session import SessionLocal
        from sqlalchemy import text

        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return JSONResponse(
        {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "database": db_status,
            "performance": get_performance_metrics(),
            "version": "0.3.0",
        }
    )


if __name__ == "__main__":

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
