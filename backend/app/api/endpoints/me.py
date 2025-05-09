from fastapi import APIRouter, Depends, Request


from app.core.auth import verify_token
from app.middleware.rate_limit import limiter

router = APIRouter(tags=["user"])

@router.get("/me", summary="Get current user info")
@limiter.limit("30/minute")
async def get_current_user(
    request: Request,
    token_data: dict = Depends(verify_token)
):
    """
    Get information about the currently authenticated user.
    
    This endpoint requires a valid Supabase JWT token and is rate-limited
    to 30 requests per minute per user.
    
    Returns:
        dict: Basic user information from the token
    """
    # Extract relevant user information from the token
    user_info = {
        "id": token_data.get("sub"),
        "email": token_data.get("email"),
        "app_metadata": token_data.get("app_metadata", {}),
        "user_metadata": token_data.get("user_metadata", {})
    }
    
    return user_info 