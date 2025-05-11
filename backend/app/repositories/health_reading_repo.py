import uuid
from typing import List, Optional, Type

from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update

from app.models.health_reading import HealthReading, HealthReadingType
from app.schemas.health_reading import HealthReadingCreate, HealthReadingUpdate
from app.repositories.base import CRUDBase

class HealthReadingRepository(CRUDBase[HealthReading, HealthReadingCreate, HealthReadingUpdate]):
    def __init__(self, model: Type[HealthReading] = HealthReading):
        super().__init__(model)

    def get_by_id(self, db: Session, health_reading_id: uuid.UUID) -> Optional[HealthReading]:
        statement = select(self.model).where(self.model.health_reading_id == health_reading_id)
        return db.execute(statement).scalar_one_or_none()

    def create_with_owner(
        self, db: Session, *, obj_in: HealthReadingCreate, user_id: uuid.UUID
    ) -> HealthReading:
        db_obj = self.model(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100,
        reading_type: Optional[HealthReadingType] = None # Optional filter by type
    ) -> List[HealthReading]:
        statement = select(self.model).where(self.model.user_id == user_id)
        if reading_type:
            statement = statement.where(self.model.reading_type == reading_type)
        statement = statement.order_by(self.model.reading_date.desc()).offset(skip).limit(limit)
        return db.execute(statement).scalars().all()
    
    def update(
        self, db: Session, *, db_obj: HealthReading, obj_in: HealthReadingUpdate
    ) -> HealthReading:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, health_reading_id: uuid.UUID) -> HealthReading | None:
        statement = delete(self.model).where(self.model.health_reading_id == health_reading_id).returning(self.model)
        result = db.execute(statement)
        db.commit()
        return result.scalar_one_or_none()

health_reading_repo = HealthReadingRepository(HealthReading) 