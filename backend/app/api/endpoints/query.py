from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
import json # For formatting the JSON context
from datetime import date # Added for date range handling
from typing import Any, Optional, Tuple, List
import uuid

from app.schemas.query import QueryRequest, NaturalLanguageQueryResponse # Updated schema
from app.core.auth import verify_token, get_user_id_from_token # Added get_user_id_from_token
from app.db.session import get_db
# Renamed and changed signature for the AI processor function
from app.utils.ai_processors import extract_query_filters_with_gemini, answer_query_with_filtered_context_gemini
from app.core.config import settings
# Need ExtractedDataRepository to fetch user's data
from app.repositories.extracted_data_repo import ExtractedDataRepository
from app.repositories.document_repo import document_repo # Assuming singleton instance

logger = logging.getLogger(__name__)
router = APIRouter()

# Helper function to interpret relative dates (can be expanded)
# This is a simple example; a robust version would use libraries or more logic
def resolve_date_range(date_filter: Any) -> Optional[Tuple[date, date]]:
    # TODO: Implement more robust relative date handling (e.g., "last_year", "last_month")
    # For now, assumes date_filter is an object with start_date and end_date
    if isinstance(date_filter, dict) and 'start_date' in date_filter and 'end_date' in date_filter:
        try:
            start = date.fromisoformat(date_filter['start_date'])
            end = date.fromisoformat(date_filter['end_date'])
            return start, end
        except (ValueError, TypeError):
            logger.warning(f"Could not parse date range from filter: {date_filter}")
            return None
    logger.warning(f"Received unexpected date filter format: {date_filter}")
    return None

