import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Enum as SQLAlchemyEnum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base

class ReviewStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    REVIEWED_CORRECTED = "reviewed_corrected"
    REVIEWED_APPROVED = "reviewed_approved"

class ExtractedData(Base):
    """
    SQLAlchemy model for the extracted_data table.
    
    Stores structured data extracted from a document.
    Uses JSONB for flexibility in storing different data structures 
    (e.g., prescriptions vs. lab results).
    """
    __tablename__ = "extracted_data"
    
    extracted_data_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id"), nullable=False, unique=True, index=True)
    # Using JSONB to store flexible structured data
    content = Column(JSONB, nullable=False)
    # Optional: Store the raw text extracted by OCR before structuring
    raw_text = Column(Text, nullable=True)
    extraction_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    review_status = Column(SQLAlchemyEnum(ReviewStatus), default=ReviewStatus.PENDING_REVIEW, nullable=False)
    reviewed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    review_timestamp = Column(DateTime, nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="extracted_data")
    reviewed_by_user = relationship("User")
    notifications = relationship("Notification", back_populates="related_extracted_data")
    ai_analysis_logs = relationship("AIAnalysisLog", back_populates="related_extracted_data")

    def __repr__(self):
        return f"<ExtractedData(id={self.extracted_data_id}, document_id='{self.document_id}', status='{self.review_status}')>" 