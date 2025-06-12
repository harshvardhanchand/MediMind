"""
Notification Service
Handles creation, storage, and delivery of medical notifications
"""

import json
import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from .medical_ai_service import get_medical_ai_service

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service for managing medical notifications
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = get_medical_ai_service(db)
    
    async def create_notification(
        self,
        user_id: str,
        notification_type: str,
        severity: str,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
        # Links to existing entities
        related_medication_id: Optional[str] = None,
        related_document_id: Optional[str] = None,
        related_health_reading_id: Optional[str] = None,
        related_extracted_data_id: Optional[str] = None
    ) -> str:
        """
        Create and store a single notification with entity relationships
        """
        try:
            notification_id = str(uuid.uuid4())
            
            # Default expiration: 30 days for low severity, 7 days for high severity
            if not expires_at:
                if severity == "high":
                    expires_at = datetime.now() + timedelta(days=7)
                elif severity == "medium":
                    expires_at = datetime.now() + timedelta(days=14)
                else:
                    expires_at = datetime.now() + timedelta(days=30)
            
            # Store notification in database
            self.db.execute(
                text("""
                    INSERT INTO notifications 
                    (id, user_id, type, severity, title, message, notification_metadata, expires_at, 
                     related_medication_id, related_document_id, related_health_reading_id, related_extracted_data_id,
                     created_at)
                    VALUES (:id, :user_id, :type, :severity, :title, :message, :notification_metadata, :expires_at,
                            :related_medication_id, :related_document_id, :related_health_reading_id, :related_extracted_data_id,
                            NOW())
                """),
                {
                    "id": notification_id,
                    "user_id": user_id,
                    "type": notification_type,
                    "severity": severity,
                    "title": title,
                    "message": message,
                    "notification_metadata": json.dumps(metadata) if metadata else None,
                    "expires_at": expires_at,
                    "related_medication_id": related_medication_id,
                    "related_document_id": related_document_id,
                    "related_health_reading_id": related_health_reading_id,
                    "related_extracted_data_id": related_extracted_data_id
                }
            )
            
            self.db.commit()
            
            logger.info(f"Created notification {notification_id} for user {user_id}")
            return notification_id
            
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")
            self.db.rollback()
            raise
    
    async def create_notifications_from_analysis(
        self,
        user_id: str,
        notifications_data: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Create multiple notifications from AI analysis
        """
        notification_ids = []
        
        try:
            for notification_data in notifications_data:
                notification_id = await self.create_notification(
                    user_id=notification_data["user_id"],
                    notification_type=notification_data["type"],
                    severity=notification_data["severity"],
                    title=notification_data["title"],
                    message=notification_data["message"],
                    metadata=notification_data.get("metadata"),
                    # Extract related entity IDs from metadata
                    related_medication_id=notification_data.get("related_medication_id"),
                    related_document_id=notification_data.get("related_document_id"),
                    related_health_reading_id=notification_data.get("related_health_reading_id"),
                    related_extracted_data_id=notification_data.get("related_extracted_data_id")
                )
                notification_ids.append(notification_id)
            
            logger.info(f"Created {len(notification_ids)} notifications for user {user_id}")
            return notification_ids
            
        except Exception as e:
            logger.error(f"Failed to create notifications from analysis: {str(e)}")
            raise
    
    async def trigger_medical_analysis(
        self,
        user_id: str,
        trigger_type: str,
        event_data: Dict[str, Any]
    ) -> List[str]:
        """
        Trigger medical analysis and create resulting notifications
        """
        try:
            logger.info(f"Triggering medical analysis for user {user_id}: {trigger_type}")
            
            # Use AI service to analyze medical event
            notifications_data = await self.ai_service.analyze_medical_event(
                user_id=user_id,
                trigger_type=trigger_type,
                event_data=event_data
            )
            
            if not notifications_data:
                logger.info(f"No notifications generated for user {user_id}")
                return []
            
            # Create notifications from analysis
            notification_ids = await self.create_notifications_from_analysis(
                user_id, 
                notifications_data
            )
            
            return notification_ids
            
        except Exception as e:
            logger.error(f"Medical analysis trigger failed: {str(e)}")
            return []
    
    def get_user_notifications(
        self,
        user_id: str,
        include_read: bool = True,
        include_dismissed: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get notifications for a user with related entity information
        """
        try:
            # Build query conditions
            conditions = ["n.user_id = :user_id", "n.expires_at > NOW()"]
            
            if not include_read:
                conditions.append("n.is_read = false")
            
            if not include_dismissed:
                conditions.append("n.is_dismissed = false")
            
            where_clause = " AND ".join(conditions)
            
            result = self.db.execute(
                text(f"""
                    SELECT 
                        n.id, n.type, n.severity, n.title, n.message, n.notification_metadata, 
                        n.is_read, n.is_dismissed, n.created_at, n.expires_at,
                        n.related_medication_id, n.related_document_id, 
                        n.related_health_reading_id, n.related_extracted_data_id,
                        m.name as medication_name,
                        d.original_filename as document_filename,
                        hr.reading_type as health_reading_test
                    FROM notifications n
                    LEFT JOIN medications m ON n.related_medication_id = m.medication_id
                    LEFT JOIN documents d ON n.related_document_id = d.document_id
                    LEFT JOIN health_readings hr ON n.related_health_reading_id = hr.health_reading_id
                    WHERE {where_clause}
                    ORDER BY n.created_at DESC 
                    LIMIT :limit
                """),
                {
                    "user_id": user_id,
                    "limit": limit
                }
            ).fetchall()
            
            notifications = []
            for row in result:
                notification = {
                    "id": row[0],
                    "type": row[1],
                    "severity": row[2],
                    "title": row[3],
                    "message": row[4],
                    "metadata": json.loads(row[5]) if row[5] else {},
                    "is_read": row[6],
                    "is_dismissed": row[7],
                    "created_at": row[8].isoformat() if row[8] else None,
                    "expires_at": row[9].isoformat() if row[9] else None,
                    # Related entity information
                    "related_entities": {
                        "medication": {
                            "id": row[10],
                            "name": row[14]
                        } if row[10] else None,
                        "document": {
                            "id": row[11],
                            "filename": row[15]
                        } if row[11] else None,
                        "health_reading": {
                            "id": row[12],
                            "test_name": row[16]
                        } if row[12] else None,
                        "extracted_data": {
                            "id": row[13]
                        } if row[13] else None
                    }
                }
                notifications.append(notification)
            
            return notifications
            
        except Exception as e:
            logger.error(f"Failed to get user notifications: {str(e)}")
            return []
    
    def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """
        Mark a notification as read
        """
        try:
            result = self.db.execute(
                text("""
                    UPDATE notifications 
                    SET is_read = true 
                    WHERE id = :id AND user_id = :user_id
                """),
                {
                    "id": notification_id,
                    "user_id": user_id
                }
            )
            
            self.db.commit()
            
            if result.rowcount > 0:
                logger.info(f"Marked notification {notification_id} as read")
                return True
            else:
                logger.warning(f"Notification {notification_id} not found or not owned by user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            self.db.rollback()
            return False
    
    def dismiss_notification(self, notification_id: str, user_id: str) -> bool:
        """
        Dismiss a notification
        """
        try:
            result = self.db.execute(
                text("""
                    UPDATE notifications 
                    SET is_dismissed = true 
                    WHERE id = :id AND user_id = :user_id
                """),
                {
                    "id": notification_id,
                    "user_id": user_id
                }
            )
            
            self.db.commit()
            
            if result.rowcount > 0:
                logger.info(f"Dismissed notification {notification_id}")
                return True
            else:
                logger.warning(f"Notification {notification_id} not found or not owned by user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to dismiss notification: {str(e)}")
            self.db.rollback()
            return False
    
    def get_notification_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get notification statistics for a user
        """
        try:
            # Get basic stats
            basic_result = self.db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total_count,
                        COUNT(CASE WHEN is_read = false THEN 1 END) as unread_count
                    FROM notifications 
                    WHERE user_id = :user_id 
                    AND expires_at > NOW() 
                    AND is_dismissed = false
                """),
                {"user_id": user_id}
            ).fetchone()
            
            # Get severity breakdown
            severity_result = self.db.execute(
                text("""
                    SELECT 
                        severity,
                        COUNT(*) as count
                    FROM notifications 
                    WHERE user_id = :user_id 
                    AND expires_at > NOW() 
                    AND is_dismissed = false
                    GROUP BY severity
                """),
                {"user_id": user_id}
            ).fetchall()
            
            # Get type breakdown
            type_result = self.db.execute(
                text("""
                    SELECT 
                        type,
                        COUNT(*) as count
                    FROM notifications 
                    WHERE user_id = :user_id 
                    AND expires_at > NOW() 
                    AND is_dismissed = false
                    GROUP BY type
                """),
                {"user_id": user_id}
            ).fetchall()
            
            # Build severity breakdown
            by_severity = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
            
            for row in severity_result:
                severity = row[0].lower() if row[0] else "low"
                count = row[1]
                if severity in by_severity:
                    by_severity[severity] = count
                else:
                    # Map any other severity levels
                    if severity in ["urgent", "emergency"]:
                        by_severity["critical"] += count
                    else:
                        by_severity["low"] += count
            
            # Build type breakdown
            by_type = {
                "interaction_alert": 0,
                "risk_alert": 0,
                "medication_reminder": 0,
                "lab_followup": 0,
                "symptom_monitoring": 0,
                "general_info": 0
            }
            
            for row in type_result:
                notification_type = row[0].lower() if row[0] else "general_info"
                count = row[1]
                
                # Map notification types to expected categories
                if notification_type in ["drug_interaction", "interaction_alert", "medication_interaction"]:
                    by_type["interaction_alert"] += count
                elif notification_type in ["risk_alert", "health_risk", "medical_risk"]:
                    by_type["risk_alert"] += count
                elif notification_type in ["medication_reminder", "dose_reminder", "refill_reminder"]:
                    by_type["medication_reminder"] += count
                elif notification_type in ["lab_followup", "lab_result", "test_followup"]:
                    by_type["lab_followup"] += count
                elif notification_type in ["symptom_monitoring", "symptom_alert", "symptom_tracking"]:
                    by_type["symptom_monitoring"] += count
                else:
                    by_type["general_info"] += count
            
            if basic_result:
                return {
                    "total_count": basic_result[0] or 0,
                    "unread_count": basic_result[1] or 0,
                    "by_severity": by_severity,
                    "by_type": by_type
                }
            
            # Return empty stats if no data
            return {
                "total_count": 0,
                "unread_count": 0,
                "by_severity": by_severity,
                "by_type": by_type
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification stats: {str(e)}")
            # Return empty stats structure on error
            return {
                "total_count": 0,
                "unread_count": 0,
                "by_severity": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                },
                "by_type": {
                    "interaction_alert": 0,
                    "risk_alert": 0,
                    "medication_reminder": 0,
                    "lab_followup": 0,
                    "symptom_monitoring": 0,
                    "general_info": 0
                }
            }
    
    async def cleanup_expired_notifications(self) -> int:
        """
        Clean up expired notifications
        """
        try:
            result = self.db.execute(
                text("""
                    DELETE FROM notifications 
                    WHERE expires_at <= NOW()
                """)
            )
            
            deleted_count = result.rowcount
            self.db.commit()
            
            logger.info(f"Cleaned up {deleted_count} expired notifications")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired notifications: {str(e)}")
            return 0

