"""
Notification API Endpoints
Provides REST API for medical notifications and analysis
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from app.db.session import get_db, SessionLocal
from app.services.notification_service import get_notification_service, get_medical_triggers
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    NotificationStats,
    MedicationRequest,
    SymptomRequest,
    LabResultRequest,
    HealthReadingRequest
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["notifications"])
security = HTTPBearer()


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Temporary admin check. In production, replace with proper role-based access control.
    For now, we'll use a simple email whitelist or app_metadata check.
    """
    
    if current_user.app_metadata and current_user.app_metadata.get("role") == "admin":
        return current_user
    
    
    admin_emails = [
       "admin@example.com"  # Configure with your admin email
    ]
    
    if current_user.email in admin_emails:
        return current_user
        
    # If neither check passes, deny access
    logger.warning(f"Non-admin user {current_user.email} attempted to access admin endpoint")
    raise HTTPException(
        status_code=403, 
        detail="Admin access required. Contact system administrator."
    )

# Background task wrappers with proper DB session management
def run_medication_analysis_task(user_id: str, medication_data: Dict[str, Any]):
    """Background task wrapper for medication analysis with its own DB session."""
    db = SessionLocal()
    try:
        notification_service = get_notification_service(db)
        medical_triggers = get_medical_triggers(notification_service)
        medical_triggers.on_medication_added(user_id, medication_data)
        logger.info(f"Completed medication analysis for user {user_id}")
    except Exception as e:
        logger.error(f"Medication analysis failed for user {user_id}: {str(e)}", exc_info=True)
    finally:
        db.close()

def run_symptom_analysis_task(user_id: str, symptom_data: Dict[str, Any]):
    """Background task wrapper for symptom analysis with its own DB session."""
    db = SessionLocal()
    try:
        notification_service = get_notification_service(db)
        medical_triggers = get_medical_triggers(notification_service)
        medical_triggers.on_symptom_reported(user_id, symptom_data)
        logger.info(f"Completed symptom analysis for user {user_id}")
    except Exception as e:
        logger.error(f"Symptom analysis failed for user {user_id}: {str(e)}", exc_info=True)
    finally:
        db.close()

def run_lab_analysis_task(user_id: str, lab_data: Dict[str, Any]):
    """Background task wrapper for lab analysis with its own DB session."""
    db = SessionLocal()
    try:
        notification_service = get_notification_service(db)
        medical_triggers = get_medical_triggers(notification_service)
        medical_triggers.on_lab_result_added(user_id, lab_data)
        logger.info(f"Completed lab analysis for user {user_id}")
    except Exception as e:
        logger.error(f"Lab analysis failed for user {user_id}: {str(e)}", exc_info=True)
    finally:
        db.close()

def run_health_reading_analysis_task(user_id: str, reading_data: Dict[str, Any]):
    """Background task wrapper for health reading analysis with its own DB session."""
    db = SessionLocal()
    try:
        notification_service = get_notification_service(db)
        medical_triggers = get_medical_triggers(notification_service)
        medical_triggers.on_health_reading_added(user_id, reading_data)
        logger.info(f"Completed health reading analysis for user {user_id}")
    except Exception as e:
        logger.error(f"Health reading analysis failed for user {user_id}: {str(e)}", exc_info=True)
    finally:
        db.close()

def run_comprehensive_analysis_task(user_id: str):
    """Background task wrapper for comprehensive analysis with its own DB session."""
    db = SessionLocal()
    try:
        notification_service = get_notification_service(db)
        medical_triggers = get_medical_triggers(notification_service)
        medical_triggers.run_comprehensive_analysis(user_id)
        logger.info(f"Completed comprehensive analysis for user {user_id}")
    except Exception as e:
        logger.error(f"Comprehensive analysis failed for user {user_id}: {str(e)}", exc_info=True)
    finally:
        db.close()

def run_cleanup_task():
    """Background task wrapper for notification cleanup with its own DB session."""
    db = SessionLocal()
    try:
        notification_service = get_notification_service(db)
        cleanup_count = notification_service.cleanup_expired_notifications()
        logger.info(f"Cleaned up {cleanup_count} expired notifications")
    except Exception as e:
        logger.error(f"Notification cleanup failed: {str(e)}", exc_info=True)
    finally:
        db.close()

