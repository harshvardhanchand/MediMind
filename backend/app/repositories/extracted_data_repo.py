"""
Repository for CRUD operations on ExtractedData entities.
"""
import uuid
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session # Changed back from AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.models.extracted_data import ExtractedData, ReviewStatus


logger = logging.getLogger(__name__)

class ExtractedDataRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_initial_extracted_data(self, document_id: uuid.UUID) -> Optional[ExtractedData]:
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
            self.db.add(db_extracted_data)
            self.db.commit()
            self.db.refresh(db_extracted_data)
            logger.info(f"Initial ExtractedData record created for document_id: {document_id}")
            return db_extracted_data
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating initial ExtractedData for document {document_id}: {e}", exc_info=True)
            return None

    def get_by_document_id(self, document_id: uuid.UUID) -> Optional[ExtractedData]:
        """Retrieves an ExtractedData record by its associated document_id."""
        try:
            # Using query for sync session
            return self.db.query(ExtractedData).filter(ExtractedData.document_id == document_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving ExtractedData for document {document_id}: {e}", exc_info=True)
            return None

    def update_raw_text(self, document_id: uuid.UUID, raw_text: str) -> Optional[ExtractedData]:
        """Updates the raw_text field of an ExtractedData record."""
        db_extracted_data = self.get_by_document_id(document_id)
        if db_extracted_data:
            try:
                db_extracted_data.raw_text = raw_text
                self.db.commit()
                self.db.refresh(db_extracted_data)
                logger.info(f"Updated raw_text for ExtractedData linked to document_id: {document_id}")
                return db_extracted_data
            except SQLAlchemyError as e:
                self.db.rollback()
                logger.error(f"Error updating raw_text for ExtractedData (document {document_id}): {e}", exc_info=True)
                return None
        return None

    def update_structured_content(self, document_id: uuid.UUID, content: Dict[str, Any]) -> Optional[ExtractedData]:
        """Updates the structured content field of an ExtractedData record."""
        db_extracted_data = self.get_by_document_id(document_id)
        if db_extracted_data:
            try:
                db_extracted_data.content = content
                # Potentially update extraction_timestamp here if desired
                self.db.commit()
                self.db.refresh(db_extracted_data)
                logger.info(f"Updated structured content for ExtractedData linked to document_id: {document_id}")
                return db_extracted_data
            except SQLAlchemyError as e:
                self.db.rollback()
                logger.error(f"Error updating content for ExtractedData (document {document_id}): {e}", exc_info=True)
                return None
        return None

    def update_review_status(
        self,
        document_id: uuid.UUID,
        review_status: ReviewStatus,
        reviewed_by_user_id: Optional[uuid.UUID] = None
    ) -> Optional[ExtractedData]:
        """Updates the review_status and related fields of an ExtractedData record."""
        db_extracted_data = self.get_by_document_id(document_id)
        if db_extracted_data:
            try:
                db_extracted_data.review_status = review_status
                if reviewed_by_user_id:
                    db_extracted_data.reviewed_by_user_id = reviewed_by_user_id
                # review_timestamp could be set here to datetime.utcnow()
                self.db.commit()
                self.db.refresh(db_extracted_data)
                logger.info(f"Updated review_status to {review_status} for ExtractedData (document {document_id})")
                return db_extracted_data
            except SQLAlchemyError as e:
                self.db.rollback()
                logger.error(f"Error updating review_status for ExtractedData (document {document_id}): {e}", exc_info=True)
                return None
        return None

    # Add other methods as needed, e.g., delete 