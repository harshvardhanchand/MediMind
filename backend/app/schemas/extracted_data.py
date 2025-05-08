import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from app.models.extracted_data import ReviewStatus

# Base schema for extracted data attributes
class ExtractedDataBase(BaseModel):
    content: Dict[str, Any] = Field(..., description="Structured data extracted from the document as JSON")
    raw_text: Optional[str] = Field(None, description="Raw text extracted by OCR, if available")
    review_status: ReviewStatus = Field(..., description="Current review status of the extracted data")
    reviewed_by_user_id: Optional[uuid.UUID] = Field(None, description="ID of the user who reviewed/corrected the data")
    review_timestamp: Optional[datetime] = Field(None, description="Timestamp when the data was last reviewed/corrected")

# Schema for creating extracted data (input)
# document_id will be set based on the related document
class ExtractedDataCreate(BaseModel):
    content: Dict[str, Any] = Field(..., description="Structured data extracted from the document as JSON")
    raw_text: Optional[str] = Field(None, description="Raw text extracted by OCR, if available")
    # Status typically starts as PENDING_REVIEW

# Schema for reading extracted data (output)
class ExtractedDataRead(ExtractedDataBase):
    extracted_data_id: uuid.UUID = Field(..., description="Unique identifier for the extracted data")
    document_id: uuid.UUID = Field(..., description="Identifier of the document this data belongs to")
    extraction_timestamp: datetime = Field(..., description="Timestamp when the data was extracted")

    class Config:
        orm_mode = True # Compatibility with SQLAlchemy models

# Schema for updating extracted data (e.g., during user review)
class ExtractedDataUpdate(BaseModel):
    content: Optional[Dict[str, Any]] = Field(None, description="Corrected structured data")
    review_status: Optional[ReviewStatus] = Field(None, description="Updated review status (e.g., approved, corrected)")
    # reviewed_by_user_id and review_timestamp should be set by the backend upon update

# Alias for API responses to use with FastAPI's response_model
ExtractedDataResponse = ExtractedDataRead

# Schema specifically for updating the review status
class ExtractedDataStatusUpdate(BaseModel):
    review_status: ReviewStatus = Field(..., description="New review status to set")

# Schema specifically for updating the content
class ExtractedDataContentUpdate(BaseModel):
    content: Dict[str, Any] = Field(..., description="Updated structured content") 