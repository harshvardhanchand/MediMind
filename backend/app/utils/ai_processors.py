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

# Updated System Prompt for Structuring AND Metadata Extraction
SYSTEM_PROMPT_MEDICAL_STRUCTURING = '''
You are an expert AI assistant specialized in deep analysis of medical documents. Your task is to process the provided text, which has been OCR'd from a single medical document (such as a prescription, lab report, patient record, or clinical note). Your goal is to:
1. Identify and structure all medically relevant information (observations, findings, medications, lab results, symptoms, diagnoses, procedures) into a list of "medical_events".
2. Extract key metadata from the document text itself.

Output Format:
Provide the output as a single JSON object with two top-level keys: "extracted_metadata" and "medical_events".

1.  **`extracted_metadata`** (Object, all fields are optional - return null if not found):
    *   `document_date` (String | Null): The primary date associated with the document (e.g., report date, visit date, prescription date) in "YYYY-MM-DD" format. If multiple dates exist, choose the most representative one for the document as a whole.
    *   `source_name` (String | Null): The primary source of the document (e.g., Doctor's name, Clinic name, Hospital name, Lab name).
    *   `source_location_city` (String | Null): The city associated with the source, if mentioned.
    *   `tags` (List[String] | Null): A list of 5-10 key medical terms, conditions, medications, procedures, or topics found in the document. Choose the most salient terms.

2.  **`medical_events`** (List[Object]): Each object in the list represents a distinct piece of information from the document. Include the following fields for each event object:
    *   `event_type` (String): Category (e.g., "Symptom", "Diagnosis", "Medication", "LabResult", "VitalSign", "Procedure", "Observation", "Allergy", "Immunization", "ClinicalFinding", "PatientInstruction").
    *   `description` (String): Core information or description (e.g., "headache", "Type 2 Diabetes Mellitus", "Lisinopril 10mg", "Fasting Blood Sugar", "Appendectomy").
    *   `value` (String | Null): Specific value, if applicable (e.g., "120", "10mg").
    *   `units` (String | Null): Units for the value, if applicable (e.g., "mg/dL", "mg", "bpm").
    *   `date_time` (String | Null): Specific date/time for this event (YYYY-MM-DD HH:MM:SS or YYYY-MM-DD), potentially different from the overall document_date.
    *   `body_location` (String | Null): Body location, if applicable (e.g., "left arm", "abdomen").
    *   `qualifiers` (String or List[String] | Null): Modifiers, status, context (e.g., "mild", "acute", "chronic", "history of", "resolved", "ongoing").
    *   `raw_text_snippet` (String): The exact snippet from the original text this item was derived from (IMPORTANT!).
    *   `notes` (String | Null): Any additional relevant context or notes.

Example Output Structure:
```json
{
  "extracted_metadata": {
    "document_date": "2024-03-15",
    "source_name": "Central City Laboratory",
    "source_location_city": "Central City",
    "tags": ["Blood Test", "Metabolic Panel", "Glucose", "Cholesterol", "Routine Checkup"]
  },
  "medical_events": [
    {
      "event_type": "LabResult",
      "description": "Fasting Blood Sugar",
      "value": "110",
      "units": "mg/dL",
      "date_time": "2024-03-15",
      "body_location": null,
      "qualifiers": null,
      "raw_text_snippet": "Fasting Blood Sugar: 110 mg/dL on 2024-03-15",
      "notes": "Reference Range: 70-100 mg/dL"
    },
    {
      "event_type": "LabResult",
      "description": "Total Cholesterol",
      "value": "190",
      "units": "mg/dL",
      "date_time": "2024-03-15",
      "body_location": null,
      "qualifiers": null,
      "raw_text_snippet": "Total Cholesterol ............. 190 mg/dL",
      "notes": "Desirable: < 200 mg/dL"
    }
    // ... more medical_events ...
  ]
}
```

Guidelines:
*   Ensure the entire output is a single, valid JSON object starting with `{` and ending with `}`.
*   For `extracted_metadata`, prioritize finding the single most representative date and source for the whole document.
*   For `tags`, select terms that best summarize the document's key content.
*   For `medical_events`, capture as much detail as possible. The `raw_text_snippet` is crucial.
*   If the document contains a narrative, break it down into discrete observations within `medical_events`.
*   Focus solely on structuring the information from the single document provided.
'''

