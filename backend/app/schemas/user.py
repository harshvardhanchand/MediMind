import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

# Pydantic schema for reading user information from the database
class UserRead(BaseModel):
    user_id: uuid.UUID = Field(..., description="Internal database UUID for the user")
    supabase_id: Optional[str] = Field(None, description="Supabase user ID (auth.users.id)")
    email: str = Field(..., description="User's email address")
    created_at: datetime = Field(..., description="Timestamp when the user was created in DB")
    updated_at: datetime = Field(..., description="Timestamp when the user was last updated in DB")
    last_login: Optional[datetime] = Field(None, description="Timestamp of the user's last login (from Supabase)")
    # user_metadata and app_metadata from Supabase can be included if needed,
    # but typically the /me endpoint returns the internal user profile.
    # Supabase metadata is in the raw token if client needs it directly.
    # user_metadata: Optional[Dict[str, Any]] = Field(None, description="User-specific metadata from Supabase")
    # app_metadata: Optional[Dict[str, Any]] = Field(None, description="Application-specific metadata from Supabase")

    class Config:
        orm_mode = True # Allow mapping from ORM model 