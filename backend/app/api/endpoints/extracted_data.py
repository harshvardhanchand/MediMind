import uuid
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import verify_token # For token verification
from app.models.document import Document
from app.models.extracted_data import ExtractedData, ReviewStatus
from app.models.user import User
from app.repositories.document_repo import document_repo # Singleton repository
from app.repositories.extracted_data_repo import ExtractedDataRepository # Needs instantiation
from app.repositories.user_repo import user_repo # Singleton repository
from app.schemas.document import DocumentRead # For combined details response
from app.schemas.extracted_data import (
    ExtractedDataRead,
    ExtractedDataStatusUpdate,
    ExtractedDataContentUpdate,
    ExtractionDetailsResponse # Added import for the new schema
)
from app.services.selective_reprocessing_service import SelectiveReprocessingService

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper function to get user_id from token
# Based on unit tests and architecture document example
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

# Placeholder for the combined response schema, assuming it might be defined in app.schemas.extracted_data
# If not, it should be added there. For this edit, we'll use a type alias.
# class ExtractionDetailsResponse(ExtractedDataRead): # Simplified for now, proper schema needed
#     document: DocumentRead # Removed this inline class definition

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

    extracted_data_repo = ExtractedDataRepository(ExtractedData)  # Pass model class
    extracted_data = extracted_data_repo.get_by_document_id(db=db, document_id=document_id)
    if not extracted_data:
        # Check if document exists but extracted_data is missing (should ideally be created with document)
        # For robustness, we can create an initial one if missing, or return 404.
        # Based on ExtractedDataRepository, it has create_initial_extracted_data
        # However, the tests imply it should exist if the document exists for this endpoint.
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
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id_from_token),
):
    doc = document_repo.get_document(db, document_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this document's extracted data")

    extracted_data_repo = ExtractedDataRepository(ExtractedData)  # Pass model class
    # The repository's update_review_status expects document_id, status, and user_id
    updated_extracted_data = extracted_data_repo.update_review_status(
        db=db,
        document_id=document_id,
        review_status=status_update.review_status,
        reviewed_by_user_id=current_user_id # Assuming current user is the reviewer
    )
    if not updated_extracted_data:
        raise HTTPException(status_code=404, detail="Failed to update extracted data status or data not found")
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

    extracted_data_repo = ExtractedDataRepository(ExtractedData)  # Pass model class
    
    # Update content
    updated_data = extracted_data_repo.update_structured_content(
        db=db,
        document_id=document_id,
        content=content_update.content
    )
    if not updated_data:
        raise HTTPException(status_code=404, detail="Failed to update extracted data content or data not found")

    # Set status to REVIEWED_CORRECTED as per test logic
    final_updated_data = extracted_data_repo.update_review_status(
        db=db,
        document_id=document_id,
        review_status=ReviewStatus.REVIEWED_CORRECTED,
        reviewed_by_user_id=current_user_id
    )
    if not final_updated_data:
        raise HTTPException(status_code=500, detail="Failed to update review status after content update")

    # Trigger selective reprocessing if requested and there are changed fields
    if (content_update.trigger_selective_reprocessing and 
        content_update.changed_fields and 
        len(content_update.changed_fields) > 0):
        
        background_tasks.add_task(
            run_selective_reprocessing,
            db=db,
            document_id=str(document_id),
            changed_fields=content_update.changed_fields,
            current_content=content_update.content,
            raw_text=final_updated_data.raw_text
        )

    return final_updated_data

async def run_selective_reprocessing(
    db: Session,
    document_id: str,
    changed_fields: list,
    current_content: Any,
    raw_text: str = None
):
    """Background task for running selective reprocessing."""
    try:
        selective_service = SelectiveReprocessingService()
        
        # Run selective reprocessing
        enhanced_content = await selective_service.reprocess_changed_fields(
            db=db,
            document_id=document_id,
            changed_fields=changed_fields,
            current_content=current_content,
            raw_text=raw_text
        )
        
        # Update the content with enhanced results
        extracted_data_repo = ExtractedDataRepository(ExtractedData)
        extracted_data_repo.update_structured_content(
            db=db,
            document_id=uuid.UUID(document_id),
            content=enhanced_content
        )
        
        # Update status to completed after successful reprocessing
        extracted_data_repo.update_review_status(
            db=db,
            document_id=uuid.UUID(document_id),
            review_status=ReviewStatus.REVIEWED_APPROVED,
            reviewed_by_user_id=None  # System enhancement
        )
        
        logger.info(f"Selective reprocessing completed successfully for document {document_id}")
        
    except Exception as e:
        logger.error(f"Selective reprocessing failed for document {document_id}: {e}", exc_info=True)

@router.get(
    "/all/{document_id}",
    response_model=ExtractionDetailsResponse, # Changed to use the new schema
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

    extracted_data_repo = ExtractedDataRepository(ExtractedData)  # Pass model class
    extracted_data = extracted_data_repo.get_by_document_id(db=db, document_id=document_id)
    if not extracted_data:
        raise HTTPException(status_code=404, detail="Extracted data not found for this document")

    # Return an instance of the new schema
    # Pydantic will handle from_orm conversion for doc and extracted_data
    return ExtractionDetailsResponse(document=doc, extracted_data=extracted_data)

# Note: A proper Pydantic model for ExtractionDetailsResponse should be created in app/schemas/extracted_data.py
# Example:
# from app.schemas.document import DocumentRead
# class ExtractionDetailsResponse(BaseModel):
#     document: DocumentRead
#     extracted_data: ExtractedDataRead
#
#     class Config:
#         orm_mode = True


# You can add more endpoints here, for example:
# @router.post("/", response_model=ExtractedData)
# async def create_extracted_data_item(
#     *, 
#     db: Session = Depends(deps.get_db),
#     item_in: ExtractedDataCreate,
#     # current_user: User = Depends(get_current_active_user) # Uncomment if endpoint needs auth
# ):
#     """
#     Create new extracted data item.
#     """
#     # item = crud.extracted_data.create(db=db, obj_in=item_in) # Example CRUD call
#     # return item
#     raise HTTPException(status_code=501, detail="Not Implemented")

# Add other CRUD operations (get by id, update, delete) as needed. 