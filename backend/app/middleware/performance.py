"""
Performance monitoring middleware with Prometheus metrics and structured logging.
"""
import time
import uuid
from typing import Dict, Any, Optional
from contextlib import contextmanager
import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'user_id']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status_code'],
    buckets=[0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Active HTTP requests',
    ['method', 'endpoint']
)

DATABASE_QUERIES = Counter(
    'database_queries_total',
    'Total database queries',
    ['query_type', 'table', 'user_id']
)

DATABASE_QUERY_DURATION = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type', 'table'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

CACHE_OPERATIONS = Counter(
    'cache_operations_total',
    'Cache operations',
    ['operation', 'cache_type', 'result']
)

# Standard logger
logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive performance monitoring middleware.
    
    Features:
    - Request/response timing
    - Prometheus metrics
    - Structured logging with correlation IDs
    - User activity tracking
    - Error rate monitoring
    """
    
    def __init__(self, app: ASGIApp, enable_detailed_logging: bool = True):
        super().__init__(app)
        self.enable_detailed_logging = enable_detailed_logging
    
    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID for request tracing
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Extract request metadata
        method = request.method
        path = request.url.path
        endpoint = self._normalize_endpoint(path)
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get('user-agent', 'unknown')
        
        # Start timing
        start_time = time.time()
        
        # Track active requests
        ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).inc()
        
        # Initialize response variables
        response = None
        status_code = 500
        user_id = None
        
        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code
            
            # Extract user ID from response context if available
            user_id = getattr(request.state, 'user_id', None)
            
        except Exception as e:
            logger.error(
                "Request processing failed",
                correlation_id=correlation_id,
                method=method,
                path=path,
                client_ip=client_ip,
                error=str(e),
                exc_info=True
            )
            raise
        
        finally:
           
            duration = time.time() - start_time
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                user_id=user_id or 'anonymous'
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).observe(duration)
            
            ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).dec()
            
            
            log_data = {
                "correlation_id": correlation_id,
                "method": method,
                "path": path,
                "endpoint": endpoint,
                "status_code": status_code,
                "duration_seconds": duration,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "user_id": user_id
            }
            
            if self.enable_detailed_logging:
                if status_code >= 500:
                    logger.error("Request failed with server error", **log_data)
                elif status_code >= 400:
                    logger.warning("Request failed with client error", **log_data)
                elif duration > 5.0:  # Slow requests
                    logger.warning("Slow request detected", **log_data)
                else:
                    logger.info("Request completed", **log_data)
            
            # Add correlation ID to response headers
            if response:
                response.headers["X-Correlation-ID"] = correlation_id
        
        return response
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for metrics (replace UUIDs with placeholders)."""
        import re
        
        # Replace UUIDs with {id} placeholder
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        normalized = re.sub(uuid_pattern, '{id}', path, flags=re.IGNORECASE)
        
        # Replace numeric IDs with {id} placeholder
        numeric_pattern = r'/\d+(?=/|$)'
        normalized = re.sub(numeric_pattern, '/{id}', normalized)
        
        return normalized
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers."""
        # Check for forwarded headers (load balancer/proxy)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else 'unknown'


class DatabasePerformanceTracker:
    """Context manager for tracking database query performance."""
    
    def __init__(self, query_type: str, table: str, user_id: Optional[str] = None):
        self.query_type = query_type
        self.table = table
        self.user_id = user_id
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            
            # Update metrics
            DATABASE_QUERIES.labels(
                query_type=self.query_type,
                table=self.table,
                user_id=self.user_id or 'anonymous'
            ).inc()
            
            DATABASE_QUERY_DURATION.labels(
                query_type=self.query_type,
                table=self.table
            ).observe(duration)
            
            # Log slow queries
            if duration > 1.0:
                logger.warning(
                    "Slow database query detected",
                    query_type=self.query_type,
                    table=self.table,
                    duration_seconds=duration,
                    user_id=self.user_id
                )


class CachePerformanceTracker:
    """Utility for tracking cache operations."""
    
    @staticmethod
    def track_operation(operation: str, cache_type: str, result: str):
        """Track cache operation (hit/miss/set/delete)."""
        CACHE_OPERATIONS.labels(
            operation=operation,
            cache_type=cache_type,
            result=result
        ).inc()
        
        logger.debug(
            "Cache operation",
            operation=operation,
            cache_type=cache_type,
            result=result
        )


@contextmanager
def track_database_query(query_type: str, table: str, user_id: Optional[str] = None):
    """Context manager for tracking database queries."""
    with DatabasePerformanceTracker(query_type, table, user_id):
        yield


def track_cache_hit(cache_type: str):
    """Track cache hit."""
    CachePerformanceTracker.track_operation('get', cache_type, 'hit')


def track_cache_miss(cache_type: str):
    """Track cache miss."""
    CachePerformanceTracker.track_operation('get', cache_type, 'miss')


def track_cache_set(cache_type: str):
    """Track cache set operation."""
    CachePerformanceTracker.track_operation('set', cache_type, 'success')


def get_performance_metrics() -> Dict[str, Any]:
    """Get current performance metrics summary."""
    return {
        "active_requests": ACTIVE_REQUESTS._value._value,
        "total_requests": REQUEST_COUNT._value._value,
        "avg_response_time": REQUEST_DURATION._sum._value / max(REQUEST_DURATION._count._value, 1),
        "total_db_queries": DATABASE_QUERIES._value._value,
        "cache_hit_rate": _calculate_cache_hit_rate()
    }


def _calculate_cache_hit_rate() -> float:
    """Calculate cache hit rate percentage."""
    total_hits = 0
    total_requests = 0
    
    for sample in CACHE_OPERATIONS.collect()[0].samples:
        if sample.labels.get('operation') == 'get':
            total_requests += sample.value
            if sample.labels.get('result') == 'hit':
                total_hits += sample.value
    
    if total_requests == 0:
        return 0.0
    
    return (total_hits / total_requests) * 100


async def metrics_endpoint(request: Request) -> Response:
    """Prometheus metrics endpoint."""
    metrics_data = generate_latest()
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST,
        headers={'Cache-Control': 'no-cache'}
    ) 