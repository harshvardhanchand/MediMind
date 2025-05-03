import logging
from typing import Optional, Dict, Any

import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client

from app.core.config import settings
from app.middleware.rate_limit import get_client_ip

logger = logging.getLogger(__name__)

# Supabase client initialization
supabase: Optional[Client] = None
try:
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
    else:
        logger.error("Supabase URL or key not provided")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")

# Security scheme for Swagger UI
security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> Dict[str, Any]:
    """
    Verify Supabase JWT token from the Authorization header.
    
    Args:
        credentials: HTTP Authorization credentials from Bearer token
        request: FastAPI request object for logging context
    
    Returns:
        dict: The decoded token claims containing user information
        
    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    if not supabase:
        logger.error("Supabase client not initialized, authentication not available")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available"
        )
    
    token = credentials.credentials
    
    try:
        # Verify the token
        if not settings.SUPABASE_JWT_SECRET:
            logger.error("JWT secret not configured")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication configuration error"
            )
        
        # Decode the token manually with the JWT secret
        decoded_token = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_signature": True}
        )
        
        # Get user ID from the token claims
        user_id = decoded_token.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Log successful authentication
        client_ip = get_client_ip(request) if request else "unknown"
        logger.info(
            f"User authenticated successfully",
            extra={
                "structured_data": {
                    "user_id": user_id,
                    "client_ip": client_ip,
                }
            },
        )
        
        return decoded_token
    except jwt.ExpiredSignatureError:
        # Log token expiration
        logger.warning(
            f"Expired token used",
            extra={
                "structured_data": {
                    "client_ip": get_client_ip(request) if request else "unknown",
                }
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please login again."
        )
    except jwt.InvalidTokenError:
        # Log invalid token
        logger.warning(
            f"Invalid token used",
            extra={
                "structured_data": {
                    "client_ip": get_client_ip(request) if request else "unknown",
                }
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except Exception as e:
        # Log unexpected errors
        logger.error(
            f"Authentication error: {str(e)}",
            exc_info=True,
            extra={
                "structured_data": {
                    "client_ip": get_client_ip(request) if request else "unknown",
                }
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        ) 