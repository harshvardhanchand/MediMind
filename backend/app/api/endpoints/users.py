from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session # Ensure Session is imported if used, though get_current_user might not need it directly here

from app.core.auth import get_current_user
from app.models.user import User as UserModel # Import the SQLAlchemy model
from app.schemas.user import UserRead, UserProfileUpdate # Import the Pydantic schema for response
from app.db.session import get_db # Import get_db for the update endpoint
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

@router.put("/me", response_model=UserRead, summary="Update current user profile")
async def update_users_me(
    profile_update: UserProfileUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the profile information for the currently authenticated user.
    """
    # Update the user fields with the provided data
    update_data = profile_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    # Commit the changes
    db.commit()
    db.refresh(current_user)
    
    return current_user 