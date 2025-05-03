from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from fastapi import Response

from app.core.config import settings

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

def get_client_ip(request: Request) -> str:
    """
    Extract the client IP address from the request.
    
    This function prioritizes X-Forwarded-For header if available
    (typically set by load balancers or proxies) and falls back
    to the direct client IP otherwise.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        str: The client's IP address
    """
    if "X-Forwarded-For" in request.headers:
        # X-Forwarded-For header value format: client, proxy1, proxy2, ...
        # We take the leftmost IP which should be the client's original IP
        forwarded_for = request.headers["X-Forwarded-For"].split(",")[0].strip()
        return forwarded_for
    
    # Fall back to direct client IP
    return get_remote_address(request) 