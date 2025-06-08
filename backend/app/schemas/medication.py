import uuid
from datetime import datetime, date
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.models.medication import MedicationFrequency, MedicationStatus

# Base schema for common medication attributes
class MedicationBase(BaseModel):
    name: str = Field(..., description="Name of the medication")
    dosage: Optional[str] = Field(None, description="Dosage of the medication (e.g., 10mg)")
    frequency: MedicationFrequency = Field(..., description="How often the medication is taken")
    frequency_details: Optional[str] = Field(None, description="Additional details about the frequency")
    start_date: Optional[date] = Field(None, description="Date when the medication was started")
    end_date: Optional[date] = Field(None, description="Date when the medication will end or ended")
    time_of_day: Optional[List[str]] = Field(None, description="Times of day when medication is taken (e.g., ['08:00', '20:00'])")
    with_food: Optional[bool] = Field(None, description="Whether the medication should be taken with food")
    reason: Optional[str] = Field(None, description="Reason for taking the medication")
    prescribing_doctor: Optional[str] = Field(None, description="Doctor who prescribed the medication")
    pharmacy: Optional[str] = Field(None, description="Pharmacy where the medication is filled")
    notes: Optional[str] = Field(None, description="Additional notes about the medication")
    related_document_id: Optional[uuid.UUID] = Field(None, description="ID of a related document (e.g., prescription)")
    tags: Optional[List[str]] = Field(None, description="List of tags or categories for this medication")

# Schema for creating a medication (input)
class MedicationCreate(MedicationBase):
    status: MedicationStatus = Field(default=MedicationStatus.ACTIVE, description="Current status of the medication")

# Schema for updating a medication (input)
class MedicationUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Name of the medication")
    dosage: Optional[str] = Field(None, description="Dosage of the medication (e.g., 10mg)")
    frequency: Optional[MedicationFrequency] = Field(None, description="How often the medication is taken")
    frequency_details: Optional[str] = Field(None, description="Additional details about the frequency")
    start_date: Optional[date] = Field(None, description="Date when the medication was started")
    end_date: Optional[date] = Field(None, description="Date when the medication will end or ended")
    time_of_day: Optional[List[str]] = Field(None, description="Times of day when medication is taken (e.g., ['08:00', '20:00'])")
    with_food: Optional[bool] = Field(None, description="Whether the medication should be taken with food")
    reason: Optional[str] = Field(None, description="Reason for taking the medication")
    prescribing_doctor: Optional[str] = Field(None, description="Doctor who prescribed the medication")
    pharmacy: Optional[str] = Field(None, description="Pharmacy where the medication is filled")
    notes: Optional[str] = Field(None, description="Additional notes about the medication")
    status: Optional[MedicationStatus] = Field(None, description="Current status of the medication")
    related_document_id: Optional[uuid.UUID] = Field(None, description="ID of a related document (e.g., prescription)")
    tags: Optional[List[str]] = Field(None, description="List of tags or categories for this medication")

# Schema for reading a medication (output)
class MedicationResponse(MedicationBase):
    medication_id: uuid.UUID = Field(..., description="Unique identifier for the medication")
    user_id: uuid.UUID = Field(..., description="Identifier of the user who owns the medication")
    status: MedicationStatus = Field(..., description="Current status of the medication")
    created_at: datetime = Field(..., description="Timestamp when the medication was created")
    updated_at: datetime = Field(..., description="Timestamp when the medication was last updated")

    class Config:
        from_attributes = True # Compatibility with SQLAlchemy models 