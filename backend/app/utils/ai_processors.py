import logging
import os
import json # For parsing LLM JSON output
from typing import Optional, Dict, Any # Added Dict, Any

# Import Document AI Client
from google.api_core.client_options import ClientOptions
from google.cloud import documentai

# Import Google Generative AI (for Gemini)
import google.generativeai as genai

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

SYSTEM_PROMPT_MEDICAL_STRUCTURING = '''
You are an expert AI assistant specialized in deep analysis of medical documents. Your task is to process the provided text, which has been OCR'd from a single medical document (such as a prescription, lab report, patient record, or clinical note). Your goal is to identify, categorize, and structure all medically relevant information within this document to facilitate future analysis and querying across multiple such documents.

The user will provide raw text from ONE medical document.

Output Format:
Provide the extracted and structured information in a JSON format. The JSON should be a list of "medical_events" or "medical_observations". Each item in the list should represent a distinct piece of information, observation, finding, medication, lab result, symptom, diagnosis, or procedure mentioned in the document.

For each item, include:
-   `event_type`: A category for the information (e.g., "Symptom", "Diagnosis", "Medication", "LabResult", "VitalSign", "Procedure", "Observation", "Allergy", "Immunization", "ClinicalFinding", "PatientInstruction").
-   `description`: The core piece of information or a concise description of the event/observation (e.g., "headache", "Type 2 Diabetes Mellitus", "Lisinopril 10mg", "Fasting Blood Sugar", "Appendectomy").
-   `value`: The specific value associated with the event, if applicable (e.g., for a lab result: "120", for a medication dosage: "10mg").
-   `units`: Units for the value, if applicable (e.g., "mg/dL", "mg", "bpm").
-   `date_time`: The most relevant date and/or time associated with this specific event within the document (YYYY-MM-DD HH:MM:SS if possible, otherwise as written). If a general document date applies and no specific event date is found, use the document date.
-   `body_location`: If applicable, the body location related to the event (e.g., "left arm", "abdomen").
-   `qualifiers`: Any modifiers, severity, status, or temporal context (e.g., "mild", "acute", "chronic", "history of", "resolved", "ongoing", "pre-operative", "post-operative", "for 2 weeks"). This can be a string or an array of strings.
-   `raw_text_snippet`: The exact snippet from the original text that this structured item was derived from. This is crucial for future reference and verification.
-   `notes`: Any additional relevant context or notes extracted by you that don't fit cleanly into other fields.

Example for a lab result snippet "Fasting Blood Sugar: 110 mg/dL on 2024-03-15":
{
    "event_type": "LabResult",
    "description": "Fasting Blood Sugar",
    "value": "110",
    "units": "mg/dL",
    "date_time": "2024-03-15",
    "raw_text_snippet": "Fasting Blood Sugar: 110 mg/dL on 2024-03-15",
    "qualifiers": null,
    "notes": null
}

Example for a medication snippet "Prescribed Amoxicillin 500mg t.i.d. for 7 days":
{
    "event_type": "Medication",
    "description": "Amoxicillin",
    "value": "500mg",
    "units": "mg",
    "date_time": "YYYY-MM-DD", // (Use document date if prescription date not in snippet)
    "raw_text_snippet": "Amoxicillin 500mg t.i.d. for 7 days",
    "qualifiers": ["t.i.d.", "for 7 days"],
    "notes": "Prescribed"
}

Guidelines:
*   Aim to capture as much medically relevant detail as possible in this structured list format.
*   The `raw_text_snippet` is very important for traceability.
*   If the document contains a narrative, try to break it down into discrete observations or findings.
*   For lists (e.g., a list of allergies), create a separate JSON object for each item in the list.
*   Infer `event_type` based on medical knowledge.
*   If information is directly tied together (e.g., a test name, its value, units, and reference range), try to keep them within the same structured object, possibly using the `notes` field for related parts like reference ranges if they don't fit the primary `value`/`units`.
*   The main date of the document (report date, visit date) should be identified and can be used for events that don't have a more specific timestamp.

Do not attempt to analyze across documents in this step. Focus solely on structuring the information from the single document provided.
'''

def structure_text_with_gemini(api_key: str, raw_text: str) -> Optional[str]:
    """
    Sends raw text to Gemini Flash model for structured data extraction based on a medical system prompt.

    Args:
        api_key: The API key for Google Generative AI.
        raw_text: The raw text extracted from a document.

    Returns:
        A string containing the LLM's response (hopefully a JSON string), or None on failure.
    """
    if not raw_text.strip():
        logger.warning("Received empty raw text for Gemini processing. Skipping.")
        return None
    
    logger.info(f"Sending text (length: {len(raw_text)}) to Gemini 2.0 Flash for structuring...")
    try:
        genai.configure(api_key=api_key)
        
        # For safety settings, we might need to adjust them if responses are getting blocked.
        # Starting with more permissive settings for now, can be tightened later.
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]

        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction=SYSTEM_PROMPT_MEDICAL_STRUCTURING,
            safety_settings=safety_settings,
            generation_config=genai.types.GenerationConfig(
                # Ensure the output is treated as JSON by asking for it explicitly if the model supports it
                # or by instructing it in the prompt. The prompt already asks for JSON.
                # For some models, you might specify response_mime_type='application/json' here.
                # However, for gemini-1.5-flash, direct JSON mode is typically enabled by instruction.
                # We can also try to parse the output and validate if it's JSON.
                temperature=0.1 # Lower temperature for more deterministic, structured output
            )
        )
        
        response = model.generate_content(raw_text)
        
        if response.parts:
            # Assuming the response text is in the first part and contains the JSON string
            # Need to handle cases where response.text might be empty or not JSON
            llm_output = response.text
            logger.info(f"Received response from Gemini Flash (length: {len(llm_output)}).")
            
            # Basic check if it looks like JSON before returning
            # More robust validation can be added later
            if llm_output.strip().startswith("[") and llm_output.strip().endswith("]") or \
               llm_output.strip().startswith("{") and llm_output.strip().endswith("}"):
                return llm_output
            else:
                logger.warning(f"Gemini output does not appear to be valid JSON. Output: {llm_output[:500]}...")
                # Fallback: attempt to extract JSON from markdown code blocks if present
                if "```json" in llm_output:
                    try:
                        json_block = llm_output.split("```json")[1].split("```")[0].strip()
                        if json_block.strip().startswith("[") and json_block.strip().endswith("]") or \
                           json_block.strip().startswith("{") and json_block.strip().endswith("}"):
                            logger.info("Successfully extracted JSON from markdown code block.")
                            return json_block
                    except IndexError:
                        logger.warning("Could not extract JSON from markdown block despite presence of ```json.")
                return None # Or return the raw output if we want to inspect non-JSON responses
        else:
            logger.warning("Gemini response has no parts or text.")
            if response.prompt_feedback:
                logger.warning(f"Prompt Feedback: {response.prompt_feedback}")
            return None

    except Exception as e:
        logger.error(f"Exception during Gemini API call: {e}", exc_info=True)
        return None

# --- Test Block Updated for Document AI & Gemini --- 
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv() # Load environment variables from .env file

    # Ensure GOOGLE_APPLICATION_CREDENTIALS for Document AI is set
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("ERROR: GOOGLE_APPLICATION_CREDENTIALS environment variable not set for Document AI.")
        exit(1)
    
    # --- Configuration from Environment Variables ---
    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    doc_ai_location = os.getenv("DOC_AI_LOCATION", "us")
    doc_ai_processor_id = os.getenv("DOC_AI_PROCESSOR_ID")
    test_input_gcs_uri = os.getenv("TEST_GCS_INPUT_URI")
    test_mime_type = os.getenv("TEST_MIME_TYPE", "application/pdf")
    gemini_api_key = os.getenv("GEMINI_API_KEY") # <--- New: For Gemini API
    # --- End Configuration ---

    # --- Validate Essential Configuration ---
    required_env_vars = {
        "GCP_PROJECT_ID": gcp_project_id,
        "DOC_AI_PROCESSOR_ID": doc_ai_processor_id,
        "TEST_GCS_INPUT_URI": test_input_gcs_uri,
        "GEMINI_API_KEY": gemini_api_key # <--- New: Check for Gemini API key
    }
    missing_vars = [var_name for var_name, value in required_env_vars.items() if not value]
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them before running the script. For example:")
        print("  export GCP_PROJECT_ID='your-project-id'")
        print("  export DOC_AI_LOCATION='us' (or your processor's region)")
        print("  export DOC_AI_PROCESSOR_ID='your-processor-id'")
        print("  export TEST_GCS_INPUT_URI='gs://your-bucket/your-file.pdf'")
        print("  export GEMINI_API_KEY='your-gemini-api-key'")
        exit(1)

    

    print(f"Attempting to process GCS URI with Document AI: {test_input_gcs_uri}")
    print(f"Using Document AI Project: {gcp_project_id}, Location: {doc_ai_location}, Processor ID: {doc_ai_processor_id}")

    processed_document = process_document_with_docai(
        project_id=gcp_project_id,
        location=doc_ai_location,
        processor_id=doc_ai_processor_id,
        gcs_uri=test_input_gcs_uri,
        mime_type=test_mime_type
    )

    if processed_document and processed_document.text:
        print("\n--- Document AI OCR Successful ---")
        print(f"Extracted text snippet (first 200 chars): {processed_document.text[:200]}...")

        print("\n--- Attempting to Structure Text with Gemini Flash ---")
        structured_json_output = structure_text_with_gemini(
            api_key=gemini_api_key, 
            raw_text=processed_document.text
        )

        if structured_json_output:
            print("\n--- Gemini Flash Processing Successful ---")
            print("Attempting to parse and print structured JSON output from Gemini:")
            try:
                # Attempt to pretty-print the JSON
                parsed_json = json.loads(structured_json_output)
                print(json.dumps(parsed_json, indent=2))
            except json.JSONDecodeError as e:
                print(f"ERROR: Could not decode JSON from Gemini output. Error: {e}")
                print("Raw Gemini output snippet:")
                print(structured_json_output[:1000] + "...")
        else:
            print("\n--- Gemini Flash Processing Failed or No Output ---")
    elif processed_document:
        print("\n--- Document AI OCR Successful, but no text extracted ---")
    else:
        print(f"\n--- Document AI Processing Failed for: {test_input_gcs_uri} ---") 

# --- New Function for Answering Queries from Context ---
async def answer_query_from_context(api_key: str, query_text: str, json_data_context: str) -> Optional[str]:
    """
    Sends a natural language query and a context of JSON data to Gemini Flash model 
    to generate a natural language answer.

    Args:
        api_key: The API key for Google Generative AI.
        query_text: The natural language query from the user.
        json_data_context: A string containing all relevant JSON data (e.g., a list of JSON objects)
                           for the user, which the LLM should use to answer the query.

    Returns:
        A string containing the LLM's natural language answer, or None on failure.
    """
    if not query_text.strip():
        logger.warning("Received empty query text for answering. Skipping.")
        return None
    if not json_data_context.strip():
        logger.warning("Received empty JSON data context for answering. Skipping.")
        # Or, alternatively, could try to answer without context if that's ever desired.
        # For now, assume context is required.
        return "I don't have any of your medical data to search through. Please upload your documents first."

    system_prompt = f"""
    You are a helpful AI assistant. Your role is to answer the user's questions based *solely* on the provided medical data context. 
    The medical data context consists of a collection of JSON objects, where each object represents structured information extracted from one of their medical documents. 
    Each JSON object typically contains a list of 'medical_events' with fields like 'event_type', 'description', 'value', 'units', 'date_time', and 'raw_text_snippet'.

    User's Question: "{query_text}"

    Provided Medical Data Context (JSON blobs from user's documents):
    ```json
    {json_data_context}
    ```

    Instructions:
    1. Carefully analyze the User's Question.
    2. Thoroughly search the Provided Medical Data Context to find relevant information to answer the question.
    3. Formulate a clear, concise, and natural language answer based *only* on the information found in the Provided Medical Data Context.
    4. If the answer to the question cannot be found in the provided data, explicitly state that (e.g., "I could not find information about that in your provided documents.").
    5. Do NOT use any external knowledge or make assumptions beyond what is present in the provided data.
    6. If quoting specific values or snippets, you can refer to them, but the overall answer should be conversational.
    7. Do not refer to the data as "JSON blobs" or "medical_events list" in your answer to the user; just use the information naturally.
    8. Your primary goal is to be helpful and accurate based *only* on the provided documents.
    Ensure your output is only the natural language answer to the user's question.
    """
    
    logger.info(f"Sending query and JSON context (length: {len(json_data_context)}) to Gemini for answering...")
    logger.debug(f"Gemini System Prompt for Answering from Context:\n{system_prompt[:1000]}...") # Log a snippet of the prompt

    try:
        genai.configure(api_key=api_key)
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]

        # For very long prompts that include a lot of data, it's common to put the entire prompt
        # (system instructions + user query + data context) directly into the content generation call.
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest', 
            safety_settings=safety_settings,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2 # Slightly higher temp for more natural language, but still fairly factual
            )
        )
        
        response = await model.generate_content_async(system_prompt) # Pass the whole crafted prompt
        
        if response.parts:
            answer = response.text
            logger.info(f"Received answer from Gemini (length: {len(answer)}).")
            logger.debug(f"Raw LLM answer: {answer}")
            return answer.strip() # Return the natural language answer
        else:
            logger.warning("Gemini response for answering query has no parts or text.")
            if response.prompt_feedback:
                logger.warning(f"Prompt Feedback for answering query: {response.prompt_feedback}")
            return "I encountered an issue trying to generate an answer. Please try again."

    except Exception as e:
        logger.error(f"Exception during Gemini API call for answering query: {e}", exc_info=True)
        return "I'm sorry, but I encountered an error while trying to process your request." 