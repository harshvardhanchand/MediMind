"""
Selective reprocessing service for handling partial AI reprocessing of changed fields.
"""
import logging
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.repositories.extracted_data_repo import ExtractedDataRepository
from app.models.extracted_data import ExtractedData

logger = logging.getLogger(__name__)

class SelectiveReprocessingService:
    """Service for selectively reprocessing only changed fields."""
    
    def __init__(self):
        self.extracted_data_repo = ExtractedDataRepository(ExtractedData)
    
    async def reprocess_changed_fields(
        self,
        db: Session,
        document_id: str,
        changed_fields: List[Dict[str, Any]],
        current_content: Any,
        raw_text: Optional[str] = None
    ) -> Any:
        """
        Reprocess only the fields that were changed by the user.
        
        For now, this is a simplified implementation that logs the changes
        and returns the current content. This can be enhanced later with
        actual AI reprocessing.
        
        Args:
            db: Database session
            document_id: ID of the document
            changed_fields: List of fields that were changed
            current_content: Current content with user corrections
            raw_text: Original OCR text for context
            
        Returns:
            Updated content (currently just returns current_content)
        """
        try:
            logger.info(f"Selective reprocessing requested for document {document_id}")
            logger.info(f"Number of changed fields: {len(changed_fields)}")
            
            # Log the changes for monitoring and future enhancement
            for change in changed_fields:
                logger.info(f"Changed field: {change.get('section')}.{change.get('field')} "
                          f"from '{change.get('oldValue')}' to '{change.get('newValue')}'")
            
            # For now, just return the current content
            # TODO: Implement actual AI reprocessing here
            # This could involve:
            # 1. Grouping changes by section
            # 2. Extracting relevant context from raw_text
            # 3. Using focused AI prompts for each section
            # 4. Merging results back into the content
            
            logger.info(f"Selective reprocessing completed (simplified) for document {document_id}")
            return current_content
            
        except Exception as e:
            logger.error(f"Error in selective reprocessing for document {document_id}: {e}", exc_info=True)
            # Return original content if reprocessing fails
            return current_content 