import uuid

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

# Pydantic schema for reading user information
# Based on the structure returned by the /me endpoint and Supabase token data
class UserRead(BaseModel):
    id: Optional[str] = Field(None, description="Supabase user ID (from token's sub field)") # Typically the supabase ID
    user_db_id: Optional[uuid.UUID] = Field(None, description="Internal database UUID for the user") # Optional: Add if needed
    email: Optional[str] = Field(None, description="User's email address")
    app_metadata: Optional[Dict[str, Any]] = Field(None, description="Application-specific metadata from Supabase")
    user_metadata: Optional[Dict[str, Any]] = Field(None, description="User-specific metadata from Supabase")
    # Add other fields from your User model if needed for API responses
    # created_at: Optional[datetime] = None
    # updated_at: Optional[datetime] = None
    # last_login: Optional[datetime] = None

    class Config:
        orm_mode = True # Allow mapping from ORM model 