import uuid
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from decimal import Decimal


class MedicalCondition(BaseModel):
    condition_name: str = Field(..., description="Name of the medical condition", max_length=200)
    diagnosed_date: Optional[date] = Field(None, description="Date when condition was diagnosed")
    status: Optional[str] = Field("active", description="Status of condition: active, resolved, chronic, managed, suspected")
    severity: Optional[str] = Field(None, description="Severity: mild, moderate, severe, critical")
    diagnosing_doctor: Optional[str] = Field(None, description="Doctor who diagnosed the condition", max_length=200)
    notes: Optional[str] = Field(None, description="Additional notes about the condition", max_length=1000)
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None and v not in ['active', 'resolved', 'chronic', 'managed', 'suspected']:
            raise ValueError('Status must be one of: active, resolved, chronic, managed, suspected')
        return v
    
    @validator('severity')
    def validate_severity(cls, v):
        if v is not None and v not in ['mild', 'moderate', 'severe', 'critical']:
            raise ValueError('Severity must be one of: mild, moderate, severe, critical')
        return v


class UserRead(BaseModel):
    user_id: uuid.UUID = Field(..., description="Internal database UUID for the user")
    supabase_id: Optional[str] = Field(None, description="Supabase user ID (auth.users.id)")
    email: str = Field(..., description="User's email address")
    created_at: datetime = Field(..., description="Timestamp when the user was created in DB")
    updated_at: datetime = Field(..., description="Timestamp when the user was last updated in DB")
    last_login: Optional[datetime] = Field(None, description="Timestamp of the user's last login (from Supabase)")
    
    
    name: Optional[str] = Field(None, description="User's full name")
    date_of_birth: Optional[date] = Field(None, description="User's date of birth")
    weight: Optional[Decimal] = Field(None, description="Weight in kg")
    height: Optional[int] = Field(None, description="Height in cm")
    gender: Optional[str] = Field(None, description="Biological gender")
    profile_photo_url: Optional[str] = Field(None, description="URL to profile photo")
    medical_conditions: Optional[List[MedicalCondition]] = Field(default_factory=list, description="List of user's medical conditions")
    
   
    user_metadata: Optional[Dict[str, Any]] = Field(None, description="User metadata from Supabase")
    app_metadata: Optional[Dict[str, Any]] = Field(None, description="Application-specific metadata from Supabase")

    class Config:
        from_attributes = True 


class UserCreate(BaseModel):
    email: str = Field(..., description="User's email address")
    supabase_id: str = Field(..., description="Supabase user ID (auth.users.id)")
    user_metadata: Optional[Dict[str, Any]] = Field(None, description="User-specific metadata from Supabase")
    app_metadata: Optional[Dict[str, Any]] = Field(None, description="Application-specific metadata from Supabase")


class UserProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, description="User's full name", max_length=100)
    date_of_birth: Optional[date] = Field(None, description="User's date of birth (YYYY-MM-DD)")
    weight: Optional[float] = Field(None, description="Weight in kg", gt=0, le=1000)
    height: Optional[int] = Field(None, description="Height in cm", gt=0, le=300)
    gender: Optional[str] = Field(None, description="Biological gender")
    profile_photo_url: Optional[str] = Field(None, description="URL to profile photo", max_length=500)
    medical_conditions: Optional[List[MedicalCondition]] = Field(None, description="List of user's medical conditions")
    
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
           
            age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
            if age > 150:
                raise ValueError('Date of birth indicates unrealistic age')
        return v
    
    @validator('medical_conditions')
    def validate_medical_conditions(cls, v):
        if v is not None:
            if len(v) > 50:  # Reasonable limit
                raise ValueError('Maximum 50 medical conditions allowed')
            
            condition_names = [condition.condition_name.lower().strip() for condition in v]
            if len(condition_names) != len(set(condition_names)):
                raise ValueError('Duplicate medical conditions are not allowed')
        return v 