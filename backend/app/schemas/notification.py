"""
Notification-related Pydantic schemas and request/response models
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class RelatedEntityInfo(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    filename: Optional[str] = None
    test_name: Optional[str] = None


class RelatedEntities(BaseModel):
    medication: Optional[RelatedEntityInfo] = None
    document: Optional[RelatedEntityInfo] = None
    health_reading: Optional[RelatedEntityInfo] = None
    extracted_data: Optional[RelatedEntityInfo] = None


class NotificationResponse(BaseModel):
    id: str
    type: str
    severity: str
    title: str
    message: str
    metadata: Dict[str, Any]
    is_read: bool
    is_dismissed: bool
    created_at: str
    expires_at: Optional[str]
    related_entities: RelatedEntities


class NotificationStats(BaseModel):
    total_count: int
    unread_count: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]


class MedicalEventRequest(BaseModel):
    trigger_type: str
    event_data: Dict[str, Any]


class NotificationActionRequest(BaseModel):
    notification_id: str


# Validated request models for trigger endpoints
class MedicationRequest(BaseModel):
    """Validated request model for medication analysis trigger."""
    medication_id: str
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    prescribed_by: Optional[str] = None
    notes: Optional[str] = None


class SymptomRequest(BaseModel):
    """Validated request model for symptom analysis trigger."""
    symptom_name: str
    severity: Optional[int] = None  # 1-10 scale
    description: Optional[str] = None
    onset_date: Optional[str] = None
    duration: Optional[str] = None
    triggers: Optional[List[str]] = None
    associated_symptoms: Optional[List[str]] = None


class LabResultRequest(BaseModel):
    """Validated request model for lab result analysis trigger."""
    test_name: str
    test_date: str
    results: Dict[str, Any]  # Flexible for different lab result formats
    reference_ranges: Optional[Dict[str, str]] = None
    ordered_by: Optional[str] = None
    lab_facility: Optional[str] = None
    notes: Optional[str] = None


class HealthReadingRequest(BaseModel):
    """Validated request model for health reading analysis trigger."""
    reading_type: str  
    value: str  
    unit: str
    timestamp: str
    device_name: Optional[str] = None
    notes: Optional[str] = None 