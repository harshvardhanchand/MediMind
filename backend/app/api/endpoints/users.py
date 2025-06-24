from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session 

from app.core.auth import get_current_user
from app.models.user import User as UserModel 
from app.schemas.user import UserRead, UserProfileUpdate 
from app.db.session import get_db 


router = APIRouter()

@router.get("/me", response_model=UserRead, summary="Get current user details")
async def read_users_me(current_user: UserModel = Depends(get_current_user)):
    """
    Fetch the details for the currently authenticated user.
    The `get_current_user` dependency handles token verification and
    fetches the user object from the database.
    """
   
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
   
    update_data = profile_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    
    db.commit()
    db.refresh(current_user)
    
    return current_user 