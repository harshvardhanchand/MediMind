import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base

class SymptomSeverity(str, enum.Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"

def enum_values(enum_cls):
    """Helper function to get enum values for SQLAlchemy"""
    return [e.value for e in enum_cls]

class Symptom(Base):
    """
    SQLAlchemy model for the symptoms table.
    
    Represents symptoms reported by users.
    """
    __tablename__ = "symptoms"
    
    symptom_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    symptom = Column(String, nullable=False, index=True)  # e.g., "headache", "nausea", "fatigue"
    severity = Column(
        SQLAlchemyEnum(
            SymptomSeverity,
            values_callable=enum_values,
            name="symptomseverity",
            native_enum=True,
            create_type=False
        ),
        nullable=False
    )
    reported_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    duration = Column(String, nullable=True)  # e.g., "2 hours", "3 days"
    location = Column(String, nullable=True)  # e.g., "head", "chest", "abdomen"
    notes = Column(Text, nullable=True)
    
    # Optional links to triggers
    related_medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.medication_id"), nullable=True)
    related_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id"), nullable=True)
    
    # Tracking fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User")
    related_medication = relationship("Medication")
    related_document = relationship("Document")
    
    def __repr__(self):
        return f"<Symptom(id={self.symptom_id}, symptom='{self.symptom}', user_id='{self.user_id}')>" 