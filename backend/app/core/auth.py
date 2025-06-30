import logging
from typing import  Dict, Any
import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uuid

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ErrorCode
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)


security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> Dict[str, Any]:
    """
    Verify Supabase JWT token - SIMPLIFIED VERSION.
    
    Args:
        credentials: HTTP Authorization credentials from Bearer token
        request: FastAPI request object for logging context (optional)
    
    Returns:
        dict: The decoded token claims containing user information
        
    Raises:
        AuthenticationError: If token is missing, invalid, or expired
    """
    if not settings.SUPABASE_JWT_SECRET:
        logger.error("SUPABASE_JWT_SECRET not configured")
        raise AuthenticationError(
            "Authentication not configured",
            ErrorCode.CONFIGURATION_ERROR
        )
    
    token = credentials.credentials
    
    try:
        
        decoded_token = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"  
        )
        
        user_id = decoded_token.get("sub")
        if not user_id:
            raise AuthenticationError(
                "Invalid token payload - missing user ID",
                ErrorCode.INVALID_TOKEN
            )
        
        # Simple logging
        logger.debug(f"User {user_id} authenticated successfully")
        return decoded_token
        
    except jwt.ExpiredSignatureError:
        logger.warning("Expired token used")
        raise AuthenticationError(
            "Token has expired. Please login again.",
            ErrorCode.TOKEN_EXPIRED
        )
        
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise AuthenticationError(
            "Invalid authentication token",
            ErrorCode.INVALID_TOKEN
        )
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}", exc_info=True)
        raise AuthenticationError(
            "Authentication failed",
            ErrorCode.INTERNAL_ERROR
        )

def get_user_id_from_token(db: Session, token_data: dict) -> uuid.UUID:
    """Extract and validate internal application user ID from decoded token data."""
    supabase_id = token_data.get("sub")
    if not supabase_id:
        logger.error("Supabase ID (sub) not found in token payload.")
        raise AuthenticationError(
            "Invalid authentication token payload: Missing 'sub' claim.",
            ErrorCode.INVALID_TOKEN
        )
    
    from app.repositories.user_repo import user_repo 
    
    user = user_repo.get_by_supabase_id_sync(db, supabase_id=supabase_id)
    if not user:
        logger.warning(f"User with Supabase ID '{supabase_id}' not found in the database.")
        raise AuthenticationError(
            "User associated with this token not found in the application.",
            ErrorCode.USER_NOT_FOUND
        )
    
    return user.user_id

async def get_current_user(
    token_data: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from the database."""
    try:
        user_id = get_user_id_from_token(db, token_data)
        
        from app.repositories.user_repo import user_repo
        user = user_repo.get(db, id=user_id)
        if not user:
            raise AuthenticationError(
                "User not found in database",
                ErrorCode.USER_NOT_FOUND
            )
        
        return user
        
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}", exc_info=True)
        raise AuthenticationError(
            "Failed to get user information",
            ErrorCode.INTERNAL_ERROR
        )


async def clear_expired_tokens() -> int:
    """Deprecated: No cache to clear. Returns 0."""
    return 0

def get_token_cache_stats() -> Dict[str, Any]:
    """Deprecated: No cache stats. Returns empty stats."""
    return {"hits": 0, "misses": 0, "hit_rate": "0.00%", "cached_tokens": 0}

def invalidate_user_tokens(user_id: str) -> None:
    """Deprecated: No cache to invalidate."""
    logger.debug(f"Token invalidation called for user {user_id} - no-op (no cache)") 