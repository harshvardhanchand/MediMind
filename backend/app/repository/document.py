from uuid import UUID
from typing import List, Optional

# from sqlalchemy.orm import Session # Changed
from sqlalchemy.ext.asyncio import AsyncSession # Changed
from sqlalchemy.future import select

from app.models.document import Document, ProcessingStatus
from app.schemas.document import DocumentCreate, DocumentUpdate
from .base import CRUDBase

class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    async def create_with_owner(
        self, db: AsyncSession, *, obj_in: DocumentCreate, user_id: UUID, storage_path: str, file_hash: Optional[str] = None # Changed Session to AsyncSession
    ) -> Document:
        """Create a new document record associated with a user."""
        db_obj = Document(
            **obj_in.model_dump(), 
            user_id=user_id,
            storage_path=storage_path,
            file_hash=file_hash,
            processing_status=ProcessingStatus.PENDING # Explicitly set initial status
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_id(self, db: AsyncSession, *, document_id: UUID) -> Optional[Document]: # Changed Session to AsyncSession
        """Get a document by its ID."""
        stmt = select(self.model).where(self.model.document_id == document_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi_by_owner(
        self, db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 100 # Changed Session to AsyncSession
    ) -> List[Document]:
        """Get multiple documents belonging to a specific user."""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.upload_timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def update_status(
        self, db: AsyncSession, *, db_obj: Document, status: ProcessingStatus # Changed Session to AsyncSession
    ) -> Document:
        """Update the processing status of a document."""
        db_obj.processing_status = status
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
        
    async def get_by_hash_for_user(
        self, db: AsyncSession, *, user_id: UUID, file_hash: str
    ) -> Optional[Document]:
        """Get a document by file hash belonging to a specific user, if it exists."""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id, self.model.file_hash == file_hash)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_multi_by_status(
        self, db: AsyncSession, *, status: ProcessingStatus, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """Get all documents with a specific processing status."""
        stmt = (
            select(self.model)
            .where(self.model.processing_status == status)
            .order_by(self.model.upload_timestamp.asc())  # Process oldest first
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

# Create a singleton instance of the CRUDDocument class
document_repo = CRUDDocument(Document) 