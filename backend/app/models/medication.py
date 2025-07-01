import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLAlchemyEnum, Date, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from sqlalchemy.types import JSON

from app.db.session import Base

class MedicationFrequency(str, enum.Enum):
    ONCE_DAILY = "once_daily"
    TWICE_DAILY = "twice_daily"
    THREE_TIMES_DAILY = "three_times_daily"
    FOUR_TIMES_DAILY = "four_times_daily"
    EVERY_OTHER_DAY = "every_other_day"
    ONCE_WEEKLY = "once_weekly"
    TWICE_WEEKLY = "twice_weekly"
    ONCE_MONTHLY = "once_monthly"
    AS_NEEDED = "as_needed"
    OTHER = "other"

class MedicationStatus(str, enum.Enum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"

def enum_values(enum_cls):
    """Helper function to get enum values for SQLAlchemy"""
    return [e.value for e in enum_cls]

class Medication(Base):
    """
    SQLAlchemy model for the medications table.
    
    Represents a medication being taken by a user.
    """
    __tablename__ = "medications"
    
    medication_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    dosage = Column(String, nullable=True)  
    frequency = Column(
        SQLAlchemyEnum(
            MedicationFrequency,
            values_callable=enum_values,   
            name="medicationfrequency",    
            native_enum=True,              
            create_type=False              
        ),
        nullable=False
    )
    frequency_details = Column(String, nullable=True) 
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    time_of_day = Column(JSON, nullable=True)  
    with_food = Column(Boolean, nullable=True)
    reason = Column(String, nullable=True)
    prescribing_doctor = Column(String, nullable=True)
    pharmacy = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(
        SQLAlchemyEnum(
            MedicationStatus,
            values_callable=enum_values,   
            name="medicationstatus",       
            native_enum=True,             
            create_type=False              
        ),
        default=MedicationStatus.ACTIVE,
        nullable=False
    )
    
    
    related_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id"), nullable=True)
    tags = Column(JSON, nullable=True)  
    
    
    created_at = Column(DateTime, default= datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default= datetime.now(timezone.utc), onupdate= datetime.now(timezone.utc), nullable=False)
    
   
    user = relationship("User")
    related_document = relationship("Document")
    notifications = relationship("Notification", back_populates="related_medication")
    ai_analysis_logs = relationship("AIAnalysisLog", back_populates="related_medication")
    
    def __repr__(self):
        return f"<Medication(id={self.medication_id}, name='{self.name}', user_id='{self.user_id}')>" 