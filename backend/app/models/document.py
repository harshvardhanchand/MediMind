import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from sqlalchemy.types import JSON

from app.db.session import Base

class DocumentType(str, enum.Enum):
    PRESCRIPTION = "prescription"
    LAB_RESULT = "lab_result"
    OTHER = "other"

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    REVIEW_REQUIRED = "review_required"
    COMPLETED = "completed"
    FAILED = "failed"

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
    document_type = Column(SQLAlchemyEnum(DocumentType), nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_status = Column(SQLAlchemyEnum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False)
    file_hash = Column(String, nullable=True, index=True) # Optional: To detect duplicates
    file_metadata = Column(JSON, nullable=True) # Optional: Store content type, size, etc. Renamed from 'metadata'

    # Relationships
    user = relationship("User")
    # extracted_data = relationship("ExtractedData", back_populates="document", uselist=False) # One-to-one

    def __repr__(self):
        return f"<Document(id={self.document_id}, filename='{self.original_filename}', user_id='{self.user_id}')>" 