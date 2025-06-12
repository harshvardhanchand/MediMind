"""
Symptom Pydantic Schemas
Request and response models for symptom API endpoints
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator

from app.models.symptom import SymptomSeverity


class SymptomBase(BaseModel):
    """Base symptom schema with common fields"""
    symptom: str = Field(..., min_length=1, max_length=200, description="Symptom name or description")
    severity: SymptomSeverity = Field(..., description="Severity level of the symptom")
    duration: Optional[str] = Field(None, max_length=100, description="Duration of the symptom (e.g., '2 hours', '3 days')")
    location: Optional[str] = Field(None, max_length=100, description="Location of the symptom (e.g., 'head', 'chest')")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes about the symptom")
    reported_date: Optional[datetime] = Field(None, description="When the symptom was reported")
    related_medication_id: Optional[UUID] = Field(None, description="ID of related medication if applicable")
    related_document_id: Optional[UUID] = Field(None, description="ID of related document if applicable")

    @validator('symptom')
    def validate_symptom(cls, v):
        if not v or not v.strip():
            raise ValueError('Symptom description cannot be empty')
        return v.strip()

    @validator('duration')
    def validate_duration(cls, v):
        if v and not v.strip():
            return None
        return v.strip() if v else None

    @validator('location')
    def validate_location(cls, v):
        if v and not v.strip():
            return None
        return v.strip() if v else None


class SymptomCreate(SymptomBase):
    """Schema for creating a new symptom"""
    pass


class SymptomUpdate(BaseModel):
    """Schema for updating an existing symptom"""
    symptom: Optional[str] = Field(None, min_length=1, max_length=200)
    severity: Optional[SymptomSeverity] = None
    duration: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)
    reported_date: Optional[datetime] = None
    related_medication_id: Optional[UUID] = None
    related_document_id: Optional[UUID] = None

    @validator('symptom')
    def validate_symptom(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Symptom description cannot be empty')
        return v.strip() if v else None


class SymptomResponse(SymptomBase):
    """Schema for symptom response"""
    symptom_id: UUID = Field(..., description="Unique identifier for the symptom")
    user_id: UUID = Field(..., description="ID of the user who reported the symptom")
    created_at: datetime = Field(..., description="When the symptom record was created")
    updated_at: datetime = Field(..., description="When the symptom record was last updated")

    class Config:
        from_attributes = True


class SymptomListResponse(BaseModel):
    """Schema for paginated symptom list response"""
    symptoms: List[SymptomResponse] = Field(..., description="List of symptoms")
    total: int = Field(..., description="Total number of symptoms")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items returned")


class SymptomStatsResponse(BaseModel):
    """Schema for symptom statistics response"""
    total_symptoms: int = Field(..., description="Total number of symptoms reported")
    recent_symptoms: int = Field(..., description="Number of symptoms in the last 30 days")
    severity_breakdown: dict = Field(..., description="Breakdown of symptoms by severity level")


class SymptomSearchRequest(BaseModel):
    """Schema for symptom search request"""
    query: str = Field(..., min_length=1, description="Search query for symptom name or notes")
    severity: Optional[SymptomSeverity] = Field(None, description="Filter by severity level")
    start_date: Optional[datetime] = Field(None, description="Filter symptoms from this date")
    end_date: Optional[datetime] = Field(None, description="Filter symptoms until this date")
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(50, ge=1, le=100, description="Maximum number of items to return")


class SymptomAnalysisRequest(BaseModel):
    """Schema for requesting symptom analysis"""
    symptom_id: UUID = Field(..., description="ID of the symptom to analyze")
    include_medications: bool = Field(True, description="Include medication correlations in analysis")
    include_patterns: bool = Field(True, description="Include pattern analysis")


class SymptomPatternResponse(BaseModel):
    """Schema for symptom pattern analysis response"""
    symptom_name: str = Field(..., description="Name of the symptom")
    frequency: int = Field(..., description="Number of times this symptom was reported")
    average_severity: float = Field(..., description="Average severity level")
    most_common_location: Optional[str] = Field(None, description="Most common location for this symptom")
    trend: str = Field(..., description="Trend analysis (increasing, decreasing, stable)")
    last_reported: datetime = Field(..., description="When this symptom was last reported")


class SymptomCorrelationResponse(BaseModel):
    """Schema for symptom correlation analysis response"""
    symptom_id: UUID = Field(..., description="ID of the analyzed symptom")
    medication_correlations: List[dict] = Field(default_factory=list, description="Potential medication correlations")
    pattern_analysis: Optional[SymptomPatternResponse] = Field(None, description="Pattern analysis for this symptom")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations based on analysis")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the analysis")


# Bulk operations schemas
class SymptomBulkCreateRequest(BaseModel):
    """Schema for creating multiple symptoms at once"""
    symptoms: List[SymptomCreate] = Field(..., min_items=1, max_items=50, description="List of symptoms to create")


class SymptomBulkCreateResponse(BaseModel):
    """Schema for bulk symptom creation response"""
    created_symptoms: List[SymptomResponse] = Field(..., description="Successfully created symptoms")
    failed_symptoms: List[dict] = Field(default_factory=list, description="Failed symptom creations with error details")
    total_created: int = Field(..., description="Number of successfully created symptoms")
    total_failed: int = Field(..., description="Number of failed symptom creations") 