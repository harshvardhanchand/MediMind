import uuid
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field

from app.models.health_reading import HealthReadingType # Import the enum

# Base schema with common fields
class HealthReadingBase(BaseModel):
    reading_type: HealthReadingType = Field(..., description="Type of health reading")
    numeric_value: Optional[float] = Field(None, description="Numeric value of the reading, if applicable")
    unit: Optional[str] = Field(None, description="Unit for the numeric value, if applicable")
    systolic_value: Optional[int] = Field(None, description="Systolic value for blood pressure")
    diastolic_value: Optional[int] = Field(None, description="Diastolic value for blood pressure")
    text_value: Optional[str] = Field(None, description="Text value of the reading, if applicable")
    json_value: Optional[Dict[str, Any]] = Field(None, description="JSON object for complex reading values")
    reading_date: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the reading was taken or recorded")
    notes: Optional[str] = Field(None, description="Additional notes about the reading")
    source: Optional[str] = Field(None, description="Source of the health reading (e.g., manual, wearable)")
    related_document_id: Optional[uuid.UUID] = Field(None, description="ID of a related document")

    class Config:
        use_enum_values = True # Ensure enum values are used, not enum members

# Schema for creating a health reading (input)
class HealthReadingCreate(HealthReadingBase):
    pass

# Schema for updating a health reading (input)
# All fields are optional for partial updates
class HealthReadingUpdate(BaseModel):
    reading_type: Optional[HealthReadingType] = Field(None, description="Type of health reading")
    numeric_value: Optional[float] = Field(None, description="Numeric value of the reading, if applicable")
    unit: Optional[str] = Field(None, description="Unit for the numeric value, if applicable")
    systolic_value: Optional[int] = Field(None, description="Systolic value for blood pressure")
    diastolic_value: Optional[int] = Field(None, description="Diastolic value for blood pressure")
    text_value: Optional[str] = Field(None, description="Text value of the reading, if applicable")
    json_value: Optional[Dict[str, Any]] = Field(None, description="JSON object for complex reading values")
    reading_date: Optional[datetime] = Field(None, description="Timestamp when the reading was taken or recorded")
    notes: Optional[str] = Field(None, description="Additional notes about the reading")
    source: Optional[str] = Field(None, description="Source of the health reading (e.g., manual, wearable)")
    related_document_id: Optional[uuid.UUID] = Field(None, description="ID of a related document")

    class Config:
        use_enum_values = True

# Schema for reading a health reading (output)
class HealthReadingResponse(HealthReadingBase):
    health_reading_id: uuid.UUID = Field(..., description="Unique identifier for the health reading")
    user_id: uuid.UUID = Field(..., description="Identifier of the user who owns the reading")
    created_at: datetime = Field(..., description="Timestamp when the reading was created")
    updated_at: datetime = Field(..., description="Timestamp when the reading was last updated")

    class Config:
        orm_mode = True # For compatibility with SQLAlchemy models
        use_enum_values = True 