# Notification endpoints
@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    include_read: bool = Query(True, description="Include read notifications"),
    include_dismissed: bool = Query(False, description="Include dismissed notifications"),
    limit: int = Query(50, le=100, description="Maximum number of notifications"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get notifications for the current user
    """
    try:
        logger.info(f"🔍 get_notifications called - user_id: {current_user.user_id}")
        notification_service = get_notification_service(db)
        
        logger.info(f"🔍 About to call get_user_notifications with user_id: {str(current_user.user_id)}")
        notifications = notification_service.get_user_notifications(
            user_id=str(current_user.user_id),
            include_read=include_read,
            include_dismissed=include_dismissed,
            limit=limit
        )
        
        logger.info(f"🔍 get_user_notifications returned {len(notifications)} notifications")
        return notifications
        
    except Exception as e:
        logger.error(f"Failed to get notifications: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve notifications")

@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get notification statistics for the current user
    """
    try:
        notification_service = get_notification_service(db)
        
        stats = notification_service.get_notification_stats(str(current_user.user_id))
        
        return NotificationStats(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get notification stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notification statistics")

@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a notification as read
    """
    try:
        notification_service = get_notification_service(db)
        
        success = notification_service.mark_notification_read(
            notification_id=notification_id,
            user_id=str(current_user.user_id)
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
    current_user: User = Depends(get_current_user)
):
    """
    Dismiss a notification
    """
    try:
        notification_service = get_notification_service(db)
        
        success = notification_service.dismiss_notification(
            notification_id=notification_id,
            user_id=str(current_user.user_id)
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
    medication_data: MedicationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Trigger medical analysis for new medication
    """
    try:
        background_tasks.add_task(
            run_medication_analysis_task,
            str(current_user.user_id),
            medication_data.dict()
        )
        
        return {"message": "Medical analysis triggered for new medication"}
        
    except Exception as e:
        logger.error(f"Failed to trigger medication analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger medical analysis")

@router.post("/trigger/symptom")
async def trigger_symptom_analysis(
    symptom_data: SymptomRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Trigger medical analysis for reported symptom
    """
    try:
        background_tasks.add_task(
            run_symptom_analysis_task,
            str(current_user.user_id),
            symptom_data.dict()
        )
        
        return {"message": "Medical analysis triggered for symptom"}
        
    except Exception as e:
        logger.error(f"Failed to trigger symptom analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger medical analysis")

@router.post("/trigger/lab-result")
async def trigger_lab_analysis(
    lab_data: LabResultRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Trigger medical analysis for lab result
    """
    try:
        background_tasks.add_task(
            run_lab_analysis_task,
            str(current_user.user_id),
            lab_data.dict()
        )
        
        return {"message": "Medical analysis triggered for lab result"}
        
    except Exception as e:
        logger.error(f"Failed to trigger lab analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger medical analysis")

@router.post("/trigger/health-reading")
async def trigger_health_reading_analysis(
    reading_data: HealthReadingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Trigger medical analysis for health reading
    """
    try:
        background_tasks.add_task(
            run_health_reading_analysis_task,
            str(current_user.user_id),
            reading_data.dict()
        )
        
        return {"message": "Medical analysis triggered for health reading"}
        
    except Exception as e:
        logger.error(f"Failed to trigger health reading analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger medical analysis")

@router.post("/analyze")
async def trigger_manual_analysis(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Trigger comprehensive medical analysis for the current user
    """
    try:
        background_tasks.add_task(
            run_comprehensive_analysis_task,
            str(current_user.user_id)
        )
        
        return {"message": "Comprehensive medical analysis triggered"}
        
    except Exception as e:
        logger.error(f"Failed to trigger manual analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger medical analysis")

# Admin endpoints (if needed)
@router.get("/admin/stats")
async def get_system_notification_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)  
):
    """
    Get system-wide notification statistics (admin only)
    """
    try:
        
        result = db.execute("""
            SELECT 
                COUNT(*) as total_notifications,
                COUNT(DISTINCT user_id) as active_users,
                AVG(CASE WHEN is_read = false THEN 1 ELSE 0 END) as avg_unread_rate,
                COUNT(CASE WHEN severity = 'high' THEN 1 END) as high_severity_count
            FROM notifications 
            WHERE expires_at > NOW()
        """).fetchone()
        
        return {
                "total_notifications": result[0],
                "active_users": result[1],
                "average_unread_rate": float(result[2]) if result[2] else 0.0,
                "high_severity_count": result[3]
            }
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system statistics")

@router.post("/admin/cleanup")
async def cleanup_expired_notifications(
    background_tasks: BackgroundTasks,
    admin_user: User = Depends(require_admin)  # Fix #1: Admin authorization
):
    """
    Clean up expired notifications (admin only)
    """
    try:
        # Fix #2: Use background task wrapper with its own DB session
        background_tasks.add_task(run_cleanup_task)
        
        return {"message": "Notification cleanup initiated"}
        
    except Exception as e:
        logger.error(f"Failed to initiate cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate notification cleanup") 