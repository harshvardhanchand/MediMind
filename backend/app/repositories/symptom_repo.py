"""
Symptom Repository
Handles database operations for symptoms
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.symptom import Symptom, SymptomSeverity
from app.repositories.base import CRUDBase
from app.schemas.symptom import SymptomCreate, SymptomUpdate


class SymptomRepository(CRUDBase[Symptom, SymptomCreate, SymptomUpdate]):
    """Repository for symptom operations"""
    
    def get_by_user(
        self, 
        db: Session, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 100,
        severity: Optional[SymptomSeverity] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Symptom]:
        """Get symptoms for a specific user with optional filters"""
        query = db.query(self.model).filter(self.model.user_id == user_id)
        
       
        if severity:
            query = query.filter(self.model.severity == severity)
        
        if start_date:
            query = query.filter(self.model.reported_date >= start_date)
            
        if end_date:
            query = query.filter(self.model.reported_date <= end_date)
        
        return query.order_by(desc(self.model.reported_date)).offset(skip).limit(limit).all()
    
    def get_recent_by_user(
        self, 
        db: Session, 
        user_id: UUID, 
        days: int = 30,
        limit: int = 50
    ) -> List[Symptom]:
        """Get recent symptoms for a user within specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return db.query(self.model).filter(
            and_(
                self.model.user_id == user_id,
                self.model.reported_date >= cutoff_date
            )
        ).order_by(desc(self.model.reported_date)).limit(limit).all()
    
    def get_by_symptom_name(
        self, 
        db: Session, 
        user_id: UUID, 
        symptom_name: str,
        limit: int = 20
    ) -> List[Symptom]:
        """Get symptoms by name for a user (for tracking patterns)"""
        return db.query(self.model).filter(
            and_(
                self.model.user_id == user_id,
                self.model.symptom.ilike(f"%{symptom_name}%")
            )
        ).order_by(desc(self.model.reported_date)).limit(limit).all()
    
    def get_by_severity(
        self, 
        db: Session, 
        user_id: UUID, 
        severity: SymptomSeverity,
        limit: int = 50
    ) -> List[Symptom]:
        """Get symptoms by severity level"""
        return db.query(self.model).filter(
            and_(
                self.model.user_id == user_id,
                self.model.severity == severity
            )
        ).order_by(desc(self.model.reported_date)).limit(limit).all()
    
    def search_symptoms(
        self, 
        db: Session, 
        user_id: UUID, 
        search_query: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Symptom]:
        """Search symptoms by name or notes"""
        return db.query(self.model).filter(
            and_(
                self.model.user_id == user_id,
                self.model.symptom.ilike(f"%{search_query}%") |
                self.model.notes.ilike(f"%{search_query}%")
            )
        ).order_by(desc(self.model.reported_date)).offset(skip).limit(limit).all()
    
    def get_symptom_stats(self, db: Session, user_id: UUID) -> dict:
        """Get symptom statistics for a user"""
        total_symptoms = db.query(self.model).filter(self.model.user_id == user_id).count()
        
       
        recent_cutoff = datetime.utcnow() - timedelta(days=30)
        recent_symptoms = db.query(self.model).filter(
            and_(
                self.model.user_id == user_id,
                self.model.reported_date >= recent_cutoff
            )
        ).count()
        
        
        severity_stats = {}
        for severity in SymptomSeverity:
            count = db.query(self.model).filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.severity == severity
                )
            ).count()
            severity_stats[severity.value] = count
        
        return {
            "total_symptoms": total_symptoms,
            "recent_symptoms": recent_symptoms,
            "severity_breakdown": severity_stats
        }
    
    def create_with_user(
        self, 
        db: Session, 
        obj_in: SymptomCreate, 
        user_id: UUID
    ) -> Symptom:
        """Create a new symptom for a specific user"""
        obj_data = obj_in.dict()
        obj_data["user_id"] = user_id
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_by_id_and_user(
        self, 
        db: Session, 
        symptom_id: UUID, 
        user_id: UUID
    ) -> Optional[Symptom]:
        """Get a symptom by ID, ensuring it belongs to the user"""
        return db.query(self.model).filter(
            and_(
                self.model.symptom_id == symptom_id,
                self.model.user_id == user_id
            )
        ).first()
    
    def update_by_user(
        self, 
        db: Session, 
        symptom_id: UUID, 
        user_id: UUID, 
        obj_in: SymptomUpdate
    ) -> Optional[Symptom]:
        """Update a symptom, ensuring it belongs to the user"""
        db_obj = self.get_by_id_and_user(db, symptom_id, user_id)
        if not db_obj:
            return None
        
        return self.update(db, db_obj=db_obj, obj_in=obj_in)
    
    def delete_by_user(
        self, 
        db: Session, 
        symptom_id: UUID, 
        user_id: UUID
    ) -> bool:
        """Delete a symptom, ensuring it belongs to the user"""
        db_obj = self.get_by_id_and_user(db, symptom_id, user_id)
        if not db_obj:
            return False
        
        db.delete(db_obj)
        db.commit()
        return True



symptom_repo = SymptomRepository(Symptom) 