"""
DocumentRepository module - imports from the original location for compatibility
"""
from uuid import UUID
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.document import Document, ProcessingStatus
from app.schemas.document import DocumentCreate, DocumentUpdate
from .base import CRUDBase

class DocumentRepository(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: DocumentCreate, user_id: UUID, storage_path: str, file_hash: Optional[str] = None
    ) -> Document:
        """Create a new document record associated with a user."""
        db_obj = Document(
            **obj_in.model_dump(), 
            user_id=user_id,
            storage_path=storage_path,
            file_hash=file_hash,
            processing_status=ProcessingStatus.PENDING
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_id(self, db: Session, *, document_id: UUID) -> Optional[Document]:
        """Get a document by its ID using select()."""
        stmt = select(self.model).where(self.model.document_id == document_id)
        result = db.execute(stmt)
        return result.scalar_one_or_none() # Use scalar_one_or_none for single result

    def get_document(self, db: Session, *, document_id: UUID) -> Optional[Document]:
        """Alias for get_by_id for compatibility with tests."""
        return self.get_by_id(db, document_id=document_id)

    def get_multi_by_owner(
        self, db: Session, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """Get multiple documents belonging to a specific user using select()."""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.upload_timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return result.scalars().all() # Use scalars().all() for multiple results

    def update_status(
        self, db: Session, *, document_id: UUID, status: ProcessingStatus
    ) -> Optional[Document]:
        """Update the processing status of a document."""
        db_obj = self.get_by_id(db, document_id=document_id) # Uses the refactored get_by_id
        if not db_obj:
            return None
        db_obj.processing_status = status
        db.commit()
        db.refresh(db_obj)
        return db_obj
        
    def get_by_hash_for_user(
        self, db: Session, *, user_id: UUID, file_hash: str
    ) -> Optional[Document]:
        """Get a document by file hash belonging to a specific user using select()."""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id, self.model.file_hash == file_hash)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()
        
    def get_multi_by_status(
        self, db: Session, *, status: ProcessingStatus, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """Get all documents with a specific processing status using select()."""
        stmt = (
            select(self.model)
            .where(self.model.processing_status == status)
            .order_by(self.model.upload_timestamp.asc())
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        return result.scalars().all()

# Create a singleton instance
document_repo = DocumentRepository(Document) 