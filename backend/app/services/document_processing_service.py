import uuid
import logging
import json # For parsing LLM output if it's a string
from datetime import date # Import date for type checking
from sqlalchemy.orm import Session

from app.core.config import settings # For API keys and other settings
from app.db.session import SessionLocal # To create a new session for the background task
from app.models.document import Document, ProcessingStatus
from app.models.extracted_data import ExtractedData
from app.repositories.document_repo import DocumentRepository
from app.repositories.extracted_data_repo import ExtractedDataRepository
from app.utils.ai_processors import process_document_with_docai, structure_text_with_gemini
from app.utils.storage import get_gcs_uri
from app.services.auto_population_service import get_auto_population_service
from app.services.notification_service import get_notification_service, get_medical_triggers

logger = logging.getLogger(__name__)

async def run_document_processing_pipeline(document_id: uuid.UUID):
    """
    Background task to process a document through OCR and LLM structuring.
    """
    logger.info(f"Starting document processing pipeline for document_id: {document_id}")
    
    db: Session = SessionLocal() # Create a new session for this background task
    doc_repo = DocumentRepository(Document)  # Pass model class, not session
    extracted_data_repo = ExtractedDataRepository(ExtractedData)  # Now uses same pattern as DocumentRepository

    try:
        document = doc_repo.get_document(db=db, document_id=document_id)
        if not document:
            logger.error(f"Document with id {document_id} not found. Exiting pipeline.")
            db.close() # Close session before returning
            return

        # Caching Check 1: Already completed or failed
        if document.processing_status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
            logger.info(f"Document {document_id} already processed (status: {document.processing_status}). Skipping.")
            db.close() # Close session before returning
            return

        # Concurrency Check: Don't process if already processing
        if document.processing_status in [ProcessingStatus.OCR_COMPLETED, ProcessingStatus.EXTRACTION_COMPLETED, ProcessingStatus.REVIEW_REQUIRED]:
            logger.info(f"Document {document_id} is already being processed by another worker (status: {document.processing_status}). Skipping.")
            db.close()
            return

        # Caching Check 2: Already processed based on ExtractedData content (more granular if needed)
        # This might be redundant if processing_status is managed well, but can be an extra safeguard.
        # For instance, if a previous run failed after OCR but before LLM.
        existing_extracted_data = extracted_data_repo.get_by_document_id(db, document_id=document_id)
        if existing_extracted_data and existing_extracted_data.content and existing_extracted_data.content != {}: # content is not empty
             if document.processing_status != ProcessingStatus.FAILED: # If not failed, assume it's done
                logger.info(f"Document {document_id} appears to have structured content already. Status: {document.processing_status}. Skipping processing.")
                # Set to completed if not already
                if document.processing_status != ProcessingStatus.COMPLETED:
                    doc_repo.update_status(db, document_id=document_id, status=ProcessingStatus.COMPLETED)
                    logger.info(f"Document {document_id} status updated to COMPLETED.")
                db.close()
                return

        # Document starts at PENDING status, proceed with processing

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
                extracted_data_repo.update_raw_text(db, document_id=document_id, raw_text=raw_text_content)
                # Update status to OCR_COMPLETED
                doc_repo.update_status(db, document_id=document_id, status=ProcessingStatus.OCR_COMPLETED)
                logger.info(f"OCR successful for document {document_id}. Raw text stored. Status: OCR_COMPLETED")
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
             # Set to review required or completed
             doc_repo.update_status(db, document_id=document_id, status=ProcessingStatus.REVIEW_REQUIRED)
             logger.info(f"Document {document_id} status updated to REVIEW_REQUIRED after skipping LLM.")
        else:
            # Retry wrapper to prevent silent failures
            structured_json_str = None
            for attempt in range(3):
                try:
                    structured_json_str = structure_text_with_gemini(
                        api_key=settings.GEMINI_API_KEY,
                        raw_text=raw_text_content
                    )
                    break
                except Exception as exc:
                    logger.warning("Gemini structuring attempt %d/3 failed: %s", attempt+1, exc)
            else:
                logger.error(f"All Gemini structuring attempts failed for document {document_id}")
                doc_repo.update_status(db, document_id=document_id, status=ProcessingStatus.FAILED)
                db.close()
                return

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
                    extracted_data_repo.update_structured_content(db, document_id=document_id, content=medical_events)
                    # Update status to EXTRACTION_COMPLETED
                    doc_repo.update_status(db, document_id=document_id, status=ProcessingStatus.EXTRACTION_COMPLETED)
                    logger.info(f"LLM structuring successful for document {document_id}. Structured content stored. Status: EXTRACTION_COMPLETED")
                    
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

                    # 3. Auto-populate structured tables from extracted medical events
                    try:
                        logger.info(f"Starting auto-population for document {document_id}")
                        auto_population_service = get_auto_population_service(db)
                        
                        # Get the updated extracted data
                        updated_extracted_data = extracted_data_repo.get_by_document_id(db, document_id=document_id)
                        
                        if updated_extracted_data and updated_extracted_data.content:
                            # Auto-populate structured tables
                            population_result = await auto_population_service.populate_from_extracted_data(
                                user_id=str(document.user_id),
                                extracted_data=updated_extracted_data,
                                document_id=str(document_id)
                            )
                            
                            logger.info(f"Auto-population completed for document {document_id}: {population_result}")
                            
                            # If any entries were created, trigger AI analysis
                            total_created = (
                                population_result.get("medications_created", 0) +
                                population_result.get("symptoms_created", 0) +
                                population_result.get("health_readings_created", 0)
                            )
                            
                            if total_created > 0:
                                try:
                                    logger.info(f"Triggering AI analysis for {total_created} auto-populated entries")
                                    notification_service = get_notification_service(db)
                                    medical_triggers = get_medical_triggers(notification_service)
                                    
                                    # Trigger AI analysis for the document processing event
                                    await medical_triggers.on_document_processed(
                                        user_id=str(document.user_id),
                                        document_data={
                                            "document_id": str(document_id),
                                            "medical_events": medical_events,
                                            "auto_population_result": population_result
                                        },
                                        document_id=str(document_id),
                                        extracted_data_id=str(updated_extracted_data.extracted_data_id)
                                    )
                                    
                                    logger.info(f"AI analysis triggered successfully for document {document_id}")
                                    
                                except Exception as ai_error:
                                    logger.error(f"Failed to trigger AI analysis for document {document_id}: {str(ai_error)}")
                                    # Don't fail the entire pipeline for AI analysis errors
                            
                        else:
                            logger.warning(f"No extracted data found for auto-population for document {document_id}")
                            
                    except Exception as auto_pop_error:
                        logger.error(f"Auto-population failed for document {document_id}: {str(auto_pop_error)}")
                        # Don't fail the entire pipeline for auto-population errors
                        # Continue with setting status to REVIEW_REQUIRED

                    # 4. Update Document status to REVIEW_REQUIRED (requires human review)
                    doc_repo.update_status(db, document_id=document_id, status=ProcessingStatus.REVIEW_REQUIRED)
                    
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    logger.error(f"Error processing LLM JSON output for document {document_id}: {e}. Output: {structured_json_str[:500]}")
                    doc_repo.update_status(db, document_id=document_id, status=ProcessingStatus.FAILED)
            else:
                logger.error(f"LLM structuring failed for document {document_id} (no output or error in call).")
                doc_repo.update_status(db, document_id=document_id, status=ProcessingStatus.FAILED)
                db.close()
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