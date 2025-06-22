import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLAlchemyEnum, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from sqlalchemy.types import JSON

from app.db.session import Base

class DocumentType(str, enum.Enum):
    PRESCRIPTION = "prescription"
    LAB_RESULT = "lab_result"
    IMAGING_REPORT = "imaging_report"
    CONSULTATION_NOTE = "consultation_note"
    DISCHARGE_SUMMARY = "discharge_summary"
    OTHER = "other"

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"  
    OCR_COMPLETED = "ocr_completed"
    EXTRACTION_COMPLETED = "extraction_completed"
    REVIEW_REQUIRED = "review_required"
    COMPLETED = "completed"
    FAILED = "failed"

def enum_values(enum_cls):
    """Helper function to get enum values for SQLAlchemy"""
    return [e.value for e in enum_cls]

class Document(Base):
    """
    SQLAlchemy model for the documents table.
    
    Represents an uploaded medical document belonging to a user.
    """
    __tablename__ = "documents"
    
    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    original_filename = Column(String, nullable=False)
    storage_path = Column(String, unique=True, nullable=False) # e.g., GCS path or identifier
    document_type = Column(
        SQLAlchemyEnum(
            DocumentType,
            values_callable=enum_values,   # Use .value list instead of .name
            name="documenttype",           # Must match existing PG type
            native_enum=True,              # Keep it a real PG enum
            create_type=False              # Don't try to recreate
        ),
        nullable=False
    )
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_status = Column(
        SQLAlchemyEnum(
            ProcessingStatus,
            values_callable=enum_values,   # Use .value list for ProcessingStatus too
            name="processingstatus",
            native_enum=True,
            create_type=False
        ),
        default=ProcessingStatus.PENDING,
        nullable=False
    )
    file_hash = Column(String, nullable=True, index=True) # Optional: To detect duplicates
    file_metadata = Column(JSON, nullable=True) # Optional: Store content type, size, etc. Renamed from 'metadata'

    # New metadata fields for enhanced filtering
    document_date = Column(Date, nullable=True) # Actual date on the report/prescription
    source_name = Column(String, nullable=True) # Doctor, lab, hospital name
    source_location_city = Column(String, nullable=True) # City of the source
    tags = Column(JSON, nullable=True) # List of LLM-generated keywords/tags
    user_added_tags = Column(JSON, nullable=True) # List of user-added tags
    related_to_health_goal_or_episode = Column(String, nullable=True) # Link to a health goal or episode

    # NEW field to store user overrides for specific metadata fields
    metadata_overrides = Column(JSON, nullable=True) 
    # Example: {"document_date": "YYYY-MM-DD", "source_name": "User Input Clinic", "tags": ["override_tag"]} 

    # Relationships
    user = relationship("User")
    extracted_data = relationship("ExtractedData", back_populates="document", uselist=False) # One-to-one
    notifications = relationship("Notification", back_populates="related_document")
    ai_analysis_logs = relationship("AIAnalysisLog", back_populates="related_document")

    def __repr__(self):
        return f"<Document(id={self.document_id}, filename='{self.original_filename}', user_id='{self.user_id}')>" 