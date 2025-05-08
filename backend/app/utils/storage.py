import logging
import uuid
from google.cloud import storage
from fastapi import UploadFile
from typing import Optional, Tuple

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
        # Use upload_from_string for in-memory content (synchronous call)
        blob.upload_from_string(content, content_type=file.content_type)
        
        gcs_path = f"gs://{settings.GCS_BUCKET_NAME}/{blob_name}"
        logger.info(f"File {file.filename} uploaded successfully to {gcs_path}")
        return gcs_path
    except Exception as e:
        logger.error(f"Failed to upload {file.filename} to GCS path {blob_name}: {e}", exc_info=True)
        return None
    finally:
        # Ensure the UploadFile is closed
        await file.close()

def parse_gcs_path(gcs_path: str) -> Tuple[str, str]:
    """
    Parses a GCS path into bucket name and blob name.
    
    Args:
        gcs_path: A GCS path in the format 'gs://bucket_name/blob_name'
        
    Returns:
        Tuple of (bucket_name, blob_name)
    """
    if not gcs_path.startswith("gs://"):
        raise ValueError(f"Invalid GCS path format: {gcs_path}")
    
    # Remove 'gs://' prefix
    path = gcs_path[5:]
    
    # Split into bucket name and blob name
    parts = path.split("/", 1)
    if len(parts) < 2:
        raise ValueError(f"Invalid GCS path format, missing blob name: {gcs_path}")
    
    bucket_name = parts[0]
    blob_name = parts[1]
    
    return bucket_name, blob_name

async def delete_file_from_gcs(gcs_path: str) -> bool:
    """
    Deletes a file from Google Cloud Storage.
    
    Args:
        gcs_path: The GCS path of the file to delete (gs://bucket_name/path/to/blob)
        
    Returns:
        True if deletion was successful, False otherwise
    """
    if not storage_client:
        logger.error("GCS client not initialized. Cannot delete file.")
        return False
    
    try:
        # Parse the GCS path
        bucket_name, blob_name = parse_gcs_path(gcs_path)
        
        # Get the bucket and blob
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        # Delete the blob
        blob.delete()
        
        logger.info(f"File deleted successfully from {gcs_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete file from {gcs_path}: {e}", exc_info=True)
        return False 

def get_gcs_uri(storage_path: str) -> str:
    """
    Converts a storage path to a GCS URI if it isn't already.
    
    Args:
        storage_path: Either a full GCS URI (gs://bucket/path) or a relative path in the default bucket
        
    Returns:
        A properly formatted GCS URI (gs://bucket_name/path)
    """
    if storage_path.startswith("gs://"):
        # Already a GCS URI
        return storage_path
    
    # Assume it's a relative path in the default bucket
    if not settings.GCS_BUCKET_NAME:
        logger.error("GCS_BUCKET_NAME not configured. Cannot construct GCS URI.")
        raise ValueError("GCS_BUCKET_NAME not configured")
        
    return f"gs://{settings.GCS_BUCKET_NAME}/{storage_path}" 