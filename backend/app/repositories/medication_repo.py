from uuid import UUID
from typing import List, Optional
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, desc

import logging

from app.models.medication import Medication, MedicationStatus
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