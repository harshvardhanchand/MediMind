"""
UserRepository module - Full implementation of the user repository

"""
from typing import Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.future import select

from app.models.user import User
from .base import CRUDBase 

class UserRepository(CRUDBase[User, Any, Any]): 
    async def get_by_supabase_id(self, db: AsyncSession, *, supabase_id: str) -> Optional[User]:
        """Get a user by their Supabase ID."""
        stmt = select(self.model).where(self.model.supabase_id == supabase_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    # Synchronous version for compatibility with tests
    def get_by_supabase_id_sync(self, db: Session, *, supabase_id: str) -> Optional[User]:
        """Synchronous version of get_by_supabase_id for testing purposes."""
        stmt = select(self.model).where(self.model.supabase_id == supabase_id)
        result = db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """Get a user by their email address."""
        stmt = select(self.model).where(self.model.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    # Add synchronous version for compatibility
    def get_by_email_sync(self, db: Session, *, email: str) -> Optional[User]:
        """Synchronous version of get_by_email for testing purposes."""
        stmt = select(self.model).where(self.model.email == email)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

# Create a singleton instance
user_repo = UserRepository(User) 