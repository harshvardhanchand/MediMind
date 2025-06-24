import uuid
from datetime import datetime, date
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.models.document import DocumentType, ProcessingStatus


class DocumentBase(BaseModel):
    original_filename: str = Field(..., description="Original filename of the uploaded document")
    document_type: DocumentType = Field(..., description="Type of the medical document")
    file_metadata: Optional[dict] = Field(None, description="Optional metadata like file size, content type")
    document_date: Optional[date] = Field(None, description="Actual date on the report/prescription (system-extracted or user-provided)")
    source_name: Optional[str] = Field(None, description="Doctor, lab, hospital name (system-extracted or user-provided)")
    source_location_city: Optional[str] = Field(None, description="City of the source (system-extracted or user-provided)")
    tags: Optional[List[str]] = Field(None, description="List of LLM-generated keywords/tags (system-extracted)")
    user_added_tags: Optional[List[str]] = Field(None, description="List of user-added tags")
    related_to_health_goal_or_episode: Optional[str] = Field(None, description="Link to a health goal or episode")


class DocumentCreate(DocumentBase):
    pass


class DocumentRead(DocumentBase):
    document_id: uuid.UUID = Field(..., description="Unique identifier for the document")
    user_id: uuid.UUID = Field(..., description="Identifier of the user who owns the document")
    upload_timestamp: datetime = Field(..., description="Timestamp when the document was uploaded")
    processing_status: ProcessingStatus = Field(..., description="Current processing status of the document")
    storage_path: str = Field(..., description="Path or identifier for the stored document file") # Included for potential use, maybe admin only
    file_hash: Optional[str] = Field(None, description="Optional hash of the file content")
    metadata_overrides: Optional[Dict[str, Any]] = Field(None, description="User-provided overrides for metadata fields")

    class Config:
        from_attributes = True 


class DocumentMetadataUpdate(BaseModel):
    document_date: Optional[date] = Field(None, description="User-set actual date on the report/prescription")
    source_name: Optional[str] = Field(None, description="User-set doctor, lab, hospital name")
    source_location_city: Optional[str] = Field(None, description="User-set city of the source")
    tags: Optional[List[str]] = Field(None, description="User-set list of tags (overwrites system tags)") # Note: User edits overwrite system tags conceptually
    user_added_tags: Optional[List[str]] = Field(None, description="User-set list of user-added tags")
    related_to_health_goal_or_episode: Optional[str] = Field(None, description="User-set link to a health goal or episode")
    # Note: We don't include file_metadata or processing_status here as they are updated differently.

# Deprecate or repurpose the old DocumentUpdate schema if only used for status/file_metadata?
# For clarity, let's keep it for now if it's used elsewhere, but new metadata updates
# should use DocumentMetadataUpdate.
class DocumentUpdate(BaseModel):
    # Keep this for updating non-override fields if needed
    processing_status: Optional[ProcessingStatus] = Field(None, description="Update the processing status")
    file_metadata: Optional[dict] = Field(None, description="Update optional file metadata like content type")
    # The fields below were previously here, but updates should now go via DocumentMetadataUpdate
    # document_date: Optional[date] = Field(None, description="Update actual date on the report/prescription")
    # source_name: Optional[str] = Field(None, description="Update doctor, lab, hospital name")
    # source_location_city: Optional[str] = Field(None, description="Update city of the source")
    # tags: Optional[List[str]] = Field(None, description="Update list of LLM-generated keywords/tags")
    # user_added_tags: Optional[List[str]] = Field(None, description="Update list of user-added tags")
    # related_to_health_goal_or_episode: Optional[str] = Field(None, description="Update link to a health goal or episode") 