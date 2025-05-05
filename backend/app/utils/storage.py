import logging
import uuid
from google.cloud import storage
from fastapi import UploadFile
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize GCS client
# Handles authentication via GOOGLE_APPLICATION_CREDENTIALS implicitly
try:
    storage_client = storage.Client()
except Exception as e:
    logger.error(f"Failed to initialize Google Cloud Storage client: {e}. Ensure credentials are set.", exc_info=True)
    storage_client = None # Set to None if init fails

async def upload_file_to_gcs(file: UploadFile, user_id: uuid.UUID) -> Optional[str]:
    """
    Uploads a file to Google Cloud Storage in a user-specific folder.

    Args:
        file: The FastAPI UploadFile object.
        user_id: The UUID of the user uploading the file.

    Returns:
        The GCS blob path (gs://bucket_name/path/to/blob) if successful, None otherwise.
    """
    if not storage_client:
        logger.error("GCS client not initialized. Cannot upload file.")
        return None
        
    if not settings.GCS_BUCKET_NAME:
        logger.error("GCS_BUCKET_NAME not configured. Cannot upload file.")
        return None

    bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
    
    # Generate a unique filename using UUID to avoid collisions
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    
    # Construct blob path: user_id/unique_filename
    # Using user ID provides basic isolation
    blob_name = f"{str(user_id)}/{unique_filename}"
    blob = bucket.blob(blob_name)

    try:
        # Read file content asynchronously
        content = await file.read()
        
        # Upload the file content
        # Use upload_from_string for in-memory content
        await blob.upload_from_string(content, content_type=file.content_type)
        
        gcs_path = f"gs://{settings.GCS_BUCKET_NAME}/{blob_name}"
        logger.info(f"File {file.filename} uploaded successfully to {gcs_path}")
        return gcs_path
    except Exception as e:
        logger.error(f"Failed to upload {file.filename} to GCS path {blob_name}: {e}", exc_info=True)
        return None
    finally:
        # Ensure the UploadFile is closed
        await file.close() 