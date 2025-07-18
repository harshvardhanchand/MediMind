import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SQLAlchemyEnum, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base

class ConditionStatus(str, enum.Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"  
    CHRONIC = "chronic"
    MANAGED = "managed"
    SUSPECTED = "suspected"

class ConditionSeverity(str, enum.Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"

def enum_values(enum_cls):
    """Helper function to get enum values for SQLAlchemy"""
    return [e.value for e in enum_cls]

class HealthCondition(Base):
    """
    SQLAlchemy model for the health_conditions table.
    
    Represents diagnosed health conditions for users.
    """
    __tablename__ = "health_conditions"
    
    condition_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    condition_name = Column(String, nullable=False, index=True)  # e.g., "Type 2 Diabetes", "Hypertension"
    diagnosed_date = Column(Date, nullable=True)
    severity = Column(
        SQLAlchemyEnum(
            ConditionSeverity,
            values_callable=enum_values,
            name="conditionseverity",
            native_enum=True,
            create_type=False
        ),
        nullable=True
    )
    status = Column(
        SQLAlchemyEnum(
            ConditionStatus,
            values_callable=enum_values,
            name="conditionstatus",
            native_enum=True,
            create_type=False
        ),
        default=ConditionStatus.ACTIVE,
        nullable=False
    )
    diagnosing_doctor = Column(String, nullable=True)
    icd_code = Column(String, nullable=True)  # ICD-10 code if available
    notes = Column(Text, nullable=True)
    
    # Optional links to source data
    related_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id"), nullable=True)
    related_extracted_data_id = Column(UUID(as_uuid=True), ForeignKey("extracted_data.extracted_data_id"), nullable=True)
    
    # Tracking fields
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User")
    related_document = relationship("Document")
    related_extracted_data = relationship("ExtractedData")
    
    def __repr__(self):
        return f"<HealthCondition(id={self.condition_id}, condition='{self.condition_name}', user_id='{self.user_id}')>" 