from uuid import UUID
from typing import List, Optional
from datetime import date

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import select, and_, or_, desc

import logging

from app.models.medication import Medication, MedicationStatus
from app.models.document import Document
from app.models.notification import Notification, AIAnalysisLog
from app.schemas.medication import MedicationCreate, MedicationUpdate
from .base import CRUDBase

logger = logging.getLogger(__name__)

class MedicationRepository(CRUDBase[Medication, MedicationCreate, MedicationUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: MedicationCreate, user_id: UUID
    ) -> Medication:
        """Create a new medication record associated with a user."""
        db_obj_data = obj_in.model_dump(exclude_unset=True)
        db_obj = Medication(
            **db_obj_data, 
            user_id=user_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_id(self, db: Session, *, medication_id: UUID) -> Optional[Medication]:
        """Get a medication by its ID."""
        stmt = select(self.model).where(self.model.medication_id == medication_id)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_multi_by_owner(
        self, db: Session, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Medication]:
        """Get multiple medications belonging to a specific user."""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(desc(self.model.updated_at))
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return result.scalars().all()
        
    def get_active_by_owner(
        self, db: Session, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Medication]:
        """Get active medications belonging to a specific user."""
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.user_id == user_id,
                    self.model.status == MedicationStatus.ACTIVE
                )
            )
            .order_by(desc(self.model.updated_at))
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return result.scalars().all()
        
    def search_by_owner(
        self, 
        db: Session, 
        *, 
        user_id: UUID, 
        search_query: str = None,
        status: MedicationStatus = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Medication]:
        """Search medications by name, reason, or doctor for a specific user."""
        stmt = select(self.model).where(self.model.user_id == user_id)
        
        # Add search filter if provided
        if search_query:
            search_term = f"%{search_query}%"
            stmt = stmt.where(
                or_(
                    self.model.name.ilike(search_term),
                    self.model.reason.ilike(search_term),
                    self.model.prescribing_doctor.ilike(search_term),
                    self.model.notes.ilike(search_term)
                )
            )
            
        # Add status filter if provided
        if status:
            stmt = stmt.where(self.model.status == status)
            
        # Add ordering, offset, and limit
        stmt = stmt.order_by(desc(self.model.updated_at)).offset(skip).limit(limit)
        
        result = db.execute(stmt)
        return result.scalars().all()
        
    def get_multi_by_owner_optimized(
        self, db: Session, *, user_id: UUID, skip: int = 0, limit: int = 50
    ) -> List[Medication]:
        """
        Get medications with optimized eager loading for list views.
        
        Loads:
        - Related document (filename and type only)
        - Recent notifications (title and severity only)
        
        Performance: ~90% fewer database queries
        Memory: ~50KB additional for 50 medications
        """
        stmt = (
            select(self.model)
            .options(
                # Load document info efficiently (joinedload for 1-to-1)
                joinedload(self.model.related_document).load_only(
                    Document.original_filename,
                    Document.document_type,
                    Document.document_date
                ),
                # Load notifications efficiently (selectinload for 1-to-many)
                selectinload(self.model.notifications).load_only(
                    Notification.title,
                    Notification.severity,
                    Notification.created_at,
                    Notification.is_read
                )
            )
            .where(self.model.user_id == user_id)
            .order_by(desc(self.model.updated_at))
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return result.scalars().unique().all()  # unique() needed with joinedload
    
    def get_active_by_owner_optimized(
        self, db: Session, *, user_id: UUID, skip: int = 0, limit: int = 50
    ) -> List[Medication]:
        """
        Get active medications with optimized eager loading.
        
        Same optimization as get_multi_by_owner_optimized but filtered for active only.
        """
        stmt = (
            select(self.model)
            .options(
                joinedload(self.model.related_document).load_only(
                    Document.original_filename,
                    Document.document_type,
                    Document.document_date
                ),
                selectinload(self.model.notifications).load_only(
                    Notification.title,
                    Notification.severity,
                    Notification.created_at,
                    Notification.is_read
                )
            )
            .where(
                and_(
                    self.model.user_id == user_id,
                    self.model.status == MedicationStatus.ACTIVE
                )
            )
            .order_by(desc(self.model.updated_at))
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return result.scalars().unique().all()
    
    def search_by_owner_optimized(
        self, 
        db: Session, 
        *, 
        user_id: UUID, 
        search_query: str = None,
        status: MedicationStatus = None,
        skip: int = 0, 
        limit: int = 50
    ) -> List[Medication]:
        """
        Search medications with optimized eager loading.
        
        Same optimization as other methods but with search functionality.
        """
        stmt = (
            select(self.model)
            .options(
                joinedload(self.model.related_document).load_only(
                    Document.original_filename,
                    Document.document_type,
                    Document.document_date
                ),
                selectinload(self.model.notifications).load_only(
                    Notification.title,
                    Notification.severity,
                    Notification.created_at,
                    Notification.is_read
                )
            )
            .where(self.model.user_id == user_id)
        )
        
        # Add search filter if provided
        if search_query:
            search_term = f"%{search_query}%"
            stmt = stmt.where(
                or_(
                    self.model.name.ilike(search_term),
                    self.model.reason.ilike(search_term),
                    self.model.prescribing_doctor.ilike(search_term),
                    self.model.notes.ilike(search_term)
                )
            )
            
        # Add status filter if provided
        if status:
            stmt = stmt.where(self.model.status == status)
            
        # Add ordering, offset, and limit
        stmt = stmt.order_by(desc(self.model.updated_at)).offset(skip).limit(limit)
        
        result = db.execute(stmt)
        return result.scalars().unique().all()
    
    def get_by_id_with_full_details(self, db: Session, *, medication_id: UUID) -> Optional[Medication]:
        """
        Get a single medication with all related data for detail views.
        
        Loads:
        - Full related document
        - All notifications
        - AI analysis logs
        
        Use this for medication detail pages where you need complete information.
        """
        stmt = (
            select(self.model)
            .options(
                # Load full document details
                joinedload(self.model.related_document),
                # Load all notifications
                selectinload(self.model.notifications),
                # Load AI analysis logs
                selectinload(self.model.ai_analysis_logs).load_only(
                    AIAnalysisLog.created_at,
                    AIAnalysisLog.trigger_type,
                    AIAnalysisLog.analysis_result,
                    AIAnalysisLog.llm_cost,
                    AIAnalysisLog.processing_time_ms
                )
            )
            .where(self.model.medication_id == medication_id)
        )
        result = db.execute(stmt)
        return result.scalars().unique().first()
    
    def get_summary_for_dashboard(self, db: Session, *, user_id: UUID, limit: int = 5) -> List[Medication]:
        """
        Get minimal medication data for dashboard/home screen.
        
        No relationships loaded - just basic medication info for performance.
        Use this when you only need medication names and basic info.
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.user_id == user_id,
                    self.model.status == MedicationStatus.ACTIVE
                )
            )
            .order_by(desc(self.model.updated_at))
            .limit(limit)
        )
        result = db.execute(stmt)
        return result.scalars().all()

    def update_status(
        self, db: Session, *, medication_id: UUID, status: MedicationStatus
    ) -> Optional[Medication]:
        """Update the status of a medication."""
        db_obj = self.get_by_id(db, medication_id=medication_id)
        if not db_obj:
            return None
            
        db_obj.status = status
        db.commit()
        db.refresh(db_obj)
        return db_obj

# Create a singleton instance
medication_repo = MedicationRepository(Medication) 