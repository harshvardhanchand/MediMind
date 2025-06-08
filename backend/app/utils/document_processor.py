import logging
import uuid
from datetime import datetime
from typing import Optional

from app.utils.ai_processors import process_document_with_docai, structure_text_with_gemini
from app.utils.storage import get_gcs_uri
from app.models.document import Document, ProcessingStatus
from app.models.extracted_data import ExtractedData
from app.repositories.document_repo import DocumentRepository
from app.repositories.extracted_data_repo import ExtractedDataRepository
from app.core.config import settings

logger = logging.getLogger(__name__)

def process_document_background(
    document_id: uuid.UUID,
    db_session,
    project_id: str = settings.GCP_PROJECT_ID,
    doc_ai_location: str = settings.DOC_AI_LOCATION,
    doc_ai_processor_id: str = settings.DOC_AI_PROCESSOR_ID,
    gemini_api_key: str = settings.GEMINI_API_KEY
) -> None:
    """
    Process document in the background using OCR and LLM.
    This function is designed to be run as a background task.
    
    Args:
        document_id: UUID of the document to process
        db_session: SQLAlchemy database session
        project_id: GCP project ID
        doc_ai_location: Document AI processor location
        doc_ai_processor_id: Document AI processor ID
        gemini_api_key: API key for Gemini AI
    """
    try:
        # 1. Get document from database
        doc_repo = DocumentRepository(Document)
        document = doc_repo.get_document(db=db_session, document_id=document_id)
        
        if not document:
            logger.error(f"Document not found: {document_id}")
            return
        
        # 2. Document starts at PENDING, proceed with processing
        
        # 3. Get GCS URI for the document
        gcs_uri = get_gcs_uri(document.storage_path)
        if not gcs_uri:
            logger.error(f"Failed to generate GCS URI for document: {document_id}")
            doc_repo.update_status(db=db_session, document_id=document_id, status=ProcessingStatus.FAILED)
            return
        
        # 4. Process document with Document AI
        logger.info(f"Processing document with Document AI: {document_id}")
        processed_document = process_document_with_docai(
            project_id=project_id,
            location=doc_ai_location,
            processor_id=doc_ai_processor_id,
            gcs_uri=gcs_uri,
            mime_type=document.mime_type
        )
        
        if not processed_document or not processed_document.text:
            logger.error(f"Document AI processing failed for document: {document_id}")
            doc_repo.update_status(db=db_session, document_id=document_id, status=ProcessingStatus.FAILED)
            return
        
        # 5. Store raw text in ExtractedData
        extracted_data_repo = ExtractedDataRepository(ExtractedData)
        
        # Check if an ExtractedData record already exists
        extracted_data = extracted_data_repo.get_by_document_id(db=db_session, document_id=document_id)
        if not extracted_data:
            # Create initial record with empty content
            extracted_data = extracted_data_repo.create_initial_extracted_data(db=db_session, document_id=document_id)
            if not extracted_data:
                logger.error(f"Failed to create ExtractedData record for document: {document_id}")
                doc_repo.update_status(db=db_session, document_id=document_id, status=ProcessingStatus.FAILED)
                return
        
        # Update with OCR text and set status to OCR_COMPLETED
        extracted_data_repo.update_raw_text(db=db_session, document_id=document_id, raw_text=processed_document.text)
        doc_repo.update_status(db=db_session, document_id=document_id, status=ProcessingStatus.OCR_COMPLETED)
        
        # 6. Process text with Gemini LLM
        logger.info(f"Processing OCR text with Gemini AI: {document_id}")
        
        # Retry wrapper to prevent silent failures
        structured_json = None
        for attempt in range(3):
            try:
                structured_json = structure_text_with_gemini(
                    api_key=gemini_api_key,
                    raw_text=processed_document.text
                )
                break
            except Exception as exc:
                logger.warning("Gemini structuring attempt %d/3 failed: %s", attempt+1, exc)
        else:
            logger.error(f"All Gemini structuring attempts failed for document {document_id}")
            doc_repo.update_status(db=db_session, document_id=document_id, status=ProcessingStatus.FAILED)
            return
        
        if not structured_json:
            logger.error(f"Gemini AI processing failed for document: {document_id}")
            doc_repo.update_status(db=db_session, document_id=document_id, status=ProcessingStatus.FAILED)
            return
        
        # 7. Parse and store structured JSON
        try:
            import json
            structured_content = json.loads(structured_json)
            extracted_data_repo.update_structured_content(db=db_session, document_id=document_id, content=structured_content)
            
            # 8. Update document status to REVIEW_REQUIRED
            doc_repo.update_status(db=db_session, document_id=document_id, status=ProcessingStatus.REVIEW_REQUIRED)
            logger.info(f"Document processing completed successfully: {document_id}")
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse structured JSON for document {document_id}: {e}")
            doc_repo.update_status(db=db_session, document_id=document_id, status=ProcessingStatus.FAILED)
            
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}", exc_info=True)
        try:
            # Try to update document status if possible
            doc_repo = DocumentRepository(Document)
            doc_repo.update_status(db=db_session, document_id=document_id, status=ProcessingStatus.FAILED)
        except Exception:
            pass  # If this fails too, just continue 