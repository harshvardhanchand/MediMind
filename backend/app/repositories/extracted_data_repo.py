"""
Repository for CRUD operations on ExtractedData entities.
"""
import uuid
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime

from app.models.extracted_data import ExtractedData, ReviewStatus
from app.schemas.extracted_data import ExtractedDataCreate, ExtractedDataUpdate
from .base import CRUDBase

logger = logging.getLogger(__name__)

class ExtractedDataRepository(CRUDBase[ExtractedData, ExtractedDataCreate, ExtractedDataUpdate]):
    def create_initial_extracted_data(self, db: Session, *, document_id: uuid.UUID) -> Optional[ExtractedData]:
        """
        Creates an initial ExtractedData record for a new document.
        Content will be empty initially, and raw_text can be populated later.
        Status defaults to PENDING_REVIEW.
        """
        try:
            # Initialize with empty content or a placeholder if your schema requires `content`
            # The model defines `content` as nullable=False, so an empty JSON object is appropriate.
            # raw_text is nullable. review_status defaults in the model.
            db_extracted_data = ExtractedData(
                document_id=document_id,
                content={}, # Default to empty JSON object
                # raw_text will be populated after OCR
                # review_status defaults to PENDING_REVIEW in the model
            )
            db.add(db_extracted_data)
            db.commit()
            db.refresh(db_extracted_data)
            logger.info(f"Initial ExtractedData record created for document_id: {document_id}")
            return db_extracted_data
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating initial ExtractedData for document {document_id}: {e}", exc_info=True)
            return None

    def get_by_document_id(self, db: Session, *, document_id: uuid.UUID) -> Optional[ExtractedData]:
        """Retrieves an ExtractedData record by its associated document_id."""
        try:
            # Using query for sync session
            return db.query(ExtractedData).filter(ExtractedData.document_id == document_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving ExtractedData for document {document_id}: {e}", exc_info=True)
            return None

    def update_raw_text(self, db: Session, *, document_id: uuid.UUID, raw_text: str) -> Optional[ExtractedData]:
        """Updates the raw_text field of an ExtractedData record."""
        db_extracted_data = self.get_by_document_id(db, document_id=document_id)
        if db_extracted_data:
            try:
                db_extracted_data.raw_text = raw_text
                db.commit()
                db.refresh(db_extracted_data)
                logger.info(f"Updated raw_text for ExtractedData linked to document_id: {document_id}")
                return db_extracted_data
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(f"Error updating raw_text for ExtractedData (document {document_id}): {e}", exc_info=True)
                return None
        return None

    def update_structured_content(self, db: Session, *, document_id: uuid.UUID, content: Dict[str, Any]) -> Optional[ExtractedData]:
        """Updates the structured content field of an ExtractedData record."""
        db_extracted_data = self.get_by_document_id(db, document_id=document_id)
        if db_extracted_data:
            try:
                db_extracted_data.content = content
                # Potentially update extraction_timestamp here if desired
                db.commit()
                db.refresh(db_extracted_data)
                logger.info(f"Updated structured content for ExtractedData linked to document_id: {document_id}")
                return db_extracted_data
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(f"Error updating content for ExtractedData (document {document_id}): {e}", exc_info=True)
                return None
        return None

    def update_review_status(
        self,
        db: Session,
        *,
        document_id: uuid.UUID,
        review_status: ReviewStatus,
        reviewed_by_user_id: Optional[uuid.UUID] = None
    ) -> Optional[ExtractedData]:
        """Updates the review_status and related fields of an ExtractedData record."""
        db_extracted_data = self.get_by_document_id(db, document_id=document_id)
        if db_extracted_data:
            try:
                db_extracted_data.review_status = review_status
                if reviewed_by_user_id:
                    db_extracted_data.reviewed_by_user_id = reviewed_by_user_id
                # Set review_timestamp to current time when status is updated
                db_extracted_data.review_timestamp = datetime.utcnow()
                db.commit()
                db.refresh(db_extracted_data)
                logger.info(f"Updated review_status to {review_status} for ExtractedData (document {document_id})")
                return db_extracted_data
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(f"Error updating review_status for ExtractedData (document {document_id}): {e}", exc_info=True)
                return None
        return None

    
    
    async def get_by_document_id_async(self, db, *, document_id: uuid.UUID) -> Optional[ExtractedData]:
        """Retrieves an ExtractedData record by its associated document_id using async session."""
        try:
            from sqlalchemy import select
            stmt = select(ExtractedData).where(ExtractedData.document_id == document_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving ExtractedData for document {document_id}: {e}", exc_info=True)
            return None

    async def update_raw_text_async(self, db, *, document_id: uuid.UUID, raw_text: str) -> bool:
        """Updates the raw_text field of an ExtractedData record using async session."""
        try:
            from sqlalchemy import update
            stmt = (
                update(ExtractedData)
                .where(ExtractedData.document_id == document_id)
                .values(raw_text=raw_text)
            )
            result = await db.execute(stmt)
            return result.rowcount > 0
        except SQLAlchemyError as e:
            logger.error(f"Error updating raw_text for ExtractedData (document {document_id}): {e}", exc_info=True)
            return False

    async def update_structured_content_async(self, db, *, document_id: uuid.UUID, content: Dict[str, Any]) -> bool:
        """Updates the structured content field of an ExtractedData record using async session."""
        try:
            from sqlalchemy import update
            stmt = (
                update(ExtractedData)
                .where(ExtractedData.document_id == document_id)
                .values(
                    content=content,
                    extraction_timestamp=datetime.utcnow()  # Update extraction timestamp
                )
            )
            result = await db.execute(stmt)
            return result.rowcount > 0
        except SQLAlchemyError as e:
            logger.error(f"Error updating content for ExtractedData (document {document_id}): {e}", exc_info=True)
            return False

    async def create_initial_extracted_data_async(self, db, *, document_id: uuid.UUID) -> bool:
        """Creates an initial ExtractedData record for a new document using async session."""
        try:
            from sqlalchemy import insert
            stmt = insert(ExtractedData).values(
                document_id=document_id,
                content={},  # Default to empty JSON object
                # raw_text will be populated after OCR
                # review_status defaults to PENDING_REVIEW in the model
            )
            await db.execute(stmt)
            logger.info(f"Initial ExtractedData record created for document_id: {document_id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error creating initial ExtractedData for document {document_id}: {e}", exc_info=True)
            return False

    # Add other methods as needed, e.g., delete 