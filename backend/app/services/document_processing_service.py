import uuid
import logging
import json # For parsing LLM output if it's a string
from datetime import date # Import date for type checking
from sqlalchemy.orm import Session

from app.core.config import settings # For API keys and other settings
from app.db.session import SessionLocal # To create a new session for the background task
from app.models.document import  ProcessingStatus
from app.repositories.document_repo import DocumentRepository
from app.repositories.extracted_data_repo import ExtractedDataRepository
from app.utils.ai_processors import process_document_with_docai, structure_text_with_gemini
from app.utils.storage import get_gcs_uri

logger = logging.getLogger(__name__)

def run_document_processing_pipeline(document_id: uuid.UUID):
    """
    Background task to process a document through OCR and LLM structuring.
    """
    logger.info(f"Starting document processing pipeline for document_id: {document_id}")
    
    db: Session = SessionLocal() # Create a new session for this background task
    doc_repo = DocumentRepository(db)
    extracted_data_repo = ExtractedDataRepository(db)

    try:
        document = doc_repo.get_document(db=db, document_id=document_id)
        if not document:
            logger.error(f"Document with id {document_id} not found. Exiting pipeline.")
            db.close() # Close session before returning
            return

        # Caching Check 1: Already completed or in review
        if document.processing_status in [ProcessingStatus.COMPLETED, ProcessingStatus.REVIEW_REQUIRED]:
            logger.info(f"Document {document_id} already processed (status: {document.processing_status}). Skipping.")
            db.close() # Close session before returning
            return

        # Caching Check 2: Already processed based on ExtractedData content (more granular if needed)
        # This might be redundant if processing_status is managed well, but can be an extra safeguard.
        # For instance, if a previous run failed after OCR but before LLM.
        existing_extracted_data = extracted_data_repo.get_by_document_id(document_id)
        if existing_extracted_data and existing_extracted_data.content and existing_extracted_data.content != {}: # content is not empty
             if document.processing_status != ProcessingStatus.FAILED: # If not failed, assume it's done or in review
                logger.info(f"Document {document_id} appears to have structured content already. Status: {document.processing_status}. Skipping LLM if applicable.")
                # Potentially skip only the LLM part if raw_text is also present and status indicates OCR done.
                # For now, assume we proceed but skip LLM step later

        doc_repo.update_status(db, document_id=document_id, status=ProcessingStatus.PROCESSING)
        logger.info(f"Document {document_id} status updated to PROCESSING.")

        # --- OCR Step ---
        raw_text_content = None
        if not (existing_extracted_data and existing_extracted_data.raw_text):
            logger.info(f"Performing OCR for document {document_id}...")
            # Ensure all necessary GCS/DocumentAI configs are loaded via settings
            doc_ai_result = process_document_with_docai(
                project_id=settings.GCP_PROJECT_ID,
                location=settings.DOCUMENT_AI_PROCESSOR_LOCATION,
                processor_id=settings.DOCUMENT_AI_PROCESSOR_ID,
                gcs_uri=document.storage_path, # Assuming storage_path is the GCS URI
                mime_type=document.file_metadata.get("content_type", "application/pdf") if document.file_metadata else "application/pdf"
            )

            if doc_ai_result and doc_ai_result.text:
                raw_text_content = doc_ai_result.text
                extracted_data_repo.update_raw_text(document_id, raw_text_content)
                logger.info(f"OCR successful for document {document_id}. Raw text stored.")
                # Optionally update status to an intermediate one like 'OCR_COMPLETED'
                # doc_repo.update_status(document_id, ProcessingStatus.OCR_COMPLETED) 
            else:
                logger.error(f"OCR processing failed for document {document_id}.")
                doc_repo.update_status(db, document_id=document_id, status=ProcessingStatus.FAILED)
                db.close() # Close session before returning
                return
        else:
            logger.info(f"Raw text already exists for document {document_id}. Skipping OCR.")
            raw_text_content = existing_extracted_data.raw_text
        
        if not raw_text_content:
            logger.error(f"No raw text available for document {document_id} after OCR step. Exiting LLM processing.")
            doc_repo.update_status(db, document_id=document_id, status=ProcessingStatus.FAILED)
            db.close() # Close session before returning
            return

        # --- LLM Structuring Step ---
        logger.info(f"Performing LLM structuring for document {document_id}...")
        
        # Caching: Check if content is already richly populated (not just '{}')
        if existing_extracted_data and existing_extracted_data.content and existing_extracted_data.content != {}:
             logger.info(f"Structured content already exists for document {document_id}. Skipping LLM structuring.")
             # If skipping LLM, ensure final status is set correctly if it wasn't already
             if document.processing_status != ProcessingStatus.REVIEW_REQUIRED and document.processing_status != ProcessingStatus.COMPLETED:
                 doc_repo.update_status(db, document_id=document_id, status=ProcessingStatus.REVIEW_REQUIRED)
                 logger.info(f"Document {document_id} status updated to REVIEW_REQUIRED after skipping LLM.")
        else:
            structured_json_str = structure_text_with_gemini(
                api_key=settings.GEMINI_API_KEY,
                raw_text=raw_text_content
            )

            if structured_json_str:
                try:
                    # Parse the full JSON output from the LLM
                    llm_output = json.loads(structured_json_str)
                    
                    # Extract the two main parts
                    medical_events = llm_output.get("medical_events")
                    extracted_metadata = llm_output.get("extracted_metadata")

                    if not isinstance(medical_events, list):
                        logger.error(f"LLM output 'medical_events' is not a list for document {document_id}. Output: {medical_events}")
                        raise ValueError("Invalid format for medical_events")
                    if not isinstance(extracted_metadata, dict):
                        logger.error(f"LLM output 'extracted_metadata' is not a dict for document {document_id}. Output: {extracted_metadata}")
                        # Allow processing to continue without metadata if events are valid
                        extracted_metadata = {} # Default to empty dict
                        
                    # 1. Update ExtractedData content
                    extracted_data_repo.update_structured_content(document_id, medical_events)
                    logger.info(f"LLM structuring successful for document {document_id}. Structured content stored.")
                    
                    # 2. Update Document metadata (if any extracted)
                    if extracted_metadata:
                        # Prepare metadata update dictionary, converting date string if present
                        metadata_to_update = {}
                        if extracted_metadata.get("document_date"):
                            try:
                                metadata_to_update["document_date"] = date.fromisoformat(extracted_metadata["document_date"])
                            except (ValueError, TypeError):
                                logger.warning(f"Could not parse document_date '{extracted_metadata['document_date']}' from LLM for doc {document_id}")
                        
                        # Add other fields directly if they exist and are not None
                        for key in ["source_name", "source_location_city", "tags", "related_to_health_goal_or_episode"]:
                            if extracted_metadata.get(key) is not None:
                                metadata_to_update[key] = extracted_metadata[key]
                        
                        if metadata_to_update:
                            logger.info(f"Attempting to update Document metadata for {document_id}: {metadata_to_update}")
                            # Replace the placeholder pass with the actual repository call
                            updated_doc = doc_repo.update_metadata(db, document_id=document_id, metadata_updates=metadata_to_update)
                            if not updated_doc:
                                logger.error(f"Failed to update document metadata in repository for document {document_id}")
                                # Decide if this is critical enough to mark the whole process as failed, 
                                # or just log the warning and continue (as metadata update might be non-critical)
                                # For now, log error and continue with setting status to REVIEW_REQUIRED

                    # 3. Update Document status
                    doc_repo.update_status(db, document_id=document_id, status=ProcessingStatus.REVIEW_REQUIRED)
                    
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    logger.error(f"Error processing LLM JSON output for document {document_id}: {e}. Output: {structured_json_str[:500]}")
                    doc_repo.update_status(db, document_id=document_id, status=ProcessingStatus.FAILED)
            else:
                logger.error(f"LLM structuring failed for document {document_id} (no output or error in call).")
                doc_repo.update_status(db, document_id=document_id, status=ProcessingStatus.FAILED)
                db.close() # Close session before returning
                return
        
        logger.info(f"Document processing pipeline completed for document_id: {document_id}")

    except Exception as e:
        logger.error(f"Unhandled exception in processing pipeline for document {document_id}: {e}", exc_info=True)
        # Attempt to set status to FAILED if possible
        try:
            # Pass db session to repo methods
            doc_repo.update_status(db, document_id=document_id, status=ProcessingStatus.FAILED)
        except Exception as inner_e:
            logger.error(f"Additionally failed to update document status to FAILED for {document_id}: {inner_e}", exc_info=True)
    finally:
        db.close()
        logger.info(f"Database session closed for document_id: {document_id} processing.")

# Note: Ensure DocumentRepository has get_by_id and update_status methods.
# Ensure settings in app.core.config correctly load:
# GOOGLE_CLOUD_PROJECT, DOCUMENT_AI_PROCESSOR_LOCATION, DOCUMENT_AI_PROCESSOR_ID, GEMINI_API_KEY
# Assumed Document model has file_metadata JSON field with content_type.
# Assumed Document model ProcessingStatus enum includes: PENDING, PROCESSING, REVIEW_REQUIRED, COMPLETED, FAILED
# (and potentially OCR_COMPLETED if more granular status is desired) 