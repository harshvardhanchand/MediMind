import logging
from typing import Optional, Dict, Any

import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from sqlalchemy.orm import Session
import uuid

from app.core.config import settings
from app.middleware.rate_limit import get_client_ip
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

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

# --- Helper function to get internal user ID from token data ---
def get_user_id_from_token(db: Session, token_data: dict) -> uuid.UUID:
    """Extract and validate internal application user ID from decoded token data."""
    
    supabase_id = token_data.get("sub")
    if not supabase_id:
        logger.error("Supabase ID (sub) not found in token payload.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid authentication token payload: Missing 'sub' claim."
        )
    
    # Import user_repo locally to avoid circular imports if auth is imported by models/repositories
    from app.repositories.user_repo import user_repo 

    user = user_repo.get_by_supabase_id_sync(db, supabase_id=supabase_id)
    if not user:
        logger.warning(f"User with Supabase ID '{supabase_id}' not found in the database.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Or 403 if preferred for "valid token, but no app user"
            detail="User associated with this token not found in the application."
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
        HTTPException: If user is not found in the database or token is invalid
    """
    # Get the Supabase user ID from the token
    supabase_id = token_data.get("sub")
    if not supabase_id:
        logger.error("Supabase ID (sub) not found in token payload.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid authentication token payload: Missing 'sub' claim."
        )
    
    # Import user_repo locally to avoid circular imports
    from app.repositories.user_repo import user_repo
    
    # Get the user from the database using Supabase ID
    user = user_repo.get_by_supabase_id_sync(db, supabase_id=supabase_id)
    if not user:
        logger.warning(f"User with Supabase ID '{supabase_id}' not found in the database.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with this token not found in the application."
        )
    
    return user 