"""
DocumentRepository module - imports from the original location for compatibility
"""
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.models.document import Document, ProcessingStatus, DocumentType
from app.schemas.document import DocumentCreate, DocumentUpdate
from .base import CRUDBase

logger = logging.getLogger(__name__)

class DocumentRepository(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: DocumentCreate, user_id: UUID, storage_path: str, file_hash: Optional[str] = None
    ) -> Document:
        """Create a new document record associated with a user."""
        db_obj_data = obj_in.model_dump(exclude_unset=True)
        db_obj = Document(
            **db_obj_data, 
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

    def get_multi_by_filters(
        self, 
        db: Session, 
        *, 
        user_id: UUID, 
        filters: Dict[str, Any],
        skip: int = 0, 
        limit: int = 100
    ) -> List[Document]:
        """Get multiple documents for a user based on dynamic filter criteria."""
        
        # TODO: Implement override handling for filters.
        # The current implementation only filters on the base/system fields.
        # It needs to be updated to check the 'metadata_overrides' JSON field first
        # for each relevant filter key (e.g., document_date, source_name, tags, etc.)
        # and use the override value if present, otherwise fall back to the base field.
        # This requires using appropriate JSON functions/operators for the specific database (e.g., PostgreSQL JSONB).
        
        stmt = select(self.model).where(self.model.user_id == user_id)
        
        # Apply filters dynamically (CURRENTLY ONLY ON BASE FIELDS)
        conditions = []
        for key, value in filters.items():
            if value is None or value == '' or value == []: # Skip empty filters
                continue

            if key == "document_type" and value in DocumentType.__members__:
                 conditions.append(self.model.document_type == DocumentType[value])
            elif key == "document_date_range" and isinstance(value, (list, tuple)) and len(value) == 2:
                start_date, end_date = value
                if isinstance(start_date, date) and isinstance(end_date, date):
                    conditions.append(self.model.document_date.between(start_date, end_date))
            elif key == "source_name_contains" and isinstance(value, str):
                conditions.append(self.model.source_name.ilike(f"%{value}%"))
            elif key == "source_location_city_equals" and isinstance(value, str):
                conditions.append(self.model.source_location_city == value)
            elif key == "tags_include_any" and isinstance(value, list) and value:
                 # Assumes PostgreSQL JSONB and tags stored as list of strings
                 # Uses the '?|' operator (jsonb_exists_any)
                 conditions.append(self.model.tags.op('?|')(value))
            elif key == "tags_include_all" and isinstance(value, list) and value:
                 # Assumes PostgreSQL JSONB and tags stored as list of strings
                 # Uses the '@>' operator (jsonb_contains)
                 conditions.append(self.model.tags.op('@>')(value))
            elif key == "user_tags_include_any" and isinstance(value, list) and value:
                 conditions.append(self.model.user_added_tags.op('?|')(value))
            elif key == "user_tags_include_all" and isinstance(value, list) and value:
                 conditions.append(self.model.user_added_tags.op('@>')(value))
            elif key == "episode_equals" and isinstance(value, str):
                 conditions.append(self.model.related_to_health_goal_or_episode == value)
            elif key == "filename_contains" and isinstance(value, str):
                 conditions.append(self.model.original_filename.ilike(f"%{value}%"))
            # Add more filter key handlers here as needed
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
            
        # Add ordering - default to document_date descending, then upload_timestamp descending
        stmt = stmt.order_by(self.model.document_date.desc().nullslast(), self.model.upload_timestamp.desc())
        
        # Add pagination
        stmt = stmt.offset(skip).limit(limit)
        
        result = db.execute(stmt)
        return result.scalars().all()

    def update_overrides(self, db: Session, *, document_id: UUID, overrides_in: Dict[str, Any]) -> Optional[Document]:
        """Update the metadata_overrides JSON field for a specific document."""
        db_obj = self.get_by_id(db=db, document_id=document_id)
        if not db_obj:
            logger.warning(f"Document not found with id {document_id} for override update.")
            return None

        # Get current overrides or initialize if null
        current_overrides = db_obj.metadata_overrides or {}
        
        # Merge new overrides - values in overrides_in will replace existing ones in current_overrides
        # Filter overrides_in to only include keys that are actually present in the input
        # (Pydantic schema might send None for fields not provided by user in PATCH)
        updated = False
        for key, value in overrides_in.items():
            if value is not None: # Only update if user provided a value (not None)
                if key not in current_overrides or current_overrides[key] != value:
                    current_overrides[key] = value
                    updated = True
            elif key in current_overrides: # Handle user setting a field back to None (removing override)
                 del current_overrides[key]
                 updated = True
                 
        if updated:
            db_obj.metadata_overrides = current_overrides
            try:
                db.add(db_obj)
                db.commit()
                db.refresh(db_obj)
                logger.info(f"Successfully updated metadata overrides for document {document_id}.")
                return db_obj
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(f"Error updating metadata overrides for document {document_id}: {e}", exc_info=True)
                return None
        else:
            logger.info(f"No changes in metadata overrides for document {document_id}. No update performed.")
            return db_obj

    def update_metadata(self, db: Session, *, document_id: UUID, metadata_updates: Dict[str, Any]) -> Optional[Document]:
        """Update specific metadata fields of a Document record."""
        db_obj = self.get_by_id(db=db, document_id=document_id)
        if not db_obj:
            logger.warning(f"Document not found with id {document_id} for metadata update.")
            return None
        
        updated = False
        allowed_metadata_fields = [
            "document_date", 
            "source_name", 
            "source_location_city", 
            "tags", # Assuming stored as JSON (list)
            # user_added_tags is managed separately by user actions
            "related_to_health_goal_or_episode"
            # Add other fields here if they should be updatable this way
        ]
        
        for key, value in metadata_updates.items():
            if key in allowed_metadata_fields:
                # Simple check to see if value actually changed to avoid unnecessary commits
                if getattr(db_obj, key) != value:
                    setattr(db_obj, key, value)
                    updated = True
            else:
                logger.warning(f"Attempted to update disallowed or unknown metadata field '{key}' for document {document_id}")

        if updated:
            try:
                db.add(db_obj) # Add to session if modified
                db.commit()
                db.refresh(db_obj)
                logger.info(f"Successfully updated metadata for document {document_id}.")
                return db_obj
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(f"Error updating metadata for document {document_id}: {e}", exc_info=True)
                return None
        else:
            logger.info(f"No metadata changes detected for document {document_id}. No update performed.")
            return db_obj # Return the object even if no changes were made

# Create a singleton instance
document_repo = DocumentRepository(Document) 