import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

from app.models.document import DocumentType, ProcessingStatus

# Base schema for common document attributes
class DocumentBase(BaseModel):
    original_filename: str = Field(..., description="Original filename of the uploaded document")
    document_type: DocumentType = Field(..., description="Type of the medical document")
    file_metadata: Optional[dict] = Field(None, description="Optional metadata like file size, content type")

# Schema for creating a document (input)
# Note: user_id and storage_path will be set internally
class DocumentCreate(DocumentBase):
    pass

# Schema for reading a document (output)
class DocumentRead(DocumentBase):
    document_id: uuid.UUID = Field(..., description="Unique identifier for the document")
    user_id: uuid.UUID = Field(..., description="Identifier of the user who owns the document")
    upload_timestamp: datetime = Field(..., description="Timestamp when the document was uploaded")
    processing_status: ProcessingStatus = Field(..., description="Current processing status of the document")
    storage_path: str = Field(..., description="Path or identifier for the stored document file") # Included for potential use, maybe admin only
    file_hash: Optional[str] = Field(None, description="Optional hash of the file content")

    class Config:
        orm_mode = True # Compatibility with SQLAlchemy models

# Schema for updating a document (e.g., changing status)
class DocumentUpdate(BaseModel):
    processing_status: Optional[ProcessingStatus] = Field(None, description="Update the processing status")
    file_metadata: Optional[dict] = Field(None, description="Update optional metadata") 