class MedicalEventTriggers:
    """
    Handles triggering medical analysis for various events
    """
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
    
    async def on_medication_added(self, user_id: str, medication_data: Dict[str, Any], medication_id: Optional[str] = None):
        """
        Trigger analysis when new medication is added
        """
        return await self.notification_service.trigger_medical_analysis(
            user_id=user_id,
            trigger_type="new_medication",
            event_data={
                "type": "new_medication",
                "medication": medication_data,
                "medication_id": medication_id,  # Link to specific medication
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def on_symptom_reported(self, user_id: str, symptom_data: Dict[str, Any]):
        """
        Trigger analysis when symptom is reported
        """
        return await self.notification_service.trigger_medical_analysis(
            user_id=user_id,
            trigger_type="symptom_reported",
            event_data={
                "type": "symptom_reported",
                "symptom": symptom_data,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def on_lab_result_added(self, user_id: str, lab_data: Dict[str, Any], health_reading_id: Optional[str] = None):
        """
        Trigger analysis when lab result is added
        """
        return await self.notification_service.trigger_medical_analysis(
            user_id=user_id,
            trigger_type="lab_result",
            event_data={
                "type": "lab_result",
                "lab_result": lab_data,
                "health_reading_id": health_reading_id,  # Link to specific health reading
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def on_health_reading_added(self, user_id: str, reading_data: Dict[str, Any], health_reading_id: Optional[str] = None):
        """
        Trigger analysis when health reading is added
        """
        return await self.notification_service.trigger_medical_analysis(
            user_id=user_id,
            trigger_type="health_reading",
            event_data={
                "type": "health_reading",
                "reading": reading_data,
                "health_reading_id": health_reading_id,  # Link to specific health reading
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def on_document_processed(self, user_id: str, document_data: Dict[str, Any], document_id: str, extracted_data_id: Optional[str] = None):
        """
        Trigger analysis when document is processed
        """
        return await self.notification_service.trigger_medical_analysis(
            user_id=user_id,
            trigger_type="document_processed",
            event_data={
                "type": "document_processed",
                "document": document_data,
                "document_id": document_id,  # Link to specific document
                "extracted_data_id": extracted_data_id,  # Link to extracted data
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def on_medication_discontinued(self, user_id: str, medication_data: Dict[str, Any], medication_id: Optional[str] = None):
        """
        Trigger analysis when medication is discontinued
        """
        return await self.notification_service.trigger_medical_analysis(
            user_id=user_id,
            trigger_type="medication_discontinued",
            event_data={
                "type": "medication_discontinued",
                "medication": medication_data,
                "medication_id": medication_id,  # Link to specific medication
                "timestamp": datetime.now().isoformat()
            }
        )

# Factory function
def get_notification_service(db: Session) -> NotificationService:
    """Get notification service instance"""
    return NotificationService(db)

def get_medical_triggers(notification_service: NotificationService) -> MedicalEventTriggers:
    """Get medical event triggers instance"""
    return MedicalEventTriggers(notification_service) 