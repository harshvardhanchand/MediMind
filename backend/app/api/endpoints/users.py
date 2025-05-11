from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session # Ensure Session is imported if used, though get_current_user might not need it directly here

from app.core.auth import get_current_user
from app.models.user import User as UserModel # Import the SQLAlchemy model
from app.schemas.user import UserRead # Import the Pydantic schema for response
# from app.db.session import get_db # Not strictly needed if only using get_current_user which handles db session for user retrieval

router = APIRouter()

@router.get("/me", response_model=UserRead, summary="Get current user details")
async def read_users_me(current_user: UserModel = Depends(get_current_user)):
    """
    Fetch the details for the currently authenticated user.
    The `get_current_user` dependency handles token verification and
    fetches the user object from the database.
    """
    # current_user is already an instance of the User SQLAlchemy model
    # Pydantic will automatically map it to UserRead due to response_model and orm_mode=True
    return current_user 