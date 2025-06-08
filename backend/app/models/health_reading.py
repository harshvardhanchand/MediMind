import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Text, Enum as SQLAlchemyEnum, Integer, Float
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship, Mapped

from app.db.session import Base # Assuming Base is in app.db.session

class HealthReadingType(str, enum.Enum):
    BLOOD_PRESSURE = "BLOOD_PRESSURE"
    GLUCOSE = "GLUCOSE"
    HEART_RATE = "HEART_RATE"
    WEIGHT = "WEIGHT"
    HEIGHT = "HEIGHT"
    BMI = "BMI"
    SPO2 = "SPO2" # Blood oxygen saturation
    TEMPERATURE = "TEMPERATURE"
    RESPIRATORY_RATE = "RESPIRATORY_RATE"
    PAIN_LEVEL = "PAIN_LEVEL" # e.g., scale of 1-10
    STEPS = "STEPS"
    SLEEP = "SLEEP" # Could be duration in minutes or more complex object
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
            values_callable=enum_values,   # Use .value list instead of .name
            name="healthreadingtype",      # Must match existing PG type
            native_enum=True,              # Keep it a real PG enum
            create_type=False              # Don't try to recreate
        ),
        nullable=False,
        index=True
    )
    
    # For simple numeric values like weight, height, glucose, heart_rate, spo2, temperature, respiratory_rate, pain_level, steps
    numeric_value = Column(Numeric(precision=10, scale=2), nullable=True)
    unit = Column(String, nullable=True) # e.g., "kg", "lbs", "mg/dL", "bpm", "%", "C", "F", "breaths/min"

    # For blood pressure (which has two values)
    systolic_value = Column(Integer, nullable=True)
    diastolic_value = Column(Integer, nullable=True)
    # unit for blood pressure is typically mmHg, can be stored in 'unit' or implicitly known

    # For text-based values or when a more complex structure is needed via JSON
    text_value = Column(Text, nullable=True)
    json_value = Column(JSONB, nullable=True) # For complex values like sleep data { "duration_minutes": 480, "quality": "good" }

    reading_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    source = Column(String, nullable=True) # e.g., "manual_entry", "apple_health", "wearable_device_xyz"
    related_document_id = Column(PG_UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User")
    related_document = relationship("Document")
    notifications = relationship("Notification", back_populates="related_health_reading")
    ai_analysis_logs = relationship("AIAnalysisLog", back_populates="related_health_reading")

    def __repr__(self):
        return f"<HealthReading(id={self.health_reading_id}, type='{self.reading_type}', user_id='{self.user_id}')>"

# from sqlalchemy import Integer # Removed redundant import 