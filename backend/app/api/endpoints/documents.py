import logging
import hashlib
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    status,
    Form,
    Query,
    BackgroundTasks,
)
from typing import List, Optional
from uuid import UUID
from app.db.session import get_db, get_async_db
from app.core.auth import verify_token, get_user_id_from_token
from app.repositories.document_repo import document_repo
from app.repositories.user_repo import user_repo
from app.schemas.document import DocumentRead, DocumentCreate, DocumentMetadataUpdate
from app.utils.storage import upload_file_to_gcs, delete_file_from_gcs
from app.models.document import DocumentType
from app.services.document_processing_service import run_document_processing_pipeline
from app.models.extracted_data import ExtractedData
from app.repositories.extracted_data_repo import ExtractedDataRepository

logger = logging.getLogger(__name__)
router = APIRouter(tags=["documents"])


async def get_or_create_user(db: AsyncSession, token_data: dict):
    """Get user from database or auto-create if doesn't exist."""
    supabase_id = token_data.get("sub")
    if not supabase_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload",
        )

    user = await user_repo.get_by_supabase_id(db, supabase_id=supabase_id)

    if not user:

        logger.info(f"Auto-creating new user for supabase_id: {supabase_id}")
        from app.schemas.user import UserCreate

        email = token_data.get("email", f"user-{supabase_id}@example.com")

        user_create = UserCreate(email=email, supabase_id=supabase_id)

        user = await user_repo.create(db=db, obj_in=user_create)
        logger.info(f" Auto-created user with id: {user.user_id}")

    return user


def calculate_hash(content: bytes) -> str:
    """Calculates SHA-256 hash of the file content."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()


@router.post(
    "/upload", response_model=List[DocumentRead], status_code=status.HTTP_201_CREATED
)
async def upload_document(
    *,
    db: AsyncSession = Depends(get_async_db),
    background_tasks: BackgroundTasks,
    token_data: dict = Depends(verify_token),
    document_type: DocumentType = Form(...),
    files: List[UploadFile] = File(
        ..., description="Upload up to 5 files simultaneously"
    ),
):
    """
    Uploads multiple medical documents (up to 5) for the authenticated user.

    Requires form data with 'document_type' (prescription, lab_result, or other) and multiple 'files'.
    Returns a list of successfully uploaded documents. If any file fails, it continues with others.
    """

    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 files allowed per upload",
        )

    if len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required",
        )

    user = await get_or_create_user(db, token_data)

    uploaded_documents = []
    failed_uploads = []

    for file_index, file in enumerate(files):
        try:
            logger.info(
                f"Processing file {file_index + 1}/{len(files)}: {file.filename}"
            )

            try:
                file_content = await file.read()
                await file.seek(0)
            except Exception as e:
                logger.error(
                    f"Failed to read uploaded file {file.filename}: {e}", exc_info=True
                )
                failed_uploads.append(
                    {
                        "filename": file.filename,
                        "error": "Could not read uploaded file.",
                    }
                )
                continue

            file_hash = calculate_hash(file_content)

            existing_doc = document_repo.get_by_hash_for_user(
                db, user_id=user.user_id, file_hash=file_hash
            )
            if existing_doc:
                logger.info(
                    f"Duplicate file detected for user {user.user_id}, existing document: {existing_doc.document_id}"
                )
                failed_uploads.append(
                    {
                        "filename": file.filename,
                        "error": f"Duplicate file detected. Existing document ID: {existing_doc.document_id}",
                        "existing_document_id": str(existing_doc.document_id),
                        "uploaded_on": existing_doc.upload_timestamp.isoformat(),
                    }
                )
                continue

            gcs_path = await upload_file_to_gcs(file=file, user_id=user.user_id)
            if not gcs_path:
                failed_uploads.append(
                    {
                        "filename": file.filename,
                        "error": "Failed to upload file to storage",
                    }
                )
                continue

            doc_meta = DocumentCreate(
                original_filename=file.filename,
                document_type=document_type,
                file_metadata={
                    "content_type": file.content_type,
                    "size": len(file_content),
                    "filename": file.filename,
                },
            )

            try:

                async with db.begin():

                    created_document = await document_repo.create_with_owner_async(
                        db=db,
                        obj_in=doc_meta,
                        user_id=user.user_id,
                        storage_path=gcs_path,
                        file_hash=file_hash,
                    )
                    logger.info(
                        f"Document record created successfully for {file.filename}, ID: {created_document.document_id}"
                    )

                    extracted_data_repo = ExtractedDataRepository(ExtractedData)
                    initial_extracted_data_success = (
                        await extracted_data_repo.create_initial_extracted_data_async(
                            db=db, document_id=created_document.document_id
                        )
                    )

                    if not initial_extracted_data_success:
                        logger.critical(
                            f"CRITICAL: Failed to create initial ExtractedData record for document {created_document.document_id}. Rolling back transaction."
                        )

                        raise Exception("Failed to initialize document for processing")

                    logger.info(
                        f"Successfully created document and extracted data records for {file.filename}"
                    )

                background_tasks.add_task(
                    run_document_processing_pipeline, created_document.document_id
                )
                logger.info(
                    f"Added document processing pipeline to background tasks for document ID: {created_document.document_id}"
                )

                uploaded_documents.append(created_document)

            except Exception as e:

                logger.error(
                    f"Failed to create document record in DB for {file.filename} at {gcs_path}: {e}",
                    exc_info=True,
                )
                if gcs_path:
                    try:
                        await delete_file_from_gcs(gcs_path)
                    except Exception as cleanup_error:
                        logger.error(
                            f"Failed to cleanup GCS file {gcs_path}: {cleanup_error}"
                        )

                failed_uploads.append(
                    {
                        "filename": file.filename,
                        "error": "Failed to save document metadata",
                    }
                )
                continue

        except Exception as e:
            logger.error(
                f"Unexpected error processing file {file.filename}: {e}", exc_info=True
            )
            failed_uploads.append(
                {"filename": file.filename, "error": f"Unexpected error: {str(e)}"}
            )
            continue

    logger.info(
        f"Upload batch completed. Successful: {len(uploaded_documents)}, Failed: {len(failed_uploads)}"
    )

    if failed_uploads:
        logger.warning(f"Some files failed to upload: {failed_uploads}")

    if not uploaded_documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "No files were successfully uploaded",
                "failed_uploads": failed_uploads,
            },
        )

    return uploaded_documents


@router.get("", response_model=List[DocumentRead])
@router.get("/", response_model=List[DocumentRead])
async def list_documents(
    *,
    db: AsyncSession = Depends(get_async_db),
    token_data: dict = Depends(verify_token),
    skip: int = Query(0, ge=0, description="Skip N items"),
    limit: int = Query(100, ge=1, le=100, description="Limit to N items"),
    optimized: bool = Query(
        True, description="Use optimized queries with eager loading (recommended)"
    ),
):
    """
    List all documents belonging to the authenticated user.

    Results are paginated and ordered by upload timestamp (newest first).
    """
    user = await get_or_create_user(db, token_data)

    limit = min(limit, 100)

    if optimized:
        documents = await document_repo.get_multi_by_owner_optimized_async(
            db=db, user_id=user.user_id, skip=skip, limit=limit
        )
    else:
        documents = await document_repo.get_multi_by_owner_async(
            db=db, user_id=user.user_id, skip=skip, limit=limit
        )

    logger.info(
        f"Retrieved {len(documents)} documents for user {user.user_id} (optimized={optimized})"
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
    user_id = get_user_id_from_token(db, token_data)

    document = document_repo.get_by_id(db=db, document_id=document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    if document.user_id != user_id:
        logger.warning(
            f"User {user_id} attempted to access document {document_id} owned by {document.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this document",
        )

    return document


@router.patch("/{document_id}/metadata", response_model=DocumentRead)
def update_document_metadata(
    *,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
    document_id: UUID,
    metadata_in: DocumentMetadataUpdate,
):
    """
    Update user-editable metadata fields for a specific document.

    This endpoint allows users to override system-extracted metadata
    or set user-specific fields like tags and health context.
    Only fields provided in the request body will be updated in the overrides.
    To clear an override, provide the field with a null value (though Pydantic
    optional fields might need specific handling or explicit `None` checking).
    """
    user_id = get_user_id_from_token(db, token_data)

    document = document_repo.get_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    if document.user_id != user_id:
        logger.warning(
            f"User {user_id} attempted to update metadata for document {document_id} owned by {document.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to update this document's metadata",
        )

    update_data = metadata_in.model_dump(exclude_unset=True)

    if not update_data:
        logger.info(f"No metadata fields provided to update for document {document_id}")

        return document

    updated_document = document_repo.update_overrides(
        db=db, document_id=document_id, overrides_in=update_data
    )

    if not updated_document:

        logger.error(
            f"Failed to update metadata overrides for document {document_id} in repository."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update document metadata",
        )

    return updated_document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
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
    user_id = get_user_id_from_token(db, token_data)

    document = document_repo.get_by_id(db=db, document_id=document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    if document.user_id != user_id:
        logger.warning(
            f"User {user_id} attempted to delete document {document_id} owned by {document.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this document",
        )

    gcs_path = document.storage_path
    gcs_deletion_success = await delete_file_from_gcs(gcs_path)

    if not gcs_deletion_success:
        logger.warning(
            f"Failed to delete file from GCS: {gcs_path}"
        )  # Continue anyway to delete the database record

    document_repo.remove(db=db, id=document_id)

    return None


@router.get("/search", response_model=List[DocumentRead], summary="Search documents")
def search_documents(
    *,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
    query: str = Query(..., description="Search query"),
    document_type: Optional[DocumentType] = Query(
        None, description="Filter by document type"
    ),
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of documents to return"
    ),
):
    """
    Search for documents using full-text search.

    This endpoint searches across multiple fields including:
    - File name
    - Source name
    - Source location
    - Document content (extracted text)
    - Tags

    Results are ranked by relevance and filtered to only include the authenticated user's documents.
    """

    user_id = get_user_id_from_token(db, token_data)

    try:

        documents = document_repo.search_documents(
            db=db,
            user_id=user_id,
            search_query=query,
            document_type=document_type,
            skip=skip,
            limit=limit,
        )

        logger.info(
            f"Document search performed",
            extra={
                "structured_data": {
                    "user_id": user_id,
                    "query": query,
                    "document_type": document_type.value if document_type else None,
                    "results_count": len(documents),
                }
            },
        )

        return documents
    except Exception as e:
        logger.error(f"Error during document search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while searching for documents",
        )
