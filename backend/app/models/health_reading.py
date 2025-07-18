import enum
import uuid
from datetime import datetime,timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Text, Enum as SQLAlchemyEnum, Integer, Float
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship, Mapped

from app.db.session import Base 

class HealthReadingType(str, enum.Enum):
    BLOOD_PRESSURE = "BLOOD_PRESSURE"
    GLUCOSE = "GLUCOSE"
    HEART_RATE = "HEART_RATE"
    WEIGHT = "WEIGHT"
    HEIGHT = "HEIGHT"
    BMI = "BMI"
    SPO2 = "SPO2" 
    TEMPERATURE = "TEMPERATURE"
    RESPIRATORY_RATE = "RESPIRATORY_RATE"
    PAIN_LEVEL = "PAIN_LEVEL" 
    STEPS = "STEPS"
    SLEEP = "SLEEP" 
    OTHER = "OTHER"

def enum_values(enum_cls):
    """Helper function to get enum values for SQLAlchemy"""
    return [e.value for e in enum_cls]

class HealthReading(Base):
    __tablename__ = "health_readings"

    health_reading_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    reading_type = Column(
        SQLAlchemyEnum(
            HealthReadingType,
            values_callable=enum_values,   
            name="healthreadingtype",      
            native_enum=True,              
            create_type=False              
        ),
        nullable=False,
        index=True
    )
    
    
    numeric_value = Column(Numeric(precision=10, scale=2), nullable=True)
    unit = Column(String, nullable=True) 

   
    systolic_value = Column(Integer, nullable=True)
    diastolic_value = Column(Integer, nullable=True)
    text_value = Column(Text, nullable=True)
    json_value = Column(JSONB, nullable=True)

    reading_date = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    related_document_id = Column(PG_UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    user = relationship("User")
    related_document = relationship("Document")
    notifications = relationship("Notification", back_populates="related_health_reading")
    ai_analysis_logs = relationship("AIAnalysisLog", back_populates="related_health_reading")

    def __repr__(self):
        return f"<HealthReading(id={self.health_reading_id}, type='{self.reading_type}', user_id='{self.user_id}')>"