def structure_text_with_gemini(api_key: str, raw_text: str) -> Optional[str]:
    """
    Sends raw text to Gemini Flash model for structured data and metadata extraction 
    based on the enhanced medical system prompt.

    Args:
        api_key: The API key for Google Generative AI.
        raw_text: The raw text extracted from a document.

    Returns:
        A JSON string representing an object with keys 'extracted_metadata' and 'medical_events',
        or None on failure or if the output format is invalid.
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
                temperature=0.1, # Lower temperature for more deterministic, structured output
                response_mime_type="application/json" # Force JSON output directly
            )
        )
        
        response = model.generate_content(raw_text)
        
        if response.parts:
            llm_output = response.text
            logger.info(f"Received response from Gemini Flash (length: {len(llm_output)}) for structuring.")
            
            # Basic check: Should be a JSON object now, not potentially a list
            if llm_output.strip().startswith("{") and llm_output.strip().endswith("}"):
                # Deeper validation (optional but recommended): Check for required keys
                try:
                    parsed_output = json.loads(llm_output)
                    if 'extracted_metadata' in parsed_output and 'medical_events' in parsed_output:
                        logger.info("Gemini output format validated (contains top-level keys).")
                        return llm_output
                    else:
                        logger.warning("Gemini output is JSON object but missing required top-level keys ('extracted_metadata', 'medical_events').")
                        return None # Treat as invalid format
                except json.JSONDecodeError:
                    logger.warning("Gemini output starts/ends with {} but is not valid JSON.")
                    return None # Invalid JSON
            else:
                logger.warning(f"Gemini output does not appear to be a valid JSON object. Output: {llm_output[:500]}...")
                # Fallback: attempt to extract JSON object from markdown code blocks
                json_content = None
                
                # Try multiple patterns for extracting JSON
                if "```json" in llm_output:
                    try:
                        # Extract content between ```json and ```
                        json_content = llm_output.split("```json")[1].split("```")[0].strip()
                    except IndexError:
                        logger.warning("Found ```json marker but could not extract content")
                elif "```" in llm_output and "{" in llm_output:
                    try:
                        # Look for any code block that contains JSON
                        parts = llm_output.split("```")
                        for part in parts:
                            if part.strip().startswith("{") and part.strip().endswith("}"):
                                json_content = part.strip()
                                break
                    except Exception:
                        pass
                
                # If we found potential JSON content, validate it
                if json_content and json_content.startswith("{") and json_content.endswith("}"):
                    try:
                        parsed_output = json.loads(json_content)
                        if 'extracted_metadata' in parsed_output and 'medical_events' in parsed_output:
                            logger.info("Successfully extracted and validated JSON object from markdown block.")
                            return json_content
                        else:
                            logger.warning("Extracted JSON object from markdown block is missing required keys.")
                            return None
                    except json.JSONDecodeError as parse_error:
                        logger.warning(f"Could not parse extracted JSON content: {parse_error}")
                        logger.warning(f"Extracted content: {json_content[:200]}...")
                        return None
                
                logger.warning("Could not extract valid JSON from Gemini response")
                return None # Output wasn't a JSON object
        else:
            logger.warning("Gemini response has no parts or text for structuring.")
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
        
        response = await _async(system_prompt) # Pass the whole crafted prompt
        
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

# --- New Function for Query Filter Extraction (LLM Call 2) ---
async def extract_query_filters_with_gemini(api_key: str, query_text: str) -> Optional[str]:
    """
    Analyzes a natural language query to extract structured filter parameters 
    based on available Document metadata.

    Args:
        api_key: The API key for Google Generative AI.
        query_text: The natural language query from the user.

    Returns:
        A JSON string representing the extracted filters, or None on failure.
        Returns an empty JSON object string '{}' if no specific filters are identified.
    """
    if not query_text.strip():
        logger.warning("Received empty query text for filter extraction. Returning no filters.")
        return "{}" # Return empty JSON object

    # Define the filterable fields from the Document model
    # Keep this updated if the Document model changes
    filterable_fields_context = {
        "description": "Extract filter parameters based on these Document metadata fields:",
        "fields": [
            {"name": "document_type", "type": "Enum", "values": ["PRESCRIPTION", "LAB_RESULT", "OTHER"], "description": "Type of document"},
            {"name": "document_date", "type": "Date (YYYY-MM-DD)", "description": "Actual date on the document"},
            {"name": "upload_timestamp", "type": "DateTime (YYYY-MM-DD HH:MM:SS)", "description": "When the document was uploaded"},
            {"name": "source_name", "type": "String", "description": "Doctor, lab, hospital, etc."}, 
            {"name": "source_location_city", "type": "String", "description": "City of the source"},
            {"name": "tags", "type": "List[String]", "description": "Keywords extracted from document content by AI"},
            {"name": "user_added_tags", "type": "List[String]", "description": "Tags added manually by the user"},
            {"name": "related_to_health_goal_or_episode", "type": "String", "description": "User-defined health goal or episode link"},
            {"name": "original_filename", "type": "String", "description": "The original uploaded filename"}
        ],
        "notes": "Focus on extracting criteria that match these fields. Date comparisons should consider ranges (e.g., 'last year', 'March 2023'). Text matching should often be case-insensitive and partial (contains). Multiple tags can be combined."
    }

    # Define the desired output structure
    output_format_instructions = {
        "description": "Return a JSON object containing identified filters. Use the keys below. Omit keys if no corresponding filter is found in the query. If no filters are found, return an empty JSON object {}.",
        "keys": {
            "document_type": "String (e.g., 'LAB_RESULT')",
            "date_range": "Object with 'start_date' and 'end_date' (YYYY-MM-DD)",
            "source_name_contains": "String (for partial match)",
            "source_location_city_equals": "String (for exact match)",
            "tags_include_all": "List[String] (all tags must be present)",
            "tags_include_any": "List[String] (any of these tags must be present)", 
            "user_tags_include_all": "List[String]",
            "user_tags_include_any": "List[String]",
            "episode_equals": "String (exact match)",
            "filename_contains": "String (for partial match)"
        },
        "example_output_for_query_glucose_labs_last_year": {
            "document_type": "LAB_RESULT",
            "date_range": {"start_date": "YYYY-01-01", "end_date": "YYYY-12-31"}, # Assuming YYYY is last year
            "tags_include_any": ["glucose", "blood sugar"]
        }
    }

    system_prompt = f"""
    You are an AI assistant specialized in analyzing user queries about their medical documents.
    Your task is to extract filter parameters from the user's query based on the available metadata fields of the documents. 
    Do not answer the query itself; only extract the filter criteria.

    Available filterable fields on documents:
    {json.dumps(filterable_fields_context, indent=2)}

    Desired output format instructions:
    {json.dumps(output_format_instructions, indent=2)}

    User Query: "{query_text}"

    Analyze the User Query and return ONLY a single JSON object containing the identified filters according to the Desired output format instructions. 
    If the query doesn't seem to imply any specific filters based on the available fields, return an empty JSON object: {{}}.
    Handle date expressions like 'last month', 'this year', 'January 2023' by defining a 'date_range' with 'start_date' and 'end_date' in 'YYYY-MM-DD' format. You might need to infer the current date to calculate ranges like 'last month' - assume today's date if needed for calculation, but return specific dates. 
    For text fields like source_name or filename, prefer 'contains' style matching unless exact match is implied.
    For tags, try to determine if the user means ALL specified tags must match ('tags_include_all') or if ANY of the tags matching is sufficient ('tags_include_any'). Default to 'tags_include_any' if ambiguous.
    Ensure the output is only the JSON object, with no surrounding text or markdown formatting.
    """
    
    logger.info(f"Sending query to Gemini for filter extraction: '{query_text}'")
    logger.debug(f"Gemini System Prompt for Filter Extraction:\n{system_prompt}")

    try:
        genai.configure(api_key=api_key)
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]

        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest',
            system_instruction=system_prompt, # Pass prompt via system_instruction
            safety_settings=safety_settings,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1, # Low temperature for deterministic JSON output
                response_mime_type="application/json" # Request JSON output explicitly
            )
        )
        
        # Pass empty content as the prompt is in system_instruction now for Gemini 1.5
        # Or pass the query again if system_instruction doesn't fully take complex prompts.
        # Let's try passing the query again in the content for clarity.
        response = await model.generate_content_async(query_text,generation_config = {
    "response_mime_type": "application/json"
})
        
        if response.parts:
            filter_json_str = response.text
            logger.info(f"Received filter parameters from Gemini: {filter_json_str}")
            # Validate if it looks like JSON
            if filter_json_str.strip().startswith("{") and filter_json_str.strip().endswith("}"):
                return filter_json_str
            else:
                logger.warning(f"LLM output for filter extraction does not appear to be valid JSON: {filter_json_str[:500]}")
                # Attempt extraction from markdown, although mime_type should prevent it.
                if "```json" in filter_json_str:
                    try:
                        json_block = filter_json_str.split("```json")[1].split("```")[0].strip()
                        if json_block.strip().startswith("{") and json_block.strip().endswith("}"):
                           logger.info("Successfully extracted JSON filters from markdown code block.")
                           return json_block
                    except IndexError:
                       logger.warning("Could not extract JSON filters from markdown block.")
                logger.warning("Returning empty filters due to invalid JSON format from LLM.")
                return "{}" # Return empty JSON if parsing failed or format is wrong
        else:
            logger.warning("Gemini response for filter extraction has no parts or text.")
            if response.prompt_feedback:
                logger.warning(f"Prompt Feedback for filter extraction: {response.prompt_feedback}")
            return None # Indicate failure

    except Exception as e:
        logger.error(f"Exception during Gemini API call for filter extraction: {e}", exc_info=True)
        return None 

# System Prompt for Answering Questions based on Filtered Context (LLM Call 3)
SYSTEM_PROMPT_ANSWER_FROM_FILTERED_CONTEXT = '''
You are a helpful AI assistant. Your task is to answer the user's question based *solely* on the provided JSON context.
The JSON context contains a list of "medical_events" extracted from relevant medical documents. Each event has details like type, description, value, units, date, etc.

User's Question: {query_text}

JSON Context:
```json
{json_data_context}
```

Guidelines:
- Answer the question clearly and concisely.
- Base your answer *only* on the information found in the provided JSON context. Do not use any external knowledge or make assumptions.
- If the answer cannot be found in the provided context, explicitly state that the information is not available in the provided documents.
- If relevant, you can refer to specific details from the `medical_events` in your answer.
- Present the answer in a natural, human-readable format.
'''

async def answer_query_with_filtered_context_gemini(api_key: str, query_text: str, json_data_context: str) -> Optional[str]:
    """
    Answers a user's query based on a provided filtered JSON context using Gemini. (LLM Call 3)

    Args:
        api_key: The API key for Google Generative AI.
        query_text: The user's original natural language query.
        json_data_context: A string containing the JSON data (list of medical_events)
                           from filtered documents, to be used as context.

    Returns:
        A string containing the LLM's answer, or None on failure.
    """
    if not query_text.strip():
        logger.warning("Received empty query text for Gemini answering. Skipping.")
        return None
    if not json_data_context.strip():
        logger.warning("Received empty JSON data context for Gemini answering. Skipping.")
        # Or, could return a message like "No relevant documents found to answer your query."
        return "No information was found in your documents that could answer this query."


    logger.info(f"Sending query and filtered context (context length: {len(json_data_context)}) to Gemini for answering...")
    try:
        genai.configure(api_key=api_key)

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]

        # Format the full prompt including the user's query and the context
        # We'll pass the system prompt as a system_instruction and the combined user query + context as the main content.
        # The prompt template approach is better handled by f-string for this model's API.
        
        # The user's "turn" or prompt to the model will be the question plus the context.
        # The system prompt will guide its overall behavior.
        # The `SYSTEM_PROMPT_ANSWER_FROM_FILTERED_CONTEXT` is a bit meta here, as it describes the whole interaction.
        # A more direct system instruction for Gemini would be:
        # "You are a helpful AI assistant. Answer the user's question based *solely* on the provided JSON context..."
        # And then the user content would be:
        # "User's Question: {query_text}\n\nJSON Context:\n```json\n{json_data_context}\n```"

        system_instruction = (
            "You are a helpful AI assistant. Your task is to answer the user's question based "
            "*solely* on the provided JSON context. The JSON context contains a list of 'medical_events' "
            "extracted from relevant medical documents. Each event has details like type, description, value, "
            "units, date, etc. If the answer cannot be found in the provided context, explicitly state that "
            "the information is not available in the provided documents. Present the answer in a natural, "
            "human-readable format."
        )
        
        prompt_content = f"User's Question: {query_text}\\n\\nJSON Context:\\n```json\\n{json_data_context}\\n```"

        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest', # Using 1.5 flash for potentially better reasoning
            system_instruction=system_instruction,
            safety_settings=safety_settings,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2 # Slightly higher for more natural language answers, but still grounded
            )
        )
        
        response = await model.generate_content_async(prompt_content) # Use async version
        
        if response.parts:
            answer = response.text
            logger.info(f"Received answer from Gemini (length: {len(answer)}).")
            return answer
        else:
            logger.warning("Gemini response for answering has no parts or text.")
            if response.prompt_feedback:
                logger.warning(f"Prompt Feedback for answering: {response.prompt_feedback}")
            return "I apologize, I encountered an issue generating an answer. Please try again."

    except Exception as e:
        logger.error(f"Exception during Gemini API call for answering: {e}", exc_info=True)
        return "I apologize, an error occurred while trying to answer your question." 