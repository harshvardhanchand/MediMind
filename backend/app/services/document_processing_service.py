import uuid
import logging
import json
import asyncio
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import DocumentProcessingError, ErrorCode
from app.db.session import SessionLocal, AsyncSessionLocal
from app.models.document import Document, ProcessingStatus
from app.models.extracted_data import ExtractedData
from app.repositories.document_repo import DocumentRepository
from app.repositories.extracted_data_repo import ExtractedDataRepository
from app.utils.ai_processors import process_document_with_docai, structure_text_with_gemini
from app.services.auto_population_service import get_auto_population_service
from app.services.notification_service import get_notification_service, get_medical_triggers
from app.middleware.performance import track_database_query

logger = logging.getLogger(__name__)

async def run_document_processing_pipeline(document_id: uuid.UUID):
    """
    Fully async background task to process a document through OCR and LLM structuring.
    
    This function is now properly async and uses async database sessions for better performance.
    """
    logger.info(f"Starting document processing pipeline for document_id: {document_id}")
    
    # Use async database session for better performance
    if not AsyncSessionLocal:
        logger.error("Async database session not configured, falling back to sync processing")
        await run_document_processing_pipeline_sync(document_id)
        return
    
    async with AsyncSessionLocal() as db:
        doc_repo = DocumentRepository(Document)
        extracted_data_repo = ExtractedDataRepository(ExtractedData)

        try:
            # Get document with row-level locking to prevent race conditions
            with track_database_query("select", "documents", str(document_id)):
                # Use SELECT FOR UPDATE to lock the row
                document = await doc_repo.get_document_with_lock_async(db=db, document_id=document_id)
            
            if not document:
                raise DocumentProcessingError(
                    f"Document with id {document_id} not found",
                    document_id=str(document_id),
                    processing_stage="initialization"
                )

            # Early exit conditions - avoid processing if already completed or failed
            if document.processing_status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
                logger.info(f"Document {document_id} already processed (status: {document.processing_status}). Skipping.")
                return

            # Race condition protection - check if another worker is processing
            if document.processing_status == ProcessingStatus.PROCESSING:
                logger.info(f"Document {document_id} is already being processed by another worker. Skipping.")
                return

            # Set status to PROCESSING immediately to prevent race conditions
            await doc_repo.update_status_async(db, document_id=document_id, status=ProcessingStatus.PROCESSING)
            await db.commit()
            logger.info(f"Document {document_id} status set to PROCESSING")

            # Check for existing extracted data to avoid redundant processing
            with track_database_query("select", "extracted_data", str(document_id)):
                existing_extracted_data = await extracted_data_repo.get_by_document_id_async(
                    db, document_id=document_id
                )
            
            # If we have complete structured content, mark as completed
            if existing_extracted_data and existing_extracted_data.content and existing_extracted_data.content != {}:
                logger.info(f"Document {document_id} has structured content. Setting to completed.")
                await doc_repo.update_status_async(db, document_id=document_id, status=ProcessingStatus.COMPLETED)
                await db.commit()
                return

            # Determine which stage to start from based on existing data
            raw_text_content = None
            
            # === OCR Processing Stage (if needed) ===
            if not existing_extracted_data or not existing_extracted_data.raw_text:
                logger.info(f"Starting OCR stage for document {document_id}")
                raw_text_content = await process_ocr_stage(
                    db, doc_repo, extracted_data_repo, document, existing_extracted_data
                )
                
                if not raw_text_content:
                    await doc_repo.update_status_async(db, document_id=document_id, status=ProcessingStatus.FAILED)
                    await db.commit()
                    raise DocumentProcessingError(
                        "OCR processing failed - no text extracted",
                        document_id=str(document_id),
                        processing_stage="ocr",
                        error_code=ErrorCode.OCR_PROCESSING_FAILED
                    )
            else:
                # Use existing raw text
                raw_text_content = existing_extracted_data.raw_text
                logger.info(f"Using existing raw text for document {document_id}")

            # === LLM Structuring Stage (if needed) ===
            if not existing_extracted_data or not existing_extracted_data.content or existing_extracted_data.content == {}:
                logger.info(f"Starting LLM structuring stage for document {document_id}")
                await process_llm_structuring_stage(
                    db, doc_repo, extracted_data_repo, document, raw_text_content
                )
            else:
                logger.info(f"Using existing structured content for document {document_id}")

            # === Auto-population Stage ===
            logger.info(f"Starting auto-population stage for document {document_id}")
            await process_auto_population_stage(db, document, extracted_data_repo)

            # Mark as completed
            await doc_repo.update_status_async(db, document_id=document_id, status=ProcessingStatus.COMPLETED)
            await db.commit()
            
            logger.info(f"Document processing pipeline completed successfully for document {document_id}")

        except DocumentProcessingError as e:
            await db.rollback()
            # Ensure failed documents are marked as FAILED
            try:
                await doc_repo.update_status_async(db, document_id=document_id, status=ProcessingStatus.FAILED)
                await db.commit()
                logger.error(f"Document {document_id} marked as FAILED due to processing error: {str(e)}")
            except Exception as status_update_error:
                logger.error(f"Failed to update status to FAILED for document {document_id}: {status_update_error}")
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Unexpected error in document processing pipeline: {str(e)}", exc_info=True)
            # Ensure failed documents are marked as FAILED
            try:
                await doc_repo.update_status_async(db, document_id=document_id, status=ProcessingStatus.FAILED)
                await db.commit()
                logger.error(f"Document {document_id} marked as FAILED due to unexpected error")
            except Exception as status_update_error:
                logger.error(f"Failed to update status to FAILED for document {document_id}: {status_update_error}")
            raise DocumentProcessingError(
                f"Document processing failed: {str(e)}",
                document_id=str(document_id),
                processing_stage="unknown"
            )

