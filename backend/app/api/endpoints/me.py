from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_token
from app.middleware.rate_limit import limiter
from app.db.session import get_async_db
from app.repositories.user_repo import user_repo
from app.schemas.user import UserRead
from app.models.user import User

router = APIRouter(tags=["user"])

@router.get("/me", summary="Get current user DB profile", response_model=UserRead)
@limiter.limit("30/minute")
async def get_current_user_profile(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    token_data: dict = Depends(verify_token)
):
    """
    Get the database profile for the currently authenticated user.
    
    This endpoint requires a valid Supabase JWT token and is rate-limited.
    It fetches the user record from the database.
    
    Returns:
        UserRead: User profile information from the database.
    """
    supabase_id = token_data.get("sub")
    if not supabase_id:
        # This case should ideally be caught by verify_token if sub is mandatory there
        raise HTTPException(status_code=401, detail="Invalid token: Missing sub claim")

    # user_repo.get_by_supabase_id is already async
    user: User | None = await user_repo.get_by_supabase_id(db, supabase_id=supabase_id)
    
    if not user:
        # This might indicate a sync issue if a user has a valid token but no DB record
        raise HTTPException(status_code=404, detail="User not found in database")
    
    return user # Pydantic will convert User ORM model to UserRead schema 