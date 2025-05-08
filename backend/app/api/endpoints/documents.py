import logging
import hashlib
# Use sync Session
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form, Query, BackgroundTasks
from typing import List, Dict, Any
from uuid import UUID

# Use sync get_db
from app.db.session import get_db
from app.core.auth import verify_token
# Update to use repositories (plural)
from app.repositories.document_repo import document_repo
from app.repositories.user_repo import user_repo
from app.schemas.document import DocumentRead, DocumentCreate
# Assuming sync storage utils or that they handle sync calls
from app.utils.storage import upload_file_to_gcs, delete_file_from_gcs 
from app.models.document import DocumentType

# Import for background task and new sync repository
from app.services.document_processing_service import run_document_processing_pipeline
from app.repositories.extracted_data_repo import ExtractedDataRepository

logger = logging.getLogger(__name__)
router = APIRouter(tags=["documents"])

def calculate_hash(content: bytes) -> str:
    """Calculates SHA-256 hash of the file content."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()

@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(
    *,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks,
    token_data: dict = Depends(verify_token),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
):
    """
    Uploads a medical document (prescription or lab result) for the authenticated user.

    Requires form data with 'document_type' (prescription or lab_result) and the 'file' itself.
    """
    supabase_id = token_data.get("sub")
    if not supabase_id:
        logger.error("Supabase ID not found in token during upload.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token payload")

    # Get internal user ID from supabase ID
    user = user_repo.get_by_supabase_id_sync(db, supabase_id=supabase_id)
    if not user:
        # This case should ideally not happen if user sync is working, 
        # but handle it defensively.
        logger.error(f"User with supabase_id {supabase_id} not found in internal database.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    internal_user_id = user.user_id

    # Read file content to calculate hash and pass to storage
    # Important: Reading the whole file into memory might be an issue for very large files.
    # Consider streaming approaches for production if large files are expected.
    try:
        file_content = file.file.read()
        file.file.seek(0) # Reset file pointer after reading for GCS upload
    except Exception as e:
         logger.error(f"Failed to read uploaded file {file.filename}: {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not read uploaded file.")

    file_hash = calculate_hash(file_content)
    # Check if a document with this hash already exists for this user to prevent duplicates
    existing_doc = document_repo.get_by_hash_for_user(db, user_id=internal_user_id, file_hash=file_hash)
    if existing_doc:
        # Return a 409 Conflict with information about the existing document
        logger.info(f"Duplicate file detected for user {internal_user_id}, existing document: {existing_doc.document_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail={
                "message": "Duplicate file detected",
                "existing_document_id": str(existing_doc.document_id),
                "uploaded_on": existing_doc.upload_timestamp.isoformat()
            }
        )

    # Upload to GCS
    gcs_path = upload_file_to_gcs(file=file, user_id=internal_user_id)
    if not gcs_path:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload file to storage")

    # Create document metadata schema
    doc_meta = DocumentCreate(
        original_filename=file.filename,
        document_type=document_type,
        file_metadata={
            "content_type": file.content_type, 
            "size": len(file_content),
            "filename": file.filename
        }
    )

    # Save document record to database
    try:
        created_document = document_repo.create_with_owner(
            db=db,
            obj_in=doc_meta,
            user_id=internal_user_id,
            storage_path=gcs_path,
            file_hash=file_hash
        )
        logger.info(f"Document record created successfully for {file.filename}, ID: {created_document.document_id}")
        
        # Create initial ExtractedData record using the now sync repository
        extracted_data_repo = ExtractedDataRepository(db)
        initial_extracted_data = extracted_data_repo.create_initial_extracted_data(document_id=created_document.document_id)

        if not initial_extracted_data:
            logger.critical(f"CRITICAL: Failed to create initial ExtractedData record for document {created_document.document_id}. This will prevent background processing. Cleaning up GCS file.")
            # Attempt to cleanup the GCS file as the document processing cannot proceed reliably.
            if gcs_path:
                delete_file_from_gcs(gcs_path)
            # Also consider deleting the created_document record itself to keep DB consistent, though this adds complexity.
            # await document_repo.remove(db=db, id=created_document.document_id) # If you decide to do this.
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to initialize document for processing. Uploaded file has been removed."
            )

        # Add document processing to background tasks
        background_tasks.add_task(run_document_processing_pipeline, created_document.document_id)
        logger.info(f"Added document processing pipeline to background tasks for document ID: {created_document.document_id}")

        return created_document
    except Exception as e:
        # Potentially try to clean up the GCS file if DB insert fails?
        logger.error(f"Failed to create document record in DB for {file.filename} at {gcs_path}: {e}", exc_info=True)
        # Consider adding GCS cleanup logic here
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save document metadata")

@router.get("/", response_model=List[DocumentRead])
def list_documents(
    *,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
    skip: int = Query(0, ge=0, description="Skip N items"),
    limit: int = Query(100, ge=1, le=100, description="Limit to N items"),
):
    """
    List all documents belonging to the authenticated user.
    
    Results are paginated and ordered by upload timestamp (newest first).
    """
    supabase_id = token_data.get("sub")
    if not supabase_id:
        logger.error("Supabase ID not found in token during document listing.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token payload")
    
    # Get internal user ID from supabase ID
    user = user_repo.get_by_supabase_id_sync(db, supabase_id=supabase_id)
    if not user:
        logger.error(f"User with supabase_id {supabase_id} not found in internal database.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    documents = document_repo.get_multi_by_owner(
        db=db,
        user_id=user.user_id,
        skip=skip,
        limit=limit
    )
    
    return documents

@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    *,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
    document_id: UUID,
):
    """
    Get details of a specific document by ID.
    
    Only returns documents belonging to the authenticated user.
    """
    supabase_id = token_data.get("sub")
    if not supabase_id:
        logger.error("Supabase ID not found in token during document retrieval.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token payload")
    
    # Get internal user ID from supabase ID
    user = user_repo.get_by_supabase_id_sync(db, supabase_id=supabase_id)
    if not user:
        logger.error(f"User with supabase_id {supabase_id} not found in internal database.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    document = document_repo.get_by_id(db=db, document_id=document_id)
    
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # Ensure the document belongs to the authenticated user
    if document.user_id != user.user_id:
        logger.warning(f"User {user.user_id} attempted to access document {document_id} owned by {document.user_id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this document")
    
    return document

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    *,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
    document_id: UUID,
):
    """
    Delete a document by ID.
    
    Also removes the document file from storage.
    Only allows deleting documents belonging to the authenticated user.
    """
    supabase_id = token_data.get("sub")
    if not supabase_id:
        logger.error("Supabase ID not found in token during document deletion.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token payload")
    
    # Get internal user ID from supabase ID
    user = user_repo.get_by_supabase_id_sync(db, supabase_id=supabase_id)
    if not user:
        logger.error(f"User with supabase_id {supabase_id} not found in internal database.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    document = document_repo.get_by_id(db=db, document_id=document_id)
    
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # Ensure the document belongs to the authenticated user
    if document.user_id != user.user_id:
        logger.warning(f"User {user.user_id} attempted to delete document {document_id} owned by {document.user_id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this document")
    
    # Delete the file from GCS storage
    gcs_path = document.storage_path
    gcs_deletion_success = delete_file_from_gcs(gcs_path)
    
    if not gcs_deletion_success:
        logger.warning(f"Failed to delete file from GCS: {gcs_path}")
        # Continue anyway to delete the database record
    
    # Delete the document from database
    document_repo.remove(db=db, id=document_id)
    
    return None 