async def process_ocr_stage(
    db: AsyncSession, 
    doc_repo: DocumentRepository, 
    extracted_data_repo: ExtractedDataRepository,
    document: Document, 
    existing_extracted_data: ExtractedData
) -> str:
    """Process OCR stage with proper error handling and caching."""
    
    # Check if raw text already exists (caching)
    if existing_extracted_data and existing_extracted_data.raw_text and existing_extracted_data.raw_text.strip():
        logger.info(f"Raw text already exists for document {document.document_id}. Skipping OCR.")
        return existing_extracted_data.raw_text

    logger.info(f"Performing OCR for document {document.document_id}...")
    
    try:
        # OCR processing - this is CPU intensive, so we run it in executor
        loop = asyncio.get_event_loop()
        doc_ai_result = await loop.run_in_executor(
            None,
            process_document_with_docai,
            settings.GCP_PROJECT_ID,
            settings.DOCUMENT_AI_PROCESSOR_LOCATION,
            settings.DOCUMENT_AI_PROCESSOR_ID,
            document.storage_path,
            document.file_metadata.get("content_type", "application/pdf") if document.file_metadata else "application/pdf"
        )

        if not doc_ai_result or not doc_ai_result.text:
            raise DocumentProcessingError(
                "OCR processing returned empty result",
                document_id=str(document.document_id),
                processing_stage="ocr",
                error_code=ErrorCode.OCR_PROCESSING_FAILED
            )

        raw_text_content = doc_ai_result.text
        
        # Store raw text with performance tracking
        with track_database_query("update", "extracted_data", str(document.document_id)):
            # Ensure extracted data record exists
            if not existing_extracted_data:
                await extracted_data_repo.create_initial_extracted_data_async(
                    db, document_id=document.document_id
                )
            
            await extracted_data_repo.update_raw_text_async(
                db, document_id=document.document_id, raw_text=raw_text_content
            )
        
        # Update document status
        await doc_repo.update_status_async(
            db, document_id=document.document_id, status=ProcessingStatus.OCR_COMPLETED
        )
        
        await db.commit()
        logger.info(f"OCR successful for document {document.document_id}")
        return raw_text_content

    except Exception as e:
        logger.error(f"OCR processing failed for document {document.document_id}: {str(e)}", exc_info=True)
        # Mark document as failed on OCR errors
        await doc_repo.update_status_async(
            db, document_id=document.document_id, status=ProcessingStatus.FAILED
        )
        await db.commit()
        raise DocumentProcessingError(
            f"OCR processing failed: {str(e)}",
            document_id=str(document.document_id),
            processing_stage="ocr",
            error_code=ErrorCode.OCR_PROCESSING_FAILED
        )

