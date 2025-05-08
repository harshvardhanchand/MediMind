from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
import json # For formatting the JSON context

from app.schemas.query import QueryRequest, NaturalLanguageQueryResponse # Updated schema
from app.core.auth import verify_token, get_user_id_from_token # Added get_user_id_from_token
from app.db.session import get_db
# Renamed and changed signature for the AI processor function
from app.utils.ai_processors import answer_query_from_context 
from app.core.config import settings
# Need ExtractedDataRepository to fetch user's data
from app.repositories.extracted_data_repo import ExtractedDataRepository

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=NaturalLanguageQueryResponse) # Updated response model
async def natural_language_query_endpoint(
    query_request: QueryRequest,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token) 
):
    """
    Answers a natural language query by providing the query and all of the user's 
    extracted JSON data as context to an LLM.
    """
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not configured.")
        raise HTTPException(status_code=500, detail="Query processing not configured.")

    user_id = get_user_id_from_token(db_session=db, token_data=token_data)
    if not user_id:
        # This case should ideally be caught by verify_token if token is invalid or user not found
        logger.error(f"Could not retrieve user_id from token for query: {query_request.query_text}")
        raise HTTPException(status_code=403, detail="User not found or invalid token.")

    logger.info(f"Received query: '{query_request.query_text}' for user_id: {user_id}")

    try:
        # 1. Fetch all ExtractedData for the user
        extracted_data_repo = ExtractedDataRepository(db)
        all_user_extracted_data_records = extracted_data_repo.get_all_by_user_id(user_id)
        
        if not all_user_extracted_data_records:
            logger.info(f"No extracted data found for user_id: {user_id}. Answering based on no data.")
            # LLM will be told there's no data in its context
            json_data_context_str = "[]" # Empty JSON array
        else:
            # Collate all the 'content' (JSONB) fields.
            # Each 'content' field from ExtractedData is already a dict/list (parsed from JSONB).
            # We want to pass these to the LLM, perhaps as a list of these dicts/lists.
            # So, we create a list of these content objects.
            user_json_contents = []
            for record in all_user_extracted_data_records:
                if record.content: # Ensure content is not None
                    user_json_contents.append(record.content)
            
            if not user_json_contents:
                 json_data_context_str = "[]"
            else:
                # Convert the list of Python dicts/lists into a single JSON string for the LLM prompt
                json_data_context_str = json.dumps(user_json_contents, indent=2) # Pretty print for prompt readability

        # 2. Call the LLM with the query and the collated JSON data context
        llm_answer = await answer_query_from_context(
            api_key=settings.GEMINI_API_KEY,
            query_text=query_request.query_text,
            json_data_context=json_data_context_str
        )

        if llm_answer is None: # Check for None, as the function can return None on error
            logger.error(f"LLM answering failed or returned empty for query: {query_request.query_text}")
            # The LLM function itself might return a user-friendly error message string
            # If it explicitly returns None, that's an unexpected internal error.
            raise HTTPException(status_code=500, detail="Failed to get an answer from the AI assistant.")
        
        logger.info(f"Successfully received answer for query: '{query_request.query_text}'")

        return NaturalLanguageQueryResponse(
            query_text=query_request.query_text,
            answer=llm_answer
        )
    
    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        logger.error(f"Error during query answering for '{query_request.query_text}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while answering the query.")

# The get_query_schema_context() function is no longer needed for this approach
# and can be removed from this file if it's not used elsewhere. 