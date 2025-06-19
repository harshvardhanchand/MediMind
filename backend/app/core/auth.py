import logging
from typing import Optional, Dict, Any
import time
from threading import Lock

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from sqlalchemy.orm import Session
import uuid

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ErrorCode
from app.middleware.rate_limit import get_client_ip
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

# JWT Token Cache with TTL
class TokenCache:
    """Thread-safe token cache with TTL."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, tuple] = {}
        self.default_ttl = default_ttl
        self.lock = Lock()
        self.hits = 0
        self.misses = 0
    
    def get(self, token_key: str) -> Optional[Dict[str, Any]]:
        """Get cached token data if still valid."""
        with self.lock:
            if token_key in self.cache:
                data, timestamp = self.cache[token_key]
                if time.time() - timestamp < self.default_ttl:
                    self.hits += 1
                    return data
                else:
                    # Remove expired entry
                    del self.cache[token_key]
            
            self.misses += 1
            return None
    
    def set(self, token_key: str, data: Dict[str, Any]) -> None:
        """Cache token data with current timestamp."""
        with self.lock:
            self.cache[token_key] = (data, time.time())
    
    def invalidate(self, token_key: str) -> None:
        """Remove specific token from cache."""
        with self.lock:
            self.cache.pop(token_key, None)
    
    def clear_expired(self) -> int:
        """Clear all expired tokens and return count."""
        current_time = time.time()
        expired_keys = []
        
        with self.lock:
            for key, (_, timestamp) in self.cache.items():
                if current_time - timestamp >= self.default_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": f"{hit_rate:.2f}%",
                "cached_tokens": len(self.cache)
            }

# Initialize token cache
token_cache = TokenCache(default_ttl=300)  # 5 minutes

# Supabase client initialization
supabase: Optional[Client] = None
try:
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        # Convert AnyHttpUrl to string for the client
        supabase_url_str = str(settings.SUPABASE_URL)
        supabase = create_client(supabase_url_str, settings.SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
    else:
        logger.error("Supabase URL or key not provided")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")

# Security scheme for Swagger UI - using standard FastAPI behavior
security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> Dict[str, Any]:
    """
    Verify Supabase JWT token from the Authorization header with caching.
    
    Args:
        credentials: HTTP Authorization credentials from Bearer token
        request: FastAPI request object for logging context
    
    Returns:
        dict: The decoded token claims containing user information
        
    Raises:
        AuthenticationError: If token is missing, invalid, or expired
    """
    if not supabase:
        logger.error("Supabase client not initialized, authentication not available")
        raise AuthenticationError(
            "Authentication service not available",
            ErrorCode.SERVICE_UNAVAILABLE
        )
    
    token = credentials.credentials
    
    # Create cache key from token hash (first 32 chars for security)
    token_key = f"token:{hash(token) % 1000000}"
    
    # Try to get from cache first
    cached_data = token_cache.get(token_key)
    if cached_data:
        logger.debug(f"Token cache hit for user {cached_data.get('sub', 'unknown')}")
        return cached_data
    
    # Debug: Log the JWT secret status and token info
    logger.debug(f"🔑 JWT Secret configured: {bool(settings.SUPABASE_JWT_SECRET)}")
    logger.debug(f"🎫 Token verification - Cache miss, validating token")
    
    try:
        # Verify the token
        if not settings.SUPABASE_JWT_SECRET:
            logger.error("JWT secret not configured")
            raise AuthenticationError(
                "Authentication configuration error",
                ErrorCode.CONFIGURATION_ERROR
            )
        
        # Decode the token manually with the JWT secret
        decoded_token = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_signature": True, "verify_aud": False}
        )
        
        # Get user ID from the token claims
        user_id = decoded_token.get("sub")
        
        if not user_id:
            raise AuthenticationError(
                "Invalid token payload - missing user ID",
                ErrorCode.INVALID_TOKEN
            )
        
        # Cache the decoded token for future requests
        token_cache.set(token_key, decoded_token)
        
        # Log successful authentication
        client_ip = get_client_ip(request) if request else "unknown"
        logger.info(
            f"✅ User authenticated successfully - user_id: {user_id}",
            extra={
                "structured_data": {
                    "user_id": user_id,
                    "client_ip": client_ip,
                    "cache_hit": False
                }
            },
        )
        
        return decoded_token
        
    except jwt.ExpiredSignatureError:
        # Invalidate cached token if it exists
        token_cache.invalidate(token_key)
        
        logger.warning(
            f"❌ Expired token used",
            extra={
                "structured_data": {
                    "client_ip": get_client_ip(request) if request else "unknown",
                }
            },
        )
        raise AuthenticationError(
            "Token has expired. Please login again.",
            ErrorCode.TOKEN_EXPIRED
        )
        
    except jwt.InvalidTokenError as e:
        # Invalidate cached token if it exists
        token_cache.invalidate(token_key)
        
        logger.warning(
            f"❌ Invalid token used - Error: {str(e)}",
            extra={
                "structured_data": {
                    "client_ip": get_client_ip(request) if request else "unknown",
                }
            },
        )
        raise AuthenticationError(
            "Invalid authentication token",
            ErrorCode.INVALID_TOKEN
        )
        
    except Exception as e:
        # Invalidate cached token if it exists
        token_cache.invalidate(token_key)
        
        logger.error(
            f"Authentication error: {str(e)}",
            exc_info=True,
            extra={
                "structured_data": {
                    "client_ip": get_client_ip(request) if request else "unknown",
                }
            },
        )
        raise AuthenticationError(
            "Authentication failed",
            ErrorCode.INTERNAL_ERROR
        )

# --- Helper function to get internal user ID from token data ---
def get_user_id_from_token(db: Session, token_data: dict) -> uuid.UUID:
    """Extract and validate internal application user ID from decoded token data."""
    
    supabase_id = token_data.get("sub")
    if not supabase_id:
        logger.error("Supabase ID (sub) not found in token payload.")
        raise AuthenticationError(
            "Invalid authentication token payload: Missing 'sub' claim.",
            ErrorCode.INVALID_TOKEN
        )
    
    # Import user_repo locally to avoid circular imports if auth is imported by models/repositories
    from app.repositories.user_repo import user_repo 

    user = user_repo.get_by_supabase_id_sync(db, supabase_id=supabase_id)
    if not user:
        logger.warning(f"User with Supabase ID '{supabase_id}' not found in the database.")
        raise AuthenticationError(
            "User associated with this token not found in the application.",
            ErrorCode.USER_NOT_FOUND
        )
    
    return user.user_id

# --- Dependency to get current user ---
async def get_current_user(
    token_data: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from the database.
    
    This dependency can be used in endpoints to directly access the User model
    of the currently authenticated user. It builds on the verify_token dependency
    to ensure proper authentication.
    
    Args:
        token_data: The decoded JWT token data (from verify_token dependency)
        db: Database session (from get_db dependency)
        
    Returns:
        User: The authenticated user's database model
        
    Raises:
        AuthenticationError: If user is not found in the database or token is invalid
    """
    try:
        user_id = get_user_id_from_token(db, token_data)
        
        # Import user_repo locally to avoid circular imports
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

# --- Cache management functions ---
async def clear_expired_tokens() -> int:
    """Clear expired tokens from cache. Returns number of cleared tokens."""
    return token_cache.clear_expired()

def get_token_cache_stats() -> Dict[str, Any]:
    """Get token cache statistics."""
    return token_cache.get_stats()

def invalidate_user_tokens(user_id: str) -> None:
    """Invalidate all cached tokens for a specific user (on logout, etc.)."""
    # Note: This is a simple implementation. For production, you might want
    # to store user_id -> token_key mappings for more efficient invalidation
    token_cache.cache.clear()  # Simple approach: clear all cache
    logger.info(f"Invalidated all cached tokens due to user {user_id} logout") 