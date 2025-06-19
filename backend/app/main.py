from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import  _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Import custom exceptions and middleware
from app.core.exceptions import MedicalAppException, AuthenticationError, ValidationError
from app.middleware.performance import PerformanceMiddleware, metrics_endpoint

# Only import health endpoint directly, others are in api_router
from app.api.endpoints import health
# Import the new main api_router
from app.api.router import api_router

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.rate_limit import limiter, get_client_ip
import logging
import traceback

# Initialize and configure FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Patient Medical Data Hub API",
    version="0.3.0",  # Bumped version for performance improvements
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/api/openapi.json" if settings.ENVIRONMENT != "production" else None,
)

# Set up logging
setup_logging()

# Set up rate limiter with our custom client IP function
limiter.key_func = get_client_ip

# Add rate limiter to the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add performance monitoring middleware (first for accurate timing)
app.add_middleware(
    PerformanceMiddleware, 
    enable_detailed_logging=settings.ENVIRONMENT != "production"
)

# Add performance middleware (order matters!)
# 1. GZip compression for responses > 500 bytes (optimized threshold)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 2. Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# 3. CORS middleware configuration with performance optimizations
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Performance optimizations
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Global exception handlers for standardized error responses
@app.exception_handler(MedicalAppException)
async def medical_app_exception_handler(request: Request, exc: MedicalAppException):
    """Handle custom medical app exceptions with structured responses."""
    
    logger = logging.getLogger(__name__)
    
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.warning(
        f"Medical app exception: {exc.error_code.value}",
        extra={
            "structured_data": {
                "correlation_id": correlation_id,
                "error_code": exc.error_code.value,
                "message": exc.message,
                "details": exc.details,
                "path": request.url.path,
                "method": request.method,
                "client_ip": get_client_ip(request),
            }
        },
    )
    
    response_data = exc.to_dict()
    response_data["correlation_id"] = correlation_id
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers={"X-Correlation-ID": correlation_id}
    )

@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors with proper logging."""
    
    logger = logging.getLogger(__name__)
    
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.warning(
        f"Authentication error: {exc.error_code.value}",
        extra={
            "structured_data": {
                "correlation_id": correlation_id,
                "error_code": exc.error_code.value,
                "path": request.url.path,
                "method": request.method,
                "client_ip": get_client_ip(request),
            }
        },
    )
    
    response_data = exc.to_dict()
    response_data["correlation_id"] = correlation_id
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers={"X-Correlation-ID": correlation_id}
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors with detailed field information."""
    
    logger = logging.getLogger(__name__)
    
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.info(
        f"Validation error: {exc.message}",
        extra={
            "structured_data": {
                "correlation_id": correlation_id,
                "error_code": exc.error_code.value,
                "details": exc.details,
                "path": request.url.path,
                "method": request.method,
            }
        },
    )
    
    response_data = exc.to_dict()
    response_data["correlation_id"] = correlation_id
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers={"X-Correlation-ID": correlation_id}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions with correlation ID."""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "correlation_id": correlation_id
        },
        headers={"X-Correlation-ID": correlation_id}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with enhanced logging and error tracking."""
   
    
    logger = logging.getLogger(__name__)
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    # Log the error with full context
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "structured_data": {
                "correlation_id": correlation_id,
                "path": request.url.path,
                "method": request.method,
                "client_ip": get_client_ip(request),
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            }
        },
    )
    
    # In production, don't expose internal error details
    if settings.ENVIRONMENT == "production":
        message = "An unexpected error occurred"
        details = {}
    else:
        message = str(exc)
        details = {"exception_type": type(exc).__name__}
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": message,
            "details": details,
            "correlation_id": correlation_id
        },
        headers={"X-Correlation-ID": correlation_id}
    )

# Include the main API router
app.include_router(api_router, prefix="/api")

# Include the health check router separately, directly under /api for consistency
app.include_router(health.router, prefix="/api/health", tags=["health"])

# Add metrics endpoint for monitoring
@app.get("/metrics", include_in_schema=False)
async def get_metrics(request: Request):
    """Prometheus metrics endpoint."""
    return await metrics_endpoint(request)

# Add performance stats endpoint
@app.get("/api/admin/performance", include_in_schema=False)
async def get_performance_stats(request: Request):
    """Get current performance statistics (admin only)."""
    from app.middleware.performance import get_performance_metrics
    from app.core.auth import get_token_cache_stats
    
    return JSONResponse({
        "performance": get_performance_metrics(),
        "token_cache": get_token_cache_stats(),
        "correlation_id": getattr(request.state, 'correlation_id', 'unknown')
    })

# Add root endpoint to redirect to API docs
@app.get("/", include_in_schema=False)
async def root():
    """Redirect from root to API documentation"""
    return RedirectResponse(url="/api/docs")

# Health check endpoint with enhanced metrics
@app.get("/health", include_in_schema=False)
async def health_check():
    """Enhanced health check with system metrics."""
    from app.middleware.performance import get_performance_metrics
    
    try:
        # Test database connectivity
        from app.db.session import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return JSONResponse({
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "performance": get_performance_metrics(),
        "version": "0.3.0"
    })

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 