async def process_llm_structuring_stage(
    db: AsyncSession,
    doc_repo: DocumentRepository,
    extracted_data_repo: ExtractedDataRepository,
    document: Document,
    raw_text_content: str
):
    """Process LLM structuring stage with retry logic and proper error handling."""
    
    logger.info(f"Performing LLM structuring for document {document.document_id}...")
    
    # Check if structured content already exists
    existing_data = await extracted_data_repo.get_by_document_id_async(db, document_id=document.document_id)
    if existing_data and existing_data.content and existing_data.content != {}:
        logger.info(f"Structured content already exists for document {document.document_id}. Skipping LLM.")
        await doc_repo.update_status_async(
            db, document_id=document.document_id, status=ProcessingStatus.REVIEW_REQUIRED
        )
        return

    # LLM processing with retry logic
    structured_json_str = None
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Run LLM processing in executor to avoid blocking
            loop = asyncio.get_event_loop()
            structured_json_str = await loop.run_in_executor(
                None,
                structure_text_with_gemini,
                settings.GEMINI_API_KEY,
                raw_text_content
            )
            
            if structured_json_str:
                break
                
        except Exception as exc:
            logger.warning(f"Gemini structuring attempt {attempt+1}/{max_retries} failed: {exc}")
            if attempt == max_retries - 1:  # Last attempt
                raise DocumentProcessingError(
                    f"All LLM structuring attempts failed. Last error: {exc}",
                    document_id=str(document.document_id),
                    processing_stage="llm_structuring",
                    error_code=ErrorCode.LLM_PROCESSING_FAILED
                )
            
            # Exponential backoff
            await asyncio.sleep(2 ** attempt)

    if not structured_json_str:
        raise DocumentProcessingError(
            "LLM structuring returned empty result",
            document_id=str(document.document_id),
            processing_stage="llm_structuring",
            error_code=ErrorCode.LLM_PROCESSING_FAILED
        )

    # Parse and store structured data
    try:
        llm_output = json.loads(structured_json_str)
        medical_events = llm_output.get("medical_events")
        extracted_metadata = llm_output.get("extracted_metadata")

        if not isinstance(medical_events, list):
            raise ValueError("Invalid format for medical_events - expected list")
        
        if not isinstance(extracted_metadata, dict):
            logger.warning(f"Invalid metadata format for document {document.document_id}, using empty dict")
            extracted_metadata = {}

        # Update structured content
        with track_database_query("update", "extracted_data", str(document.document_id)):
            await extracted_data_repo.update_structured_content_async(
                db, document_id=document.document_id, content=medical_events
            )

        # Update document status
        await doc_repo.update_status_async(
            db, document_id=document.document_id, status=ProcessingStatus.EXTRACTION_COMPLETED
        )

        # Update document metadata if available
        if extracted_metadata:
            await update_document_metadata(db, doc_repo, document.document_id, extracted_metadata)

        await db.commit()
        logger.info(f"LLM structuring successful for document {document.document_id}")

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse LLM output for document {document.document_id}: {str(e)}")
        # Mark document as failed on parse errors
        await doc_repo.update_status_async(
            db, document_id=document.document_id, status=ProcessingStatus.FAILED
        )
        await db.commit()
        raise DocumentProcessingError(
            f"Failed to parse LLM output: {str(e)}",
            document_id=str(document.document_id),
            processing_stage="llm_parsing",
            error_code=ErrorCode.LLM_PROCESSING_FAILED
        )

async def update_document_metadata(
    db: AsyncSession, 
    doc_repo: DocumentRepository, 
    document_id: uuid.UUID, 
    extracted_metadata: dict
):
    """Update document metadata from LLM extraction."""
    
    metadata_to_update = {}
    
    # Parse date if available
    if extracted_metadata.get("document_date"):
        try:
            metadata_to_update["document_date"] = date.fromisoformat(extracted_metadata["document_date"])
        except (ValueError, TypeError):
            logger.warning(f"Could not parse document_date '{extracted_metadata['document_date']}' for doc {document_id}")
    
    # Add other metadata fields
    for key in ["source_name", "source_location_city", "tags", "related_to_health_goal_or_episode"]:
        if extracted_metadata.get(key) is not None:
            metadata_to_update[key] = extracted_metadata[key]
    
    if metadata_to_update:
        try:
            await doc_repo.update_metadata_async(db, document_id=document_id, metadata_updates=metadata_to_update)
            logger.info(f"Updated document metadata for {document_id}: {list(metadata_to_update.keys())}")
        except Exception as e:
            logger.error(f"Failed to update document metadata for {document_id}: {str(e)}")

async def process_auto_population_stage(
    db: AsyncSession, 
    document: Document, 
    extracted_data_repo: ExtractedDataRepository
):
    """Process auto-population stage with proper error handling."""
    
    try:
        logger.info(f"Starting auto-population for document {document.document_id}")
        
        # Get auto-population service (this might need to be made async too)
        auto_population_service = get_auto_population_service(db)
        
        # Get updated extracted data
        updated_extracted_data = await extracted_data_repo.get_by_document_id_async(
            db, document_id=document.document_id
        )
        
        if updated_extracted_data and updated_extracted_data.content:
            # Run auto-population
            population_result = await auto_population_service.populate_from_extracted_data(
                user_id=str(document.user_id),
                extracted_data=updated_extracted_data,
                document_id=str(document.document_id)
            )
            
            logger.info(f"Auto-population completed for document {document.document_id}: {population_result}")
            
            # Trigger medical analysis if entries were created
            total_created = (
                population_result.get("medications_created", 0) +
                population_result.get("symptoms_created", 0) +
                population_result.get("health_readings_created", 0)
            )
            
            if total_created > 0:
                await trigger_medical_analysis(db, document, population_result)
                
        else:
            logger.warning(f"No extracted data available for auto-population for document {document.document_id}")
            
    except Exception as e:
        # Don't fail the entire pipeline for auto-population errors
        logger.error(f"Auto-population failed for document {document.document_id}: {str(e)}", exc_info=True)

async def trigger_medical_analysis(db: AsyncSession, document: Document, population_result: dict):
    """Trigger medical analysis after successful auto-population."""
    
    try:
        notification_service = get_notification_service(db)
        medical_triggers = get_medical_triggers(notification_service)
        
        # Trigger document processed event
        document_data = {
            "document_type": document.document_type.value if document.document_type else "unknown",
            "filename": document.original_filename,
            "created_entries": population_result
        }
        
        await medical_triggers.on_document_processed(
            str(document.user_id),
            document_data,
            str(document.document_id)
        )
        
        logger.info(f"Medical analysis triggered for document {document.document_id}")
        
    except Exception as e:
        # Don't fail the pipeline for analysis trigger errors
        logger.warning(f"Failed to trigger medical analysis for document {document.document_id}: {str(e)}")

# Fallback sync version for compatibility
async def run_document_processing_pipeline_sync(document_id: uuid.UUID):
    """
    DEPRECATED: This function is removed due to async/sync mixing issues.
    Use the main async pipeline instead.
    """
    logger.error(f"Sync fallback called for document {document_id} - this should not happen")
    raise DocumentProcessingError(
        "Sync processing fallback is not supported. Please configure async database session.",
        document_id=str(document_id),
        processing_stage="initialization"
    )
