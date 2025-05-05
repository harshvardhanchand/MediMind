from uuid import UUID
from typing import Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
# from app.schemas.user import UserRead # Not strictly needed for current methods
from .base import CRUDBase 

class CRUDUser(CRUDBase[User, Any, Any]): # Use Any for unused Create/Update schemas
    async def get_by_supabase_id(self, db: AsyncSession, *, supabase_id: str) -> Optional[User]:
        """Get a user by their Supabase ID."""
        stmt = select(self.model).where(self.model.supabase_id == supabase_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """Get a user by their email address."""
        stmt = select(self.model).where(self.model.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    # Potentially add a create method here later if the backend needs to create
    # user records directly (e.g., sync from Supabase Auth webhook)
    # async def create_user(self, db: AsyncSession, *, ...) -> User:
    #     ...

# Create a singleton instance
user_repo = CRUDUser(User) 