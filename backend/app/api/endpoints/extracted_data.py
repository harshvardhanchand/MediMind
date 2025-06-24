import uuid
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import verify_token 
from app.models.document import Document
from app.models.extracted_data import ExtractedData, ReviewStatus
from app.repositories.document_repo import DocumentRepository
from app.repositories.extracted_data_repo import ExtractedDataRepository
from app.repositories.user_repo import user_repo 
from app.schemas.extracted_data import (
    ExtractedDataRead,
    ExtractedDataStatusUpdate,
    ExtractedDataContentUpdate,
    ExtractionDetailsResponse 
)
from app.services.selective_reprocessing_service import SelectiveReprocessingService
from app.services.auto_population_service import get_auto_population_service
from app.services.notification_service import get_notification_service, get_medical_triggers, detect_changes

router = APIRouter()
logger = logging.getLogger(__name__)


document_repo = DocumentRepository(Document)
extracted_data_repo = ExtractedDataRepository(ExtractedData) 


async def get_current_user_id_from_token(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
) -> uuid.UUID:
    supabase_id = token_data.get("sub")
    if not supabase_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token: no sub claim")
    
    user = user_repo.get_by_supabase_id_sync(db, supabase_id=supabase_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found from token")
    return user.user_id



@router.get(
    "/{document_id}",
    response_model=ExtractedDataRead,
    summary="Get Extracted Data for a Document",
    description="Retrieve the structured extracted data associated with a specific document ID."
)
async def get_extracted_data(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id_from_token),
):
    doc = document_repo.get_document(db, document_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this document's extracted data")

      
    extracted_data = extracted_data_repo.get_by_document_id(db=db, document_id=document_id)
    if not extracted_data:
       raise HTTPException(status_code=404, detail="Extracted data not found for this document")
    return extracted_data

@router.put(
    "/{document_id}/status",
    response_model=ExtractedDataRead,
    summary="Update Extracted Data Review Status",
    description="Update the review status (e.g., pending, reviewed, approved) of the extracted data for a document."
)
async def update_extracted_data_status(
    document_id: uuid.UUID,
    status_update: ExtractedDataStatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id_from_token),
):
    doc = document_repo.get_document(db, document_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this document's extracted data")

    
    updated_extracted_data = extracted_data_repo.update_review_status(
        db=db,
        document_id=document_id,
        review_status=status_update.review_status,
        reviewed_by_user_id=current_user_id # Assuming current user is the reviewer
    )
    if not updated_extracted_data:
        raise HTTPException(status_code=404, detail="Failed to update extracted data status or data not found")
    
    
    if status_update.review_status == ReviewStatus.REVIEWED_APPROVED:
        background_tasks.add_task(
            trigger_auto_population_and_analysis,
            db=db,
            user_id=current_user_id,
            document_id=document_id,
            extracted_data=updated_extracted_data
        )
        logger.info(f"Triggered auto-population for approved document {document_id}")
    
    return updated_extracted_data

@router.put(
    "/{document_id}/content",
    response_model=ExtractedDataRead,
    summary="Update Extracted Data Content",
    description="Update the structured content of the extracted data and set its status to 'reviewed_corrected'. Optionally trigger selective reprocessing for changed fields."
)
async def update_extracted_data_content(
    document_id: uuid.UUID,
    content_update: ExtractedDataContentUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id_from_token),
):
    doc = document_repo.get_document(db, document_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this document's extracted data")

    
    
    
    existing_data = extracted_data_repo.get_by_document_id(db=db, document_id=document_id)
    old_content = existing_data.content if existing_data else {}
    
    
    try:
        db.begin()
        
        updated_data = extracted_data_repo.update_structured_content(
            db=db,
            document_id=document_id,
            content=content_update.content
        )
        if not updated_data:
            db.rollback()
            raise HTTPException(status_code=404, detail="Failed to update extracted data content or data not found")

        final_updated_data = extracted_data_repo.update_review_status(
            db=db,
            document_id=document_id,
            review_status=ReviewStatus.REVIEWED_CORRECTED,
            reviewed_by_user_id=current_user_id
        )
        if not final_updated_data:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to update review status after content update")
            
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    
    if (content_update.trigger_selective_reprocessing and 
        content_update.changed_fields and 
        len(content_update.changed_fields) > 0):
        
        background_tasks.add_task(
            run_selective_reprocessing,
            db=db,
            document_id=document_id,
            changed_fields=content_update.changed_fields,
            current_content=content_update.content,
            raw_text=final_updated_data.raw_text
        )
    
    
    try:
        notification_service = get_notification_service(db)
        medical_triggers = get_medical_triggers(notification_service)
        
        
        changes = detect_changes(old_content, content_update.content)
        
       
        if changes:
            await medical_triggers.on_document_reprocessed(
                current_user_id,
                {
                    "document_id": document_id,
                    "medical_events": content_update.content,
                    "trigger_source": "user_correction"
                },
                changes,
                document_id=document_id,
                extracted_data_id=final_updated_data.extracted_data_id
            )
            logger.info(f"AI analysis triggered for document re-processing: {document_id}")
        
    except Exception as e:
        
        logger.warning(f"Failed to trigger document re-processing analysis: {str(e)}")
    
   
    background_tasks.add_task(
        trigger_auto_population_and_analysis,
        db=db,
        user_id=current_user_id,
        document_id=document_id,
        extracted_data=final_updated_data
    )
    logger.info(f"Triggered auto-population for corrected document {document_id}")

    return final_updated_data

def trigger_auto_population_and_analysis(
    db: Session,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    extracted_data: ExtractedData
):
    """Background task to trigger auto-population and AI analysis"""
    try:
        logger.info(f"Starting auto-population and analysis for document {document_id}")
        
        
        auto_population_service = get_auto_population_service(db)
        population_result = auto_population_service.populate_from_extracted_data(
            user_id=user_id,
            extracted_data=extracted_data,
            document_id=document_id
        )
        
        logger.info(f"Auto-population completed for document {document_id}: {population_result}")
        
        
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
                
                
                medical_triggers.on_document_processed(
                    user_id=user_id,
                    document_data={
                        "document_id": document_id,
                        "medical_events": extracted_data.content,
                        "auto_population_result": population_result,
                        "trigger_source": "user_approval"
                    },
                    document_id=document_id,
                    extracted_data_id=extracted_data.extracted_data_id
                )
                
                logger.info(f"AI analysis triggered successfully for document {document_id}")
                
            except Exception as ai_error:
                logger.error(f"Failed to trigger AI analysis for document {document_id}: {str(ai_error)}")
        else:
            logger.info(f"No new entries created for document {document_id}, skipping AI analysis")
            
    except Exception as e:
        logger.error(f"Auto-population and analysis failed for document {document_id}: {str(e)}")

def run_selective_reprocessing(
    db: Session,
    document_id: uuid.UUID,
    changed_fields: list,
    current_content: Any,
    raw_text: str = None
):
    """
    Background task for running selective reprocessing.
    Uses AI to suggest improvements to related fields based on user corrections.
    """
    try:
        logger.info(f"Starting selective reprocessing for document {document_id}")
        
        selective_service = SelectiveReprocessingService()
        
        
        enhanced_content = selective_service.reprocess_changed_fields(
            db=db,
            document_id=document_id,
            changed_fields=changed_fields,
            current_content=current_content,
            raw_text=raw_text
        )
        
       
        if enhanced_content != current_content:
            logger.info(f"AI suggested improvements found for document {document_id}")
            
            
            
            updated_data = extracted_data_repo.update_structured_content(
                db=db,
                document_id=document_id,
                content=enhanced_content
            )
            
            if updated_data:
                logger.info(f"Successfully applied AI suggestions for document {document_id}")
                
                
                extracted_data_repo.update_review_status(
                    db=db,
                    document_id=document_id,
                    review_status=ReviewStatus.REVIEWED_CORRECTED,
                    reviewed_by_user_id=None  
                )
            else:
                logger.warning(f"Failed to save AI suggestions for document {document_id}")
        else:
            logger.info(f"No AI improvements suggested for document {document_id}")
        
        logger.info(f"Selective reprocessing completed successfully for document {document_id}")
        
    except Exception as e:
        logger.error(f"Selective reprocessing failed for document {document_id}: {e}", exc_info=True)

@router.get(
    "/all/{document_id}",
    response_model=ExtractionDetailsResponse, 
    summary="Get Combined Document and Extraction Details",
    description="Retrieve both the document details and its associated structured extracted data."
)
async def get_extraction_details(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id_from_token),
):
    doc = document_repo.get_document(db, document_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this document's details")

    
    extracted_data = extracted_data_repo.get_by_document_id(db=db, document_id=document_id)
    if not extracted_data:
        raise HTTPException(status_code=404, detail="Extracted data not found for this document")

    
    return ExtractionDetailsResponse(document=doc, extracted_data=extracted_data)

