import logging
import hashlib
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.auth import verify_token
from app.repository import document_repo, user_repo
from app.schemas.document import DocumentRead, DocumentCreate
from app.utils.storage import upload_file_to_gcs
from app.models.document import DocumentType

logger = logging.getLogger(__name__)
router = APIRouter(tags=["documents"])

def calculate_hash(content: bytes) -> str:
    """Calculates SHA-256 hash of the file content."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()

@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    *, 
    db: AsyncSession = Depends(get_db),
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
    user = await user_repo.get_by_supabase_id(db, supabase_id=supabase_id)
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
        file_content = await file.read()
        await file.seek(0) # Reset file pointer after reading for GCS upload
    except Exception as e:
         logger.error(f"Failed to read uploaded file {file.filename}: {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not read uploaded file.")

    file_hash = calculate_hash(file_content)
    # Optional: Check if a document with this hash already exists for this user to prevent duplicates
    # existing_doc = await document_repo.get_by_hash_for_user(db, user_id=internal_user_id, file_hash=file_hash)
    # if existing_doc:
    #     raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate file detected")

    # Upload to GCS
    gcs_path = await upload_file_to_gcs(file=file, user_id=internal_user_id)
    if not gcs_path:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload file to storage")

    # Create document metadata schema
    doc_meta = DocumentCreate(
        original_filename=file.filename,
        document_type=document_type,
        # Add file_metadata if desired, e.g.:
        # file_metadata={"content_type": file.content_type, "size": len(file_content)}
    )

    # Save document record to database
    try:
        created_document = await document_repo.create_with_owner(
            db=db, 
            obj_in=doc_meta, 
            user_id=internal_user_id, 
            storage_path=gcs_path, 
            file_hash=file_hash
        )
        logger.info(f"Document record created successfully for {file.filename}, ID: {created_document.document_id}")
        return created_document
    except Exception as e:
        # Potentially try to clean up the GCS file if DB insert fails?
        logger.error(f"Failed to create document record in DB for {file.filename} at {gcs_path}: {e}", exc_info=True)
        # Consider adding GCS cleanup logic here
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save document metadata")

# Add other document endpoints here (GET, LIST, DELETE etc.) later 