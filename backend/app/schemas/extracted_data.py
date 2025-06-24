import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.models.extracted_data import ReviewStatus
from app.schemas.document import DocumentRead


class ExtractedDataBase(BaseModel):
    content: Any = Field(..., description="Structured data extracted from the document as JSON (can be dict, list, or any JSON structure)")
    raw_text: Optional[str] = Field(None, description="Raw text extracted by OCR, if available")
    review_status: ReviewStatus = Field(..., description="Current review status of the extracted data")
    reviewed_by_user_id: Optional[uuid.UUID] = Field(None, description="ID of the user who reviewed/corrected the data")
    review_timestamp: Optional[datetime] = Field(None, description="Timestamp when the data was last reviewed/corrected")


class ExtractedDataCreate(BaseModel):
    content: Any = Field(..., description="Structured data extracted from the document as JSON (can be dict, list, or any JSON structure)")
    raw_text: Optional[str] = Field(None, description="Raw text extracted by OCR, if available")
   
class ExtractedDataRead(ExtractedDataBase):
    extracted_data_id: uuid.UUID = Field(..., description="Unique identifier for the extracted data")
    document_id: uuid.UUID = Field(..., description="Identifier of the document this data belongs to")
    extraction_timestamp: datetime = Field(..., description="Timestamp when the data was extracted")

    class Config:
        from_attributes = True 


class ExtractedDataUpdate(BaseModel):
    content: Optional[Any] = Field(None, description="Corrected structured data (can be dict, list, or any JSON structure)")
    review_status: Optional[ReviewStatus] = Field(None, description="Updated review status (e.g., approved, corrected)")
    

ExtractedDataResponse = ExtractedDataRead


class ExtractedDataStatusUpdate(BaseModel):
    review_status: ReviewStatus = Field(..., description="New review status to set")


class ExtractedDataContentUpdate(BaseModel):
    content: Any = Field(..., description="Updated structured content (can be dict, list, or any JSON structure)")
    changed_fields: Optional[List[Dict[str, Any]]] = Field(None, description="List of fields that were changed by the user")
    trigger_selective_reprocessing: Optional[bool] = Field(False, description="Whether to trigger selective reprocessing for changed fields")


class ExtractionDetailsResponse(BaseModel):
    document: DocumentRead
    extracted_data: ExtractedDataRead

    class Config:
        from_attributes = True 