import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Text, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base # Assuming Base is in app.db.session

class HealthReadingType(str, enum.Enum):
    BLOOD_PRESSURE = "blood_pressure"
    GLUCOSE = "glucose"
    HEART_RATE = "heart_rate"
    WEIGHT = "weight"
    HEIGHT = "height"
    BMI = "bmi"
    SPO2 = "spo2" # Blood oxygen saturation
    TEMPERATURE = "temperature"
    RESPIRATORY_RATE = "respiratory_rate"
    PAIN_LEVEL = "pain_level" # e.g., scale of 1-10
    STEPS = "steps"
    SLEEP = "sleep" # Could be duration in minutes or more complex object
    OTHER = "other"

class HealthReading(Base):
    __tablename__ = "health_readings"

    health_reading_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    reading_type = Column(SQLAlchemyEnum(HealthReadingType), nullable=False, index=True)
    
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

    def __repr__(self):
        return f"<HealthReading(id={self.health_reading_id}, type='{self.reading_type}', user_id='{self.user_id}')>"

from sqlalchemy import Integer 