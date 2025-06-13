import uuid
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from decimal import Decimal

# Pydantic schema for reading user information from the database
class UserRead(BaseModel):
    user_id: uuid.UUID = Field(..., description="Internal database UUID for the user")
    supabase_id: Optional[str] = Field(None, description="Supabase user ID (auth.users.id)")
    email: str = Field(..., description="User's email address")
    created_at: datetime = Field(..., description="Timestamp when the user was created in DB")
    updated_at: datetime = Field(..., description="Timestamp when the user was last updated in DB")
    last_login: Optional[datetime] = Field(None, description="Timestamp of the user's last login (from Supabase)")
    
    # Profile fields
    name: Optional[str] = Field(None, description="User's full name")
    date_of_birth: Optional[date] = Field(None, description="User's date of birth")
    weight: Optional[Decimal] = Field(None, description="Weight in kg")
    height: Optional[int] = Field(None, description="Height in cm")
    gender: Optional[str] = Field(None, description="Biological gender")
    profile_photo_url: Optional[str] = Field(None, description="URL to profile photo")
    
    # Keep metadata fields for backward compatibility
    user_metadata: Optional[Dict[str, Any]] = Field(None, description="User metadata from Supabase")
    app_metadata: Optional[Dict[str, Any]] = Field(None, description="Application-specific metadata from Supabase")

    class Config:
        from_attributes = True # Allow mapping from ORM model

# Pydantic schema for creating new users
class UserCreate(BaseModel):
    email: str = Field(..., description="User's email address")
    supabase_id: str = Field(..., description="Supabase user ID (auth.users.id)")
    user_metadata: Optional[Dict[str, Any]] = Field(None, description="User-specific metadata from Supabase")
    app_metadata: Optional[Dict[str, Any]] = Field(None, description="Application-specific metadata from Supabase")

# Pydantic schema for updating user profile
class UserProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, description="User's full name", max_length=100)
    date_of_birth: Optional[date] = Field(None, description="User's date of birth (YYYY-MM-DD)")
    weight: Optional[float] = Field(None, description="Weight in kg", gt=0, le=1000)
    height: Optional[int] = Field(None, description="Height in cm", gt=0, le=300)
    gender: Optional[str] = Field(None, description="Biological gender")
    profile_photo_url: Optional[str] = Field(None, description="URL to profile photo", max_length=500)
    
    @validator('gender')
    def validate_gender(cls, v):
        if v is not None and v not in ['male', 'female', 'other']:
            raise ValueError('Gender must be one of: male, female, other')
        return v
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        if v is not None:
            today = date.today()
            if v > today:
                raise ValueError('Date of birth cannot be in the future')
            # Check if age would be reasonable (0-150 years)
            age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
            if age > 150:
                raise ValueError('Date of birth indicates unrealistic age')
        return v 