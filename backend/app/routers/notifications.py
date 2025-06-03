"""
Notification API Endpoints
Provides REST API for medical notifications and analysis
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from ..db.session import get_db
from ..services.notification_service import get_notification_service, get_medical_triggers
from ..core.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])
security = HTTPBearer()

# Pydantic models
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
    total_notifications: int
    unread_count: int
    high_priority_unread: int
    recent_notifications: int

class MedicalEventRequest(BaseModel):
    trigger_type: str
    event_data: Dict[str, Any]

class NotificationActionRequest(BaseModel):
    notification_id: str

# Notification endpoints
@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    include_read: bool = Query(True, description="Include read notifications"),
    include_dismissed: bool = Query(False, description="Include dismissed notifications"),
    limit: int = Query(50, le=100, description="Maximum number of notifications"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get notifications for the current user
    """
    try:
        notification_service = get_notification_service(db)
        
        notifications = notification_service.get_user_notifications(
            user_id=str(current_user.id),
            include_read=include_read,
            include_dismissed=include_dismissed,
            limit=limit
        )
        
        return notifications
        
    except Exception as e:
        logger.error(f"Failed to get notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notifications")

@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get notification statistics for the current user
    """
    try:
        notification_service = get_notification_service(db)
        
        stats = notification_service.get_notification_stats(str(current_user.id))
        
        return NotificationStats(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get notification stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notification statistics")

@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Mark a notification as read
    """
    try:
        notification_service = get_notification_service(db)
        
        success = notification_service.mark_notification_read(
            notification_id=notification_id,
            user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update notification")

@router.post("/{notification_id}/dismiss")
async def dismiss_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Dismiss a notification
    """
    try:
        notification_service = get_notification_service(db)
        
        success = notification_service.dismiss_notification(
            notification_id=notification_id,
            user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification dismissed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to dismiss notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update notification")

# Medical analysis trigger endpoints
@router.post("/trigger/medication")
async def trigger_medication_analysis(
    medication_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Trigger medical analysis for new medication
    """
    try:
        notification_service = get_notification_service(db)
        medical_triggers = get_medical_triggers(notification_service)
        
        # Run analysis in background
        background_tasks.add_task(
            medical_triggers.on_medication_added,
            str(current_user.id),
            medication_data
        )
        
        return {"message": "Medical analysis triggered for new medication"}
        
    except Exception as e:
        logger.error(f"Failed to trigger medication analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger medical analysis")

@router.post("/trigger/symptom")
async def trigger_symptom_analysis(
    symptom_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Trigger medical analysis for reported symptom
    """
    try:
        notification_service = get_notification_service(db)
        medical_triggers = get_medical_triggers(notification_service)
        
        # Run analysis in background
        background_tasks.add_task(
            medical_triggers.on_symptom_reported,
            str(current_user.id),
            symptom_data
        )
        
        return {"message": "Medical analysis triggered for symptom"}
        
    except Exception as e:
        logger.error(f"Failed to trigger symptom analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger medical analysis")

@router.post("/trigger/lab-result")
async def trigger_lab_analysis(
    lab_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Trigger medical analysis for lab result
    """
    try:
        notification_service = get_notification_service(db)
        medical_triggers = get_medical_triggers(notification_service)
        
        # Run analysis in background
        background_tasks.add_task(
            medical_triggers.on_lab_result_added,
            str(current_user.id),
            lab_data
        )
        
        return {"message": "Medical analysis triggered for lab result"}
        
    except Exception as e:
        logger.error(f"Failed to trigger lab analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger medical analysis")

@router.post("/trigger/health-reading")
async def trigger_health_reading_analysis(
    reading_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Trigger medical analysis for health reading
    """
    try:
        notification_service = get_notification_service(db)
        medical_triggers = get_medical_triggers(notification_service)
        
        # Run analysis in background
        background_tasks.add_task(
            medical_triggers.on_health_reading_added,
            str(current_user.id),
            reading_data
        )
        
        return {"message": "Medical analysis triggered for health reading"}
        
    except Exception as e:
        logger.error(f"Failed to trigger health reading analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger medical analysis")

# Manual analysis trigger
@router.post("/analyze")
async def trigger_manual_analysis(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Manually trigger comprehensive medical analysis
    """
    try:
        notification_service = get_notification_service(db)
        
        # Run comprehensive analysis in background
        background_tasks.add_task(
            notification_service.trigger_medical_analysis,
            str(current_user.id),
            "manual_analysis",
            {
                "type": "manual_analysis",
                "triggered_by": "user_request",
                "timestamp": None
            }
        )
        
        return {"message": "Comprehensive medical analysis triggered"}
        
    except Exception as e:
        logger.error(f"Failed to trigger manual analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger medical analysis")

# Admin endpoints (if needed)
@router.get("/admin/stats")
async def get_system_notification_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get system-wide notification statistics (admin only)
    """
    # Add admin check here if you have role-based access
    try:
        # Get system-wide stats
        result = db.execute("""
            SELECT 
                COUNT(*) as total_notifications,
                COUNT(DISTINCT user_id) as active_users,
                AVG(CASE WHEN is_read = false THEN 1 ELSE 0 END) as avg_unread_rate,
                COUNT(CASE WHEN severity = 'high' THEN 1 END) as high_severity_count
            FROM notifications 
            WHERE expires_at > NOW()
        """).fetchone()
        
        if result:
            return {
                "total_notifications": result[0],
                "active_users": result[1],
                "average_unread_rate": float(result[2]) if result[2] else 0.0,
                "high_severity_count": result[3]
            }
        
        return {}
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system statistics")

@router.post("/admin/cleanup")
async def cleanup_expired_notifications(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Clean up expired notifications (admin only)
    """
    # Add admin check here if you have role-based access
    try:
        notification_service = get_notification_service(db)
        
        # Run cleanup in background
        background_tasks.add_task(
            notification_service.cleanup_expired_notifications
        )
        
        return {"message": "Notification cleanup initiated"}
        
    except Exception as e:
        logger.error(f"Failed to trigger cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger cleanup") 