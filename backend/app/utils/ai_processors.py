import logging
import os
from typing import Optional

# Import Document AI Client
from google.api_core.client_options import ClientOptions
from google.cloud import documentai

# Keep storage client for downloading if needed, though Document AI often reads GCS directly
from google.cloud import storage
from app.utils.storage import parse_gcs_path # Assuming this helper exists

logger = logging.getLogger(__name__)

def process_document_with_docai(
    project_id: str,
    location: str, # e.g., "us" or "eu"
    processor_id: str,
    gcs_uri: str,
    mime_type: str = "application/pdf" # Can be inferred usually, but good to provide
) -> Optional[documentai.Document]:
    """
    Processes a document stored in GCS using a specified Document AI processor.

    Args:
        project_id: The Google Cloud Project ID.
        location: The location of the processor (e.g., "us", "eu").
        processor_id: The ID of the Document AI processor.
        gcs_uri: The GCS URI of the document.
        mime_type: The MIME type of the document.

    Returns:
        The processed documentai.Document object, or None if processing fails.
    """
    if not gcs_uri.startswith("gs://"):
        logger.error(f"Invalid GCS URI: {gcs_uri}. Must start with 'gs://'.")
        return None

    try:
        # You must set the `api_endpoint` if you use a location other than "us".
        opts = {}
        if location != "us":
            opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")

        client = documentai.DocumentProcessorServiceClient(client_options=opts)

        # The full resource name of the processor version, e.g.:
        # `projects/{project_id}/locations/{location}/processors/{processor_id}`
        # or `projects/{project_id}/locations/{location}/processors/{processor_id}/processorVersions/{processor_version_id}`
        # For this example, we'll use the processor ID directly, assuming it's the default version.
        processor_path = client.processor_path(project_id, location, processor_id)

        # Construct the GcsDocument object
        gcs_doc_info = documentai.GcsDocument(gcs_uri=gcs_uri, mime_type=mime_type)

        # Construct the ProcessRequest
        request = documentai.ProcessRequest(
            name=processor_path,
            gcs_document=gcs_doc_info,  # Pass the GcsDocument object here
            skip_human_review=True  # Set to False if human review is part of your workflow
        )

        logger.info(f"Sending request to Document AI processor: {processor_path} for GCS URI: {gcs_uri}")
        result = client.process_document(request=request)
        logger.info("Successfully processed document with Document AI.")
        return result.document

    except Exception as e:
        logger.error(f"Exception during Document AI processing for {gcs_uri} (Processor: {processor_id}): {e}", exc_info=True)
        return None

# --- Test Block Updated for Document AI ---
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv() # Load environment variables from .env file

    # Ensure credentials are set via GOOGLE_APPLICATION_CREDENTIALS
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("ERROR: GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")
        exit(1)

    # --- Configuration from Environment Variables ---
    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    doc_ai_location = os.getenv("DOC_AI_LOCATION", "us") # Default to "us" if not set
    doc_ai_processor_id = os.getenv("DOC_AI_PROCESSOR_ID")
    test_input_gcs_uri = os.getenv("TEST_GCS_INPUT_URI")
    # Optional: Specify mime type if needed, Document AI often infers it.
    # Defaulting to application/pdf, can be overridden by an env var if needed.
    test_mime_type = os.getenv("TEST_MIME_TYPE", "application/pdf")
    # --- End Configuration ---

    # --- Validate Essential Configuration ---
    required_env_vars = {
        "GCP_PROJECT_ID": gcp_project_id,
        "DOC_AI_PROCESSOR_ID": doc_ai_processor_id,
        "TEST_GCS_INPUT_URI": test_input_gcs_uri
    }
    missing_vars = [var_name for var_name, value in required_env_vars.items() if not value]
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them before running the script. For example:")
        print("  export GCP_PROJECT_ID='your-project-id'")
        print("  export DOC_AI_LOCATION='us' (or your processor's region)")
        print("  export DOC_AI_PROCESSOR_ID='your-processor-id'")
        print("  export TEST_GCS_INPUT_URI='gs://your-bucket/your-file.pdf'")
        exit(1)

    print(f"Attempting to process GCS URI: {test_input_gcs_uri}")
    print(f"Using Project: {gcp_project_id}, Location: {doc_ai_location}, Processor ID: {doc_ai_processor_id}")

    # --- Process with Document AI ---
    processed_document = process_document_with_docai(
        project_id=gcp_project_id,
        location=doc_ai_location,
        processor_id=doc_ai_processor_id,
        gcs_uri=test_input_gcs_uri,
        mime_type=test_mime_type
    )
    # --- End Processing ---

    # --- Print Results ---
    if processed_document:
        print("\n--- Document AI Processing Successful ---")
        print(f"Extracted text snippet (first 200 chars): {processed_document.text[:200]}...")

        # Simplified Key-Value Pair Extraction Example
        form_fields_found = False
        for page in processed_document.pages:
            if page.form_fields:
                form_fields_found = True
                print("\n--- Sample Detected Form Fields ---")
                for field in page.form_fields[:3]: # Print only the first 3 found for brevity
                    field_name = field.field_name.text_anchor.content.strip().replace('\n', ' ') if field.field_name.text_anchor else ""
                    field_value = field.field_value.text_anchor.content.strip().replace('\n', ' ') if field.field_value.text_anchor else ""
                    print(f"  * Key: '{field_name}', Value: '{field_value}'")
                if len(page.form_fields) > 3:
                    print("  ... (and more fields)")
                break # Only show from the first page with fields for this concise output
        if not form_fields_found:
            print("\n(No form fields detected or processor is not a form parser type)")

    else:
        print(f"\n--- Document AI Processing Failed for: {test_input_gcs_uri} ---") 