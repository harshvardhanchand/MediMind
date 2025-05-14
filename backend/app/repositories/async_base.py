from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy import select, delete # delete is used in original remove
from sqlalchemy.ext.asyncio import AsyncSession
# Assuming your Pydantic models might have a .model_dump() method (from Pydantic v2)
# If using Pydantic v1, it would be .dict()

# ModelType, CreateSchemaType, UpdateSchemaType are defined as in the sync base
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

class AsyncCRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        pk_col = next(iter(self.model.__mapper__.primary_key))
        stmt = select(self.model).where(pk_col == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        # Assuming obj_in is a Pydantic model with model_dump()
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Assuming obj_in is a Pydantic model with model_dump()
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db.add(db_obj) # db_obj is already in session or becomes part of it
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        # Re-fetch the object in the current async session before deleting
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj 