from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.db.session import get_db
from app.core.auth import verify_token, get_user_id_from_token
from app.models.extracted_data import ReviewStatus
from app.repositories.extracted_data_repo import ExtractedDataRepository
from app.repositories.document_repo import document_repo
from app.repositories.user_repo import user_repo
from app.schemas.extracted_data import (
    ExtractedDataResponse,
    ExtractedDataStatusUpdate,
    ExtractedDataContentUpdate
)

router = APIRouter(tags=["extracted_data"])

@router.get("/{document_id}", response_model=ExtractedDataResponse)
def get_extracted_data(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    """
    Retrieve the extracted data for a specific document.
    """
    # Get internal user ID from token data
    user_id = get_user_id_from_token(db, token_data)
    
    # Check document ownership
    document = document_repo.get_document(db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this document"
        )
    
    # Get extracted data
    extracted_data_repo = ExtractedDataRepository(db)
    extracted_data = extracted_data_repo.get_by_document_id(document_id)
    
    if not extracted_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No extracted data found for this document"
        )
    
    return extracted_data

@router.put("/{document_id}/status", response_model=ExtractedDataResponse)
def update_extracted_data_status(
    document_id: uuid.UUID,
    status_update: ExtractedDataStatusUpdate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    """
    Update the review status of extracted data.
    """
    # Get internal user ID from token data
    user_id = get_user_id_from_token(db, token_data)
    
    # Check document ownership
    document = document_repo.get_document(db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this document"
        )
    
    # Update extracted data status
    extracted_data_repo = ExtractedDataRepository(db)
    updated_data = extracted_data_repo.update_review_status(
        document_id=document_id,
        review_status=status_update.review_status,
        reviewed_by_user_id=user_id
    )
    
    if not updated_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No extracted data found for this document"
        )
    
    return updated_data

@router.put("/{document_id}/content", response_model=ExtractedDataResponse)
def update_extracted_data_content(
    document_id: uuid.UUID,
    content_update: ExtractedDataContentUpdate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    """
    Update the structured content of extracted data.
    This endpoint allows manual correction of the AI-extracted data.
    """
    # Get internal user ID from token data
    user_id = get_user_id_from_token(db, token_data)
    
    # Check document ownership
    document = document_repo.get_document(db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this document"
        )
    
    # Update extracted data content
    extracted_data_repo = ExtractedDataRepository(db)
    updated_data = extracted_data_repo.update_structured_content(
        document_id=document_id,
        content=content_update.content
    )
    
    if not updated_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No extracted data found for this document"
        )
    
    # Also update the review status to indicate it was corrected
    extracted_data_repo.update_review_status(
        document_id=document_id,
        review_status=ReviewStatus.REVIEWED_CORRECTED,
        reviewed_by_user_id=user_id
    )
    
    return updated_data

@router.get("/all/{document_id}", response_model=Dict[str, Any])
def get_extraction_details(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    """
    Get all details about the extraction including document info, raw text, and structured content.
    This combined endpoint is useful for the review UI.
    """
    # Get internal user ID from token data
    user_id = get_user_id_from_token(db, token_data)
    
    # Check document ownership
    document = document_repo.get_document(db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this document"
        )
    
    # Get extracted data
    extracted_data_repo = ExtractedDataRepository(db)
    extracted_data = extracted_data_repo.get_by_document_id(document_id)
    
    if not extracted_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No extracted data found for this document"
        )
    
    # Create a combined response
    return {
        "document": {
            "document_id": document.document_id,
            "filename": document.filename,
            "document_type": document.document_type,
            "upload_date": document.upload_date,
            "processing_status": document.processing_status
        },
        "extracted_data": {
            "extracted_data_id": extracted_data.extracted_data_id,
            "raw_text": extracted_data.raw_text,
            "content": extracted_data.content,
            "review_status": extracted_data.review_status,
            "extraction_timestamp": extracted_data.extraction_timestamp,
            "review_timestamp": extracted_data.review_timestamp
        }
    } 