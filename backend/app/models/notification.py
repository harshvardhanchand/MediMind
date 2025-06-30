"""
Notification Models
SQLAlchemy models for the notification system
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..db.session import Base


class Notification(Base):
    """
    User notifications for medical events and recommendations
    """
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  
    severity = Column(String(20), nullable=False) 
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_metadata = Column(JSONB, nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    is_dismissed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)
    
    
    related_medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.medication_id", ondelete="SET NULL"), nullable=True)
    related_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="SET NULL"), nullable=True)
    related_health_reading_id = Column(UUID(as_uuid=True), ForeignKey("health_readings.health_reading_id", ondelete="SET NULL"), nullable=True)
    related_extracted_data_id = Column(UUID(as_uuid=True), ForeignKey("extracted_data.extracted_data_id", ondelete="SET NULL"), nullable=True)
    
    
    user = relationship("User", back_populates="notifications")
    related_medication = relationship("Medication", back_populates="notifications")
    related_document = relationship("Document", back_populates="notifications")
    related_health_reading = relationship("HealthReading", back_populates="notifications")
    related_extracted_data = relationship("ExtractedData", back_populates="notifications")


class MedicalSituation(Base):
    """
    Vector storage for medical situations to enable similarity matching
    """
    __tablename__ = "medical_situations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medical_context = Column(JSONB, nullable=False) 
    analysis_result = Column(JSONB, nullable=False)  
    confidence_score = Column(Float, nullable=False)
    similarity_threshold = Column(Float, nullable=False, default=0.85)
    usage_count = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    last_used_at = Column(DateTime, nullable=False, server_default=func.now())
    
    


class AIAnalysisLog(Base):
    """
    Logging table for AI analysis debugging and cost tracking
    """
    __tablename__ = "ai_analysis_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    trigger_type = Column(String(50), nullable=False)
    medical_profile_hash = Column(String(64), nullable=False)
    similarity_matches = Column(JSONB, nullable=True)
    llm_called = Column(Boolean, nullable=False)
    llm_cost = Column(Float, nullable=True)
    processing_time_ms = Column(Integer, nullable=False)
    analysis_result = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    
    related_medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.medication_id", ondelete="SET NULL"), nullable=True)
    related_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="SET NULL"), nullable=True)
    related_health_reading_id = Column(UUID(as_uuid=True), ForeignKey("health_readings.health_reading_id", ondelete="SET NULL"), nullable=True)
    related_extracted_data_id = Column(UUID(as_uuid=True), ForeignKey("extracted_data.extracted_data_id", ondelete="SET NULL"), nullable=True)
    
    
    user = relationship("User", back_populates="ai_analysis_logs")
    related_medication = relationship("Medication", back_populates="ai_analysis_logs")
    related_document = relationship("Document", back_populates="ai_analysis_logs")
    related_health_reading = relationship("HealthReading", back_populates="ai_analysis_logs")
    related_extracted_data = relationship("ExtractedData", back_populates="ai_analysis_logs")
    
    