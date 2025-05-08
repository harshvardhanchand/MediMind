from typing import Generic, TypeVar, Type, Optional, List, Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import Base

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        pk_col = next(iter(self.model.__mapper__.primary_key))
        stmt = select(self.model).where(pk_col == id)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        result = db.execute(stmt)
        return result.scalars().all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: Any) -> Optional[ModelType]:
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj 