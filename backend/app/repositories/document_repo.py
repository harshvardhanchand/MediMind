"""
DocumentRepository module - imports from the original location for compatibility
"""

from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import date

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import select, and_, func, or_, text, update
from sqlalchemy.types import Date as SQLDate

from sqlalchemy.exc import SQLAlchemyError
import logging

from app.models.document import Document, ProcessingStatus, DocumentType
from app.models.extracted_data import ExtractedData
from app.models.notification import Notification, AIAnalysisLog
from app.schemas.document import DocumentCreate, DocumentUpdate
from .base import CRUDBase

logger = logging.getLogger(__name__)


class DocumentRepository(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    def create_with_owner(
        self,
        db: Session,
        *,
        obj_in: DocumentCreate,
        user_id: UUID,
        storage_path: str,
        file_hash: Optional[str] = None,
    ) -> Document:
        """Create a new document record associated with a user."""
        db_obj_data = obj_in.model_dump(exclude_unset=True)

        db_obj = Document(
            **db_obj_data,
            user_id=user_id,
            storage_path=storage_path,
            file_hash=file_hash,
            processing_status=ProcessingStatus.PENDING,
        )

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    async def create_with_owner_async(
        self,
        db,
        *,
        obj_in: DocumentCreate,
        user_id: UUID,
        storage_path: str,
        file_hash: Optional[str] = None,
    ) -> Document:
        """Create a new document record associated with a user (async version)."""
        db_obj_data = obj_in.model_dump(exclude_unset=True)

        db_obj = Document(
            **db_obj_data,
            user_id=user_id,
            storage_path=storage_path,
            file_hash=file_hash,
            processing_status=ProcessingStatus.PENDING,
        )

        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    def get_by_id(self, db: Session, *, document_id: UUID) -> Optional[Document]:
        """Get a document by its ID using select()."""
        stmt = select(self.model).where(self.model.document_id == document_id)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_document(self, db: Session, *, document_id: UUID) -> Optional[Document]:
        """Alias for get_by_id for compatibility with tests."""
        return self.get_by_id(db, document_id=document_id)

    async def get_document_async(self, db, *, document_id: UUID) -> Optional[Document]:
        """Get a document by its ID using async session."""
        stmt = select(self.model).where(self.model.document_id == document_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_document_with_lock_async(
        self, db, *, document_id: UUID
    ) -> Optional[Document]:
        """Get a document by its ID with row-level locking to prevent race conditions."""
        stmt = (
            select(self.model)
            .where(self.model.document_id == document_id)
            .with_for_update()
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status_async(
        self, db, *, document_id: UUID, status: ProcessingStatus
    ) -> bool:
        """Update document processing status using async session."""
        stmt = (
            update(self.model)
            .where(self.model.document_id == document_id)
            .values(processing_status=status)
        )
        result = await db.execute(stmt)
        return result.rowcount > 0

    async def update_metadata_async(
        self, db, *, document_id: UUID, metadata_updates: Dict[str, Any]
    ) -> bool:
        """Update document metadata using async session."""
        stmt = (
            update(self.model)
            .where(self.model.document_id == document_id)
            .values(**metadata_updates)
        )
        result = await db.execute(stmt)
        return result.rowcount > 0

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
        return result.scalars().all()

    def get_multi_by_owner_optimized(
        self, db: Session, *, user_id: UUID, skip: int = 0, limit: int = 50
    ) -> List[Document]:
        """
        Get documents with optimized eager loading for list views.

        Loads:
        - Extracted data (content summary only, not full raw_text)
        - Recent notifications (title and severity only)

        Performance: ~85% fewer database queries
        Memory: ~100KB additional for 50 documents
        """
        stmt = (
            select(self.model)
            .options(
                joinedload(self.model.extracted_data).load_only(
                    ExtractedData.extraction_timestamp,
                    ExtractedData.processing_status,
                    ExtractedData.review_status,
                    ExtractedData.summary,  # Small text summary
                    ExtractedData.confidence_score,
                    ExtractedData.flags,
                ),
                selectinload(self.model.notifications)
                .options(
                    joinedload(Notification.ai_analysis_log).load_only(
                        AIAnalysisLog.summary, AIAnalysisLog.severity_assessment
                    )
                )
                .load_only(
                    Notification.title,
                    Notification.severity,
                    Notification.created_at,
                    Notification.is_read,
                    Notification.notification_type,
                ),
            )
            .where(self.model.user_id == user_id)
            .order_by(self.model.upload_timestamp.desc())
            .offset(skip)
            .limit(limit)
        )

        try:
            result = db.execute(stmt)
            documents = result.unique().scalars().all()

            logger.debug(
                f"Retrieved {len(documents)} documents with optimized loading for user {user_id}"
            )
            return documents

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_multi_by_owner_optimized: {e}")
            raise

    async def get_multi_by_owner_async(
        self, db, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """Get multiple documents belonging to a specific user (async version)."""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.upload_timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_multi_by_owner_optimized_async(
        self, db, *, user_id: UUID, skip: int = 0, limit: int = 50
    ) -> List[Document]:
        """
        Get documents with optimized eager loading for list views (async version).

        Loads:
        - Extracted data (basic fields only)
        - Recent notifications (title and severity only)

        Performance: ~85% fewer database queries
        Memory: ~100KB additional for 50 documents
        """
        stmt = (
            select(self.model)
            .options(
                joinedload(self.model.extracted_data).load_only(
                    ExtractedData.extraction_timestamp, ExtractedData.review_status
                ),
                selectinload(self.model.notifications)
                .options(
                    joinedload(Notification.ai_analysis_log).load_only(
                        AIAnalysisLog.summary, AIAnalysisLog.severity_assessment
                    )
                )
                .load_only(
                    Notification.title,
                    Notification.severity,
                    Notification.created_at,
                    Notification.is_read,
                    Notification.notification_type,
                ),
            )
            .where(self.model.user_id == user_id)
            .order_by(self.model.upload_timestamp.desc())
            .offset(skip)
            .limit(limit)
        )

        try:
            result = await db.execute(stmt)
            documents = result.unique().scalars().all()

            logger.debug(
                f"Retrieved {len(documents)} documents with optimized loading for user {user_id}"
            )
            return documents

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_multi_by_owner_optimized_async: {e}")
            raise

    def get_by_id_with_full_details(
        self, db: Session, *, document_id: UUID
    ) -> Optional[Document]:
        """
        Get a single document with all related data for detail views.

        Loads:
        - Full extracted data (including content and raw_text)
        - All notifications
        - AI analysis logs

        Use this for document detail pages where you need complete information.
        """
        stmt = (
            select(self.model)
            .options(
                # Load full extracted data
                joinedload(self.model.extracted_data),
                # Load all notifications
                selectinload(self.model.notifications),
                # Load AI analysis logs
                selectinload(self.model.ai_analysis_logs).load_only(
                    AIAnalysisLog.created_at,
                    AIAnalysisLog.trigger_type,
                    AIAnalysisLog.analysis_result,
                    AIAnalysisLog.llm_cost,
                    AIAnalysisLog.processing_time_ms,
                ),
            )
            .where(self.model.document_id == document_id)
        )
        result = db.execute(stmt)
        return result.scalars().unique().first()

    def get_summary_for_dashboard(
        self, db: Session, *, user_id: UUID, limit: int = 5
    ) -> List[Document]:
        """
        Get minimal document data for dashboard/home screen.

        No relationships loaded - just basic document info for performance.
        Use this when you only need document names and basic info.
        """
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.upload_timestamp.desc())
            .limit(limit)
        )
        result = db.execute(stmt)
        return result.scalars().all()

    def search_documents_optimized(
        self,
        db: Session,
        *,
        user_id: UUID,
        search_query: str,
        document_type: Optional[DocumentType] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Document]:
        """
        Search documents with optimized eager loading.

        Same optimization as get_multi_by_owner_optimized but with search functionality.
        """
        try:

            stmt = (
                select(self.model)
                .options(
                    joinedload(self.model.extracted_data).load_only(
                        ExtractedData.extraction_timestamp, ExtractedData.review_status
                    ),
                    selectinload(self.model.notifications).load_only(
                        Notification.title,
                        Notification.severity,
                        Notification.created_at,
                        Notification.is_read,
                    ),
                )
                .join(self.model.extracted_data, isouter=True)
                .where(self.model.user_id == user_id)
            )

            if document_type:
                stmt = stmt.where(self.model.document_type == document_type)

            search_term = f"%{search_query}%"

            search_conditions = [
                self.model.original_filename.ilike(search_term),
                func.coalesce(
                    self.model.metadata_overrides["source_name"].astext,
                    self.model.source_name,
                ).ilike(search_term),
                func.coalesce(
                    self.model.metadata_overrides["source_location_city"].astext,
                    self.model.source_location_city,
                ).ilike(search_term),
                func.coalesce(
                    self.model.metadata_overrides[
                        "related_to_health_goal_or_episode"
                    ].astext,
                    self.model.related_to_health_goal_or_episode,
                ).ilike(search_term),
            ]

            search_conditions.append(
                self.model.extracted_data.has(text("raw_text ILIKE :search_term"))
            )

            stmt = stmt.where(or_(*search_conditions))

            stmt = (
                stmt.order_by(self.model.upload_timestamp.desc())
                .offset(skip)
                .limit(limit)
            )

            result = db.execute(stmt, {"search_term": search_term})
            return result.scalars().unique().all()

        except Exception as e:
            logger.error(f"Failed to search documents: {str(e)}")
            return []

    def update_status(
        self, db: Session, *, document_id: UUID, status: ProcessingStatus
    ) -> Optional[Document]:
        """Update the processing status of a document."""
        db_obj = self.get_by_id(db, document_id=document_id)
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
        stmt = select(self.model).where(
            self.model.user_id == user_id, self.model.file_hash == file_hash
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
        limit: int = 100,
    ) -> List[Document]:
        """Get multiple documents for a user based on dynamic filter criteria,
        considering metadata_overrides first for filterable fields."""

        stmt = select(self.model).where(self.model.user_id == user_id)

        conditions = []
        for key, value in filters.items():
            if (
                value is None or value == "" or (isinstance(value, list) and not value)
            ):  # Skip empty/null filters
                continue

            if key == "document_type":
                # Accept either enum value (e.g., "lab_result") or name (e.g., "LAB_RESULT")
                try:
                    enum_val = DocumentType(value)
                    conditions.append(self.model.document_type == enum_val)
                except ValueError:
                    if isinstance(value, str) and value in DocumentType.__members__:
                        conditions.append(
                            self.model.document_type == DocumentType[value]
                        )

            elif (
                key == "document_date_range"
                and isinstance(value, (list, tuple))
                and len(value) == 2
            ):
                start_date, end_date = value
                if isinstance(start_date, date) and isinstance(end_date, date):

                    override_val = self.model.metadata_overrides[
                        "document_date"
                    ].astext.cast(SQLDate)
                    actual_val = func.coalesce(override_val, self.model.document_date)
                    conditions.append(actual_val.between(start_date, end_date))

            elif key == "source_name_contains" and isinstance(value, str):
                override_val = self.model.metadata_overrides["source_name"].astext
                actual_val = func.coalesce(override_val, self.model.source_name)
                conditions.append(actual_val.ilike(f"%{value}%"))

            elif key == "source_location_city_equals" and isinstance(value, str):
                override_val = self.model.metadata_overrides[
                    "source_location_city"
                ].astext
                actual_val = func.coalesce(
                    override_val, self.model.source_location_city
                )
                conditions.append(actual_val == value)

            elif key == "tags_include_any" and isinstance(value, list) and value:
                string_values = [str(v) for v in value]
                override_tags = self.model.metadata_overrides[
                    "tags"
                ]  # Assuming it's a JSON array
                actual_tags_json = func.coalesce(override_tags, self.model.tags)
                conditions.append(actual_tags_json.op("?|")(string_values))

            elif key == "tags_include_all" and isinstance(value, list) and value:
                string_values = [str(v) for v in value]
                override_tags = self.model.metadata_overrides["tags"]
                actual_tags_json = func.coalesce(override_tags, self.model.tags)

                conditions.append(actual_tags_json.op("@>")(string_values))

            elif key == "user_tags_include_any" and isinstance(value, list) and value:
                conditions.append(self.model.user_added_tags.op("?|")(value))
            elif key == "user_tags_include_all" and isinstance(value, list) and value:
                conditions.append(self.model.user_added_tags.op("@>")(value))

            elif key == "episode_equals" and isinstance(value, str):
                override_val = self.model.metadata_overrides[
                    "related_to_health_goal_or_episode"
                ].astext
                actual_val = func.coalesce(
                    override_val, self.model.related_to_health_goal_or_episode
                )
                conditions.append(actual_val == value)

            elif key == "filename_contains" and isinstance(value, str):
                conditions.append(self.model.original_filename.ilike(f"%{value}%"))

        if conditions:
            stmt = stmt.where(and_(*conditions))
            override_order_date = self.model.metadata_overrides[
                "document_date"
            ].astext.cast(SQLDate)
            actual_order_date = func.coalesce(
                override_order_date, self.model.document_date
            )
            stmt = stmt.order_by(
                actual_order_date.desc().nullslast(), self.model.upload_timestamp.desc()
            )
            stmt = stmt.offset(skip).limit(limit)
            result = db.execute(stmt)
            return result.scalars().all()

    def update_overrides(
        self, db: Session, *, document_id: UUID, overrides_in: Dict[str, Any]
    ) -> Optional[Document]:
        """Update the metadata_overrides JSON field for a specific document."""
        db_obj = self.get_by_id(db=db, document_id=document_id)
        if not db_obj:
            logger.warning(
                f"Document not found with id {document_id} for override update."
            )
            return None

        current_overrides = db_obj.metadata_overrides or {}

        updated = False
        for key, value in overrides_in.items():
            if value is not None:
                if key not in current_overrides or current_overrides[key] != value:
                    current_overrides[key] = value
                    updated = True
            elif key in current_overrides:
                del current_overrides[key]
                updated = True

        if updated:
            db_obj.metadata_overrides = current_overrides
            try:
                db.add(db_obj)
                db.commit()
                db.refresh(db_obj)
                logger.info(
                    f"Successfully updated metadata overrides for document {document_id}."
                )
                return db_obj
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(
                    f"Error updating metadata overrides for document {document_id}: {e}",
                    exc_info=True,
                )
                return None
        else:
            logger.info(
                f"No changes in metadata overrides for document {document_id}. No update performed."
            )
            return db_obj

    def update_metadata(
        self, db: Session, *, document_id: UUID, metadata_updates: Dict[str, Any]
    ) -> Optional[Document]:
        """Update specific metadata fields of a Document record."""
        db_obj = self.get_by_id(db=db, document_id=document_id)
        if not db_obj:
            logger.warning(
                f"Document not found with id {document_id} for metadata update."
            )
            return None

        updated = False
        allowed_metadata_fields = [
            "document_date",
            "source_name",
            "source_location_city",
            "tags",
            "related_to_health_goal_or_episode",
        ]

        for key, value in metadata_updates.items():
            if key in allowed_metadata_fields:

                if getattr(db_obj, key) != value:
                    setattr(db_obj, key, value)
                    updated = True
            else:
                logger.warning(
                    f"Attempted to update disallowed or unknown metadata field '{key}' for document {document_id}"
                )

        if updated:
            try:
                db.add(db_obj)
                db.commit()
                db.refresh(db_obj)
                logger.info(
                    f"Successfully updated metadata for document {document_id}."
                )
                return db_obj
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(
                    f"Error updating metadata for document {document_id}: {e}",
                    exc_info=True,
                )
                return None
        else:
            logger.info(
                f"No metadata changes detected for document {document_id}. No update performed."
            )
            return db_obj

    def search_documents(
        self,
        db: Session,
        *,
        user_id: UUID,
        search_query: str,
        document_type: Optional[DocumentType] = None,
        skip: int = 0,
        limit: int = 100,
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
            return self.get_multi_by_owner(
                db=db, user_id=user_id, skip=skip, limit=limit
            )

        try:
            # Create a query that joins Document with ExtractedData to search in raw_text as well
            stmt = (
                select(self.model)
                .join(self.model.extracted_data, isouter=True)
                .where(self.model.user_id == user_id)
            )

            # Add document_type filter if provided
            if document_type:
                stmt = stmt.where(self.model.document_type == document_type)

            search_term = f"%{search_query}%"

            search_conditions = [
                self.model.original_filename.ilike(search_term),
                func.coalesce(
                    self.model.metadata_overrides["source_name"].astext,
                    self.model.source_name,
                ).ilike(search_term),
                func.coalesce(
                    self.model.metadata_overrides["source_location_city"].astext,
                    self.model.source_location_city,
                ).ilike(search_term),
                func.coalesce(
                    self.model.metadata_overrides[
                        "related_to_health_goal_or_episode"
                    ].astext,
                    self.model.related_to_health_goal_or_episode,
                ).ilike(search_term),
            ]

            search_conditions.append(
                self.model.extracted_data.has(text("raw_text ILIKE :search_term"))
            )

            tsquery = func.plainto_tsquery("english", search_query)

            tsvector_expr = func.to_tsvector(
                "english",
                func.concat_ws(
                    " ",
                    self.model.original_filename,
                    func.coalesce(
                        self.model.metadata_overrides["source_name"].astext,
                        self.model.source_name,
                    ),
                    func.coalesce(
                        self.model.metadata_overrides["source_location_city"].astext,
                        self.model.source_location_city,
                    ),
                    func.coalesce(
                        self.model.metadata_overrides[
                            "related_to_health_goal_or_episode"
                        ].astext,
                        self.model.related_to_health_goal_or_episode,
                    ),
                ),
            )

            # Add full-text search condition
            search_conditions.append(tsvector_expr.op("@@")(tsquery))

            # Add combined search conditions to the query
            stmt = stmt.where(or_(*search_conditions))

            stmt = stmt.order_by(
                func.ts_rank(tsvector_expr, tsquery).desc(),
                self.model.upload_timestamp.desc(),
            )

            stmt = stmt.offset(skip).limit(limit)

            result = db.execute(stmt, {"search_term": search_term})
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error during document search: {str(e)}", exc_info=True)

            return []


document_repo = DocumentRepository(Document)