@router.post("/", response_model=NaturalLanguageQueryResponse) # Updated response model
async def natural_language_query_endpoint(
    query_request: QueryRequest,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token) 
):
    """
    Answers a natural language query using a two-step LLM process:
    1. Extract filter criteria from the query based on Document metadata.
    2. Retrieve filtered documents and their data.
    3. Generate an answer based on the filtered data context.
    """
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not configured.")
        raise HTTPException(status_code=500, detail="Query processing not configured.")

    user_id = get_user_id_from_token(db_session=db, token_data=token_data)
    if not user_id:
        # This case should ideally be caught by verify_token if token is invalid or user not found
        logger.error(f"Could not retrieve user_id from token for query: {query_request.query_text}")
        raise HTTPException(status_code=403, detail="User not found or invalid token.")

    logger.info(f"Processing query: '{query_request.query_text}' for user_id: {user_id}")

    try:
        # --- Step 1: Extract Filters using LLM --- 
        logger.debug("Step 1: Extracting filters from query...")
        filter_json_str = await extract_query_filters_with_gemini(
            api_key=settings.GEMINI_API_KEY,
            query_text=query_request.query_text
        )

        if filter_json_str is None:
            logger.error(f"LLM filter extraction failed for query: {query_request.query_text}")
            raise HTTPException(status_code=500, detail="Failed to analyze query for filtering.")

        try:
            extracted_filters = json.loads(filter_json_str)
            logger.info(f"Extracted filters: {extracted_filters}")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON filters from LLM: {filter_json_str}")
            # Proceed without filters if LLM returns invalid JSON
            extracted_filters = {}

        # --- Step 2: Retrieve Filtered Documents --- 
        logger.debug("Step 2: Retrieving filtered documents...")
        # TODO: Implement document_repo.get_multi_by_filters
        # This function will need to translate extracted_filters into SQLAlchemy conditions
        
        # Placeholder implementation - needs actual filtering logic in repository
        # For now, let's retrieve all documents and simulate filtering conceptually
        # REPLACE THIS with call to actual repository method later
        
        # Conceptual filtering based on extracted filters (will be moved to repository)
        query_filters = {}
        if extracted_filters.get("document_type"):
             query_filters["document_type"] = extracted_filters["document_type"]
        if extracted_filters.get("date_range"):
            resolved_range = resolve_date_range(extracted_filters["date_range"])
            if resolved_range:
                query_filters["document_date_range"] = resolved_range # Use a key the repo understands
        # Add logic for other filters: source_name, tags, user_tags etc.
        # ... Example for tags ...
        if extracted_filters.get("tags_include_any"):
            query_filters["tags_include_any"] = extracted_filters["tags_include_any"]
        # Add more filter conversions here...
        
        # ASSUMING get_multi_by_filters takes user_id and a dictionary of filters
        filtered_documents = document_repo.get_multi_by_filters(db=db, user_id=user_id, filters=query_filters)

        if not filtered_documents:
            logger.info(f"No documents found matching filters for user_id: {user_id}")
            return NaturalLanguageQueryResponse(
                query_text=query_request.query_text,
                answer="I couldn't find any documents matching your specific criteria. You might want to broaden your search.",
                relevant_document_ids=[] # Return empty list
            )

        # --- Step 3: Prepare Context and Answer using LLM --- 
        logger.debug(f"Step 3: Preparing context from {len(filtered_documents)} documents and generating answer...")
        extracted_data_repo = ExtractedDataRepository(db)
        user_json_contents = [] # This will become a list of medical_events lists
        all_medical_events = [] # This will be a flat list of all medical_events objects
        # Collect document IDs used for context
        context_document_ids: List[uuid.UUID] = [] 

        for doc in filtered_documents:
            # Fetch associated ExtractedData
            extracted_data = extracted_data_repo.get_by_document_id(doc.document_id)
            if extracted_data and extracted_data.content:
                # Check if 'medical_events' key exists and is a list
                medical_events_from_doc = extracted_data.content.get("medical_events")
                if isinstance(medical_events_from_doc, list):
                    all_medical_events.extend(medical_events_from_doc)
                    context_document_ids.append(doc.document_id) # Add doc ID if content used
                else:
                    logger.warning(f"Document {doc.document_id} has content but no 'medical_events' list or it's not a list.")
            else:
                logger.warning(f"No ExtractedData or no content for document_id: {doc.document_id}")


        if not all_medical_events: # Check if we gathered any medical events
            logger.warning(f"Filtered documents found, but no extractable medical_events for query: {query_request.query_text}")
            # This might happen if documents were filtered but their processing hasn't completed or content is empty/malformed
            return NaturalLanguageQueryResponse(
                query_text=query_request.query_text,
                answer="I found some documents that might match, but I couldn't retrieve the specific medical details needed to answer your question from them.",
                relevant_document_ids=[doc.document_id for doc in filtered_documents] # Return all filtered doc IDs
            )
        
        json_data_context_str = json.dumps(all_medical_events, indent=2) # Use all_medical_events
        
        # Limit context size if necessary (crude example)
        MAX_CONTEXT_TOKENS = 200000 # Example limit, adjust based on model and cost
        if len(json_data_context_str) > MAX_CONTEXT_TOKENS * 4: # Rough estimate: 1 token ~ 4 chars
            logger.warning(f"Context size potentially exceeds limit, truncating for query: {query_request.query_text}")
            # Add more sophisticated truncation or selection logic if needed
            json_data_context_str = json_data_context_str[:MAX_CONTEXT_TOKENS * 4] + "... [CONTEXT TRUNCATED] ..."

        # Call the answering LLM
        llm_answer = await answer_query_with_filtered_context_gemini( # Changed function call
            api_key=settings.GEMINI_API_KEY,
            query_text=query_request.query_text,
            json_data_context=json_data_context_str
        )

        if llm_answer is None:
            logger.error(f"LLM answering failed for query: {query_request.query_text}")
            raise HTTPException(status_code=500, detail="Failed to get an answer from the AI assistant based on the filtered documents.")
        
        logger.info(f"Successfully generated answer for query: '{query_request.query_text}'")

        return NaturalLanguageQueryResponse(
            query_text=query_request.query_text,
            answer=llm_answer,
            relevant_document_ids=context_document_ids # Use the collected document_ids
        )
    
    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        logger.error(f"Error during query processing for '{query_request.query_text}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the query.")

# The get_query_schema_context() function is no longer needed for this approach
# and can be removed from this file if it's not used elsewhere. 