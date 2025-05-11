"""
DocumentRepository module - imports from the original location for compatibility
"""
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, or_, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import Date as SQLDate

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
        """Get multiple documents for a user based on dynamic filter criteria,
        considering metadata_overrides first for filterable fields."""
        
        stmt = select(self.model).where(self.model.user_id == user_id)
        
        conditions = []
        for key, value in filters.items():
            if value is None or value == '' or (isinstance(value, list) and not value): # Skip empty/null filters
                continue

            # Helper to get overridden value or base value
            # metadata_overrides field is assumed to be JSON or JSONB
            # Base fields are actual columns
            
            if key == "document_type" and value in DocumentType.__members__:
                # document_type is not typically overridden in metadata_overrides as per current model structure.
                # If it were, similar coalesce logic would apply.
                conditions.append(self.model.document_type == DocumentType[value])

            elif key == "document_date_range" and isinstance(value, (list, tuple)) and len(value) == 2:
                start_date, end_date = value
                if isinstance(start_date, date) and isinstance(end_date, date):
                    # Coalesce logic: metadata_overrides['document_date'] (as text, then cast to Date) OR model.document_date
                    override_val = self.model.metadata_overrides['document_date'].astext.cast(SQLDate)
                    actual_val = func.coalesce(override_val, self.model.document_date)
                    conditions.append(actual_val.between(start_date, end_date))

            elif key == "source_name_contains" and isinstance(value, str):
                override_val = self.model.metadata_overrides['source_name'].astext
                actual_val = func.coalesce(override_val, self.model.source_name)
                conditions.append(actual_val.ilike(f"%{value}%"))

            elif key == "source_location_city_equals" and isinstance(value, str):
                override_val = self.model.metadata_overrides['source_location_city'].astext
                actual_val = func.coalesce(override_val, self.model.source_location_city)
                conditions.append(actual_val == value)
            
            # For tags, metadata_overrides might store tags as a JSON array.
            # Base model.tags is also JSON.
            # We need to ensure the JSON operators work on the result of coalesce.
            # The .astext might not be needed if the column is JSONB and op works directly.
            # Assuming PostgreSQL specific JSON operators:
            # '?|' (jsonb_exists_any) and '@>' (jsonb_contains)

            elif key == "tags_include_any" and isinstance(value, list) and value:
                # Coalesce returns a JSON(B) array if override exists, else the base tags JSON(B) field
                # Ensure value is a list of strings for the ?| operator
                string_values = [str(v) for v in value]
                override_tags = self.model.metadata_overrides['tags'] # Assuming it's a JSON array
                actual_tags_json = func.coalesce(override_tags, self.model.tags)
                # The op('?|') requires the left side to be a JSONB expression usually.
                # If 'tags' and 'metadata_overrides.tags' are JSONB, this should work.
                # If they are JSON, some DBs might require casting to JSONB for these operators.
                # For simplicity, assuming direct op works or casting happens implicitly/configured.
                conditions.append(actual_tags_json.op('?|')(string_values))


            elif key == "tags_include_all" and isinstance(value, list) and value:
                string_values = [str(v) for v in value] # Ensure list of strings for @>
                override_tags = self.model.metadata_overrides['tags']
                actual_tags_json = func.coalesce(override_tags, self.model.tags)
                # The contains operator (@>) typically works with JSONB arrays on the left
                # and a JSONB array on the right.
                conditions.append(actual_tags_json.op('@>')(string_values))


            # user_added_tags are not typically in metadata_overrides, they are a separate field.
            # If they were part of overrides, similar logic to 'tags' would apply.
            elif key == "user_tags_include_any" and isinstance(value, list) and value:
                 conditions.append(self.model.user_added_tags.op('?|')(value))
            elif key == "user_tags_include_all" and isinstance(value, list) and value:
                 conditions.append(self.model.user_added_tags.op('@>')(value))
            
            elif key == "episode_equals" and isinstance(value, str):
                # Assuming 'related_to_health_goal_or_episode' can be overridden
                override_val = self.model.metadata_overrides['related_to_health_goal_or_episode'].astext
                actual_val = func.coalesce(override_val, self.model.related_to_health_goal_or_episode)
                conditions.append(actual_val == value)

            elif key == "filename_contains" and isinstance(value, str):
                 # original_filename is not typically overridden.
                 conditions.append(self.model.original_filename.ilike(f"%{value}%"))
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
            
            # Add ordering - default to document_date descending, then upload_timestamp descending
            # If document_date is overridden, we should order by the actual_date used for filtering.
            override_order_date = self.model.metadata_overrides['document_date'].astext.cast(SQLDate)
            actual_order_date = func.coalesce(override_order_date, self.model.document_date)
            
            stmt = stmt.order_by(actual_order_date.desc().nullslast(), self.model.upload_timestamp.desc())
            
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

    def search_documents(
        self,
        db: Session,
        *,
        user_id: UUID, 
        search_query: str,
        document_type: Optional[DocumentType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """
        Search documents using PostgreSQL full-text search.
        
        This method creates a full-text search query across multiple fields:
        - original_filename
        - source_name
        - source_location_city
        - tags (as text)
        - user_added_tags (as text)
        - related_to_health_goal_or_episode
        - extracted text from ExtractedData.raw_text (via join)
        
        Args:
            db: Database session
            user_id: User ID to restrict search to
            search_query: Text to search for
            document_type: Optional filter for document type
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of Document objects matching the search criteria
        """
        # Sanitize the search query to prevent SQL injection
        search_query = search_query.strip()
        if not search_query:
            # If empty search, just return documents by recency
            return self.get_multi_by_owner(db=db, user_id=user_id, skip=skip, limit=limit)
            
        try:
            # Create a query that joins Document with ExtractedData to search in raw_text as well
            stmt = (
                select(self.model)
                .join(
                    self.model.extracted_data, 
                    isouter=True
                )
                .where(self.model.user_id == user_id)
            )
            
            # Add document_type filter if provided
            if document_type:
                stmt = stmt.where(self.model.document_type == document_type)
                
            # Create conditions for full-text search across various fields
            # PostgreSQL's to_tsvector converts text to searchable tokens
            # and to_tsquery converts the search query to a query object
            
            # Search terms for simple string matching on various fields
            search_term = f"%{search_query}%"
            
            # Use a combination of ilike for simple text fields and array operators for JSON array fields
            search_conditions = [
                self.model.original_filename.ilike(search_term),
                func.coalesce(self.model.metadata_overrides['source_name'].astext, self.model.source_name).ilike(search_term),
                func.coalesce(self.model.metadata_overrides['source_location_city'].astext, self.model.source_location_city).ilike(search_term),
                func.coalesce(self.model.metadata_overrides['related_to_health_goal_or_episode'].astext, self.model.related_to_health_goal_or_episode).ilike(search_term),
            ]
            
            # Add condition for searching within ExtractedData.raw_text
            # Only search if there's a join to ExtractedData (raw_text is not null)
            search_conditions.append(
                self.model.extracted_data.has(text("raw_text ILIKE :search_term"))
            )
            
            # PostgreSQL full-text search using tsvector/tsquery for better search quality
            # Convert the search query to tsquery format, normalizing it
            tsquery = func.plainto_tsquery('english', search_query)
            
            # Search in document fields using tsvector
            # Convert multiple fields to tsvectors and combine them
            tsvector_expr = func.to_tsvector(
                'english',
                func.concat_ws(
                    ' ',
                    self.model.original_filename,
                    func.coalesce(self.model.metadata_overrides['source_name'].astext, self.model.source_name),
                    func.coalesce(self.model.metadata_overrides['source_location_city'].astext, self.model.source_location_city),
                    func.coalesce(self.model.metadata_overrides['related_to_health_goal_or_episode'].astext, self.model.related_to_health_goal_or_episode)
                )
            )
            
            # Add full-text search condition
            search_conditions.append(tsvector_expr.op('@@')(tsquery))
            
            # Add combined search conditions to the query
            stmt = stmt.where(or_(*search_conditions))
            
            # Order by relevance and recency
            # For relevance ranking, use ts_rank with normalized tsvector
            stmt = stmt.order_by(
                # Rank by text search relevance (higher is better)
                func.ts_rank(tsvector_expr, tsquery).desc(),
                # Then by upload timestamp (newer first)
                self.model.upload_timestamp.desc()
            )
            
            # Add pagination
            stmt = stmt.offset(skip).limit(limit)
            
            # Parameterize the query to safely handle the search term
            # This is important for security against SQL injection
            result = db.execute(stmt, {"search_term": search_term})
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error during document search: {str(e)}", exc_info=True)
            # In case of error, return empty list rather than crashing
            return []

# Create a singleton instance
document_repo = DocumentRepository(Document) 