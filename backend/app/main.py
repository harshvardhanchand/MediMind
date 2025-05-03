from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.endpoints.health import router as health_router
from app.api.endpoints.me import router as me_router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.rate_limit import limiter, get_client_ip

# Initialize and configure FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Patient Medical Data Hub API",
    version="0.2.0",
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

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(me_router, prefix="/api/v1")

# Add root endpoint to redirect to API docs
@app.get("/", include_in_schema=False)
async def root():
    """Redirect from root to API documentation"""
    return RedirectResponse(url="/api/docs")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # In a production environment, we should log the error details
    # but return a generic error message to the client
    import logging
    logger = logging.getLogger(__name__)
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "structured_data": {
                "path": request.url.path,
                "method": request.method,
                "client_ip": get_client_ip(request),
            }
        },
    )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"},
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 