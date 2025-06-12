"""
Medical Analysis API Endpoints
Endpoints for triggering comprehensive medical correlation analysis
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.db.session import get_db
from app.core.auth import get_current_user, User
from app.services.medical_ai_service import MedicalAIService
from app.services.notification_service import NotificationService
from app.models.medication import Medication
from app.models.health_reading import HealthReading
from app.models.symptom import Symptom
from app.models.health_condition import HealthCondition
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

# Request models
class SymptomAnalysisRequest(BaseModel):
    symptom: str
    severity: Optional[str] = "medium"
    description: Optional[str] = None
    reported_date: Optional[datetime] = None

class MedicationAnalysisRequest(BaseModel):
    medication_id: str
    analysis_type: str = "new_medication"  # new_medication, medication_change, etc.

class LabResultAnalysisRequest(BaseModel):
    test_name: str
    value: float
    unit: str
    date: Optional[datetime] = None
    reference_range: Optional[str] = None

class ComprehensiveAnalysisRequest(BaseModel):
    trigger_type: str  # symptom_reported, medication_added, lab_result, etc.
    event_data: Dict[str, Any]
    force_llm: Optional[bool] = False  # Force LLM analysis even if correlations exist

# Response models
class AnalysisResponse(BaseModel):
    analysis_id: str
    correlations_found: int
    notifications_created: int
    confidence: float
    summary: str
    processing_time_ms: int

@router.post("/analyze-symptom", response_model=AnalysisResponse)
async def analyze_symptom(
    request: SymptomAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a newly reported symptom for correlations with medications, lab results, and patterns
    """
    try:
        logger.info(f"Analyzing symptom '{request.symptom}' for user {current_user.user_id}")
        
        # Create the event data
        event_data = {
            "symptom": request.symptom,
            "severity": request.severity,
            "description": request.description,
            "reported_date": (request.reported_date or datetime.now()).isoformat()
        }
        
        # Initialize services
        ai_service = MedicalAIService(db)
        
        # Run comprehensive analysis
        start_time = datetime.now()
        notifications = await ai_service.analyze_medical_event(
            user_id=str(current_user.user_id),
            trigger_type="symptom_reported",
            event_data=event_data
        )
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Create notifications in background
        if notifications:
            notification_service = NotificationService(db)
            background_tasks.add_task(
                create_notifications_background,
                notification_service,
                notifications
            )
        
        # Generate response
        summary = f"Analyzed symptom '{request.symptom}' and found {len(notifications)} potential correlations."
        
        return AnalysisResponse(
            analysis_id=f"symptom_{current_user.user_id}_{int(datetime.now().timestamp())}",
            correlations_found=len(notifications),
            notifications_created=len(notifications),
            confidence=0.8,  # TODO: Calculate from actual analysis
            summary=summary,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Symptom analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis failed")

@router.post("/analyze-medication", response_model=AnalysisResponse)
async def analyze_medication(
    request: MedicationAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a medication addition/change for drug interactions, side effects, and monitoring needs
    """
    try:
        logger.info(f"Analyzing medication {request.medication_id} for user {current_user.user_id}")
        
        # Get medication from database
        medication = db.query(Medication).filter(
            Medication.id == request.medication_id,
            Medication.user_id == current_user.user_id
        ).first()
        
        if not medication:
            raise HTTPException(status_code=404, detail="Medication not found")
        
        # Create the event data
        event_data = {
            "medication_id": str(medication.id),
            "name": medication.name,
            "dosage": medication.dosage,
            "frequency": medication.frequency,
            "start_date": medication.start_date.isoformat() if medication.start_date else None,
            "reason": medication.reason,
            "doctor": medication.doctor
        }
        
        # Get AI service and run analysis
        ai_service = MedicalAIService(db)
        start_time = datetime.now()
        notifications = await ai_service.analyze_medical_event(
            user_id=str(current_user.user_id),
            trigger_type="medication_added",
            event_data=event_data
        )
        analysis_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Medication analysis completed in {analysis_time:.2f}s, created {len(notifications)} notifications")
        
        return AnalysisResponse(
            analysis_id=f"medication_{current_user.user_id}_{int(datetime.now().timestamp())}",
            correlations_found=len(notifications),
            notifications_created=len(notifications),
            analysis_time_seconds=analysis_time,
            summary=f"Analyzed medication '{medication.name}' and found {len(notifications)} potential issues or recommendations"
        )
        
    except Exception as e:
        logger.error(f"Medication analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis failed")

@router.post("/analyze-lab-result", response_model=AnalysisResponse)
async def analyze_lab_result(
    request: LabResultAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a lab result for correlations with symptoms and medication effects
    """
    try:
        logger.info(f"Analyzing lab result '{request.test_name}' for user {current_user.user_id}")
        
        # Create the event data
        event_data = {
            "lab_test": request.test_name,
            "value": request.value,
            "unit": request.unit,
            "date": (request.date or datetime.now()).isoformat(),
            "reference_range": request.reference_range
        }
        
        # Initialize services
        ai_service = MedicalAIService(db)
        
        # Run comprehensive analysis
        start_time = datetime.now()
        notifications = await ai_service.analyze_medical_event(
            user_id=str(current_user.user_id),
            trigger_type="lab_result",
            event_data=event_data
        )
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Create notifications in background
        if notifications:
            notification_service = NotificationService(db)
            background_tasks.add_task(
                create_notifications_background,
                notification_service,
                notifications
            )
        
        # Generate response
        summary = f"Analyzed lab result '{request.test_name}' ({request.value} {request.unit}) and found {len(notifications)} potential correlations."
        
        return AnalysisResponse(
            analysis_id=f"lab_{current_user.user_id}_{int(datetime.now().timestamp())}",
            correlations_found=len(notifications),
            notifications_created=len(notifications),
            confidence=0.8,  # TODO: Calculate from actual analysis
            summary=summary,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Lab result analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis failed")

@router.post("/comprehensive-analysis", response_model=AnalysisResponse)
async def comprehensive_analysis(
    request: ComprehensiveAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run comprehensive multi-correlation analysis for any medical event
    """
    try:
        logger.info(f"Running comprehensive analysis for trigger '{request.trigger_type}' for user {current_user.user_id}")
        
        # Initialize services
        ai_service = MedicalAIService(db)
        
        # Run comprehensive analysis
        start_time = datetime.now()
        notifications = await ai_service.analyze_medical_event(
            user_id=str(current_user.user_id),
            trigger_type=request.trigger_type,
            event_data=request.event_data
        )
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Create notifications in background
        if notifications:
            notification_service = NotificationService(db)
            background_tasks.add_task(
                create_notifications_background,
                notification_service,
                notifications
            )
        
        # Generate response
        summary = f"Comprehensive analysis for '{request.trigger_type}' found {len(notifications)} correlations."
        
        return AnalysisResponse(
            analysis_id=f"comprehensive_{current_user.user_id}_{int(datetime.now().timestamp())}",
            correlations_found=len(notifications),
            notifications_created=len(notifications),
            confidence=0.8,  # TODO: Calculate from actual analysis
            summary=summary,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis failed")

@router.get("/user-medical-profile")
async def get_user_medical_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's current medical profile for analysis
    """
    try:
        ai_service = MedicalAIService(db)
        
        # Build medical profile (this will be used internally for analysis)
        medical_profile = await ai_service._build_medical_profile(str(current_user.user_id), {})
        
        if not medical_profile:
            return {
                "user_id": str(current_user.user_id),
                "medications": [],
                "recent_symptoms": [],
                "lab_results": [],
                "health_conditions": [],
                "profile_completeness": 0.0
            }
        
        # Calculate profile completeness
        completeness = 0.0
        total_categories = 4
        
        if medical_profile.get("medications"):
            completeness += 0.25
        if medical_profile.get("recent_symptoms"):
            completeness += 0.25
        if medical_profile.get("lab_results"):
            completeness += 0.25
        if medical_profile.get("health_conditions"):
            completeness += 0.25
        
        medical_profile["profile_completeness"] = completeness
        return medical_profile
        
    except Exception as e:
        logger.error(f"Failed to get medical profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve medical profile")

@router.post("/trigger-analysis-for-all-data")
async def trigger_analysis_for_all_data(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger comprehensive analysis for all user's medical data (useful for testing or manual review)
    """
    try:
        logger.info(f"Triggering comprehensive analysis for all data for user {current_user.user_id}")
        
        # Get all user's medical data
        medications = db.query(Medication).filter(Medication.user_id == current_user.user_id).all()
        symptoms = db.query(Symptom).filter(Symptom.user_id == current_user.user_id).all()
        lab_results = db.query(HealthReading).filter(HealthReading.user_id == current_user.user_id).all()
        conditions = db.query(HealthCondition).filter(HealthCondition.user_id == current_user.user_id).all()
        
        # Create comprehensive event data
        event_data = {
            "analysis_type": "comprehensive_review",
            "medication_count": len(medications),
            "symptom_count": len(symptoms),
            "lab_result_count": len(lab_results),
            "condition_count": len(conditions)
        }
        
        # Initialize services
        ai_service = MedicalAIService(db)
        
        # Run comprehensive analysis
        start_time = datetime.now()
        notifications = await ai_service.analyze_medical_event(
            user_id=str(current_user.user_id),
            trigger_type="comprehensive_review",
            event_data=event_data
        )
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Create notifications in background
        if notifications:
            notification_service = NotificationService(db)
            background_tasks.add_task(
                create_notifications_background,
                notification_service,
                notifications
            )
        
        return {
            "message": "Comprehensive analysis triggered successfully",
            "correlations_found": len(notifications),
            "processing_time_ms": processing_time,
            "data_analyzed": {
                "medications": len(medications),
                "symptoms": len(symptoms),
                "lab_results": len(lab_results),
                "conditions": len(conditions)
            }
        }
        
    except Exception as e:
        logger.error(f"Comprehensive data analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis failed")

# Background task function
async def create_notifications_background(
    notification_service: NotificationService,
    notifications: List[Dict[str, Any]]
):
    """
    Create notifications in the background
    """
    try:
        for notification_data in notifications:
            await notification_service.create_notification(notification_data)
        logger.info(f"Created {len(notifications)} notifications in background")
    except Exception as e:
        logger.error(f"Background notification creation failed: {str(e)}") 