from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
import logging
import json 
from datetime import date 
from typing import Any, Optional, Tuple, List
import uuid
import google.generativeai as genai
from pydantic import BaseModel, Field, validator

from app.schemas.query import QueryRequest, NaturalLanguageQueryResponse 
from app.core.auth import verify_token, get_user_id_from_token 
from app.db.session import get_db

from app.utils.ai_processors import extract_query_filters_with_gemini, answer_query_with_filtered_context_gemini
from app.core.config import settings

from app.models.extracted_data import ExtractedData
from app.repositories.extracted_data_repo import ExtractedDataRepository
from app.repositories.document_repo import document_repo 

logger = logging.getLogger(__name__)
router = APIRouter()


extracted_data_repo = ExtractedDataRepository(ExtractedData)


if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)


class DateRangeFilter(BaseModel):
    start_date: str = Field(..., description="ISO format date string")
    end_date: str = Field(..., description="ISO format date string")
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        try:
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("Date must be in ISO format (YYYY-MM-DD)")

class ExtractedFilters(BaseModel):
    document_type: Optional[str] = Field(None, pattern="^(prescription|lab_result|imaging_report|consultation_note|discharge_summary|other)$")
    date_range: Optional[DateRangeFilter] = None
    source_name: Optional[str] = Field(None, max_length=200)
    tags_include_any: Optional[List[str]] = Field(None, max_items=10)
    tags_include_all: Optional[List[str]] = Field(None, max_items=10)
    
    class Config:
        extra = "forbid"  # Reject any unexpected fields

async def classify_and_handle_general_query(api_key: str, query_text: str) -> Optional[str]:
    """
    Uses LLM to classify if a query is general conversation vs medical-specific.
    If general, provides a natural conversational response.
    If medical, returns None to proceed with medical document pipeline.
    """
    system_prompt = """
    You are a health assistant AI. Analyze the user's query and determine if it's:
    1. General conversation (greetings, how are you, what can you do, general chat)
    2. Medical-specific (asking about medications, lab results, symptoms, health data)

    If it's GENERAL conversation:
    - Respond naturally and helpfully as a health assistant
    - Mention that you can help with medical questions when they have documents
    - Be warm and conversational

    If it's MEDICAL-specific:
    - Respond with exactly: "MEDICAL_QUERY"

    Examples:
    - "Hello" → Natural greeting response
    - "How are you?" → Natural friendly response  
    - "What can you do?" → Explain capabilities naturally
    - "Tell me about my medications" → "MEDICAL_QUERY"
    - "What were my lab results?" → "MEDICAL_QUERY"
    """

    try:
        
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction=system_prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.7)
        )
        
        response = await model.generate_content_async(query_text)
        
        if response.parts:
            answer = response.text.strip()
            if answer == "MEDICAL_QUERY":
                return None  
            else:
                return answer  #
        
        return None
        
    except Exception as e:
        logger.error(f"Error in query classification: {e}")
        return None


def resolve_date_range(date_filter: Any) -> Optional[Tuple[date, date]]:
    
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

@router.post("/", response_model=NaturalLanguageQueryResponse) 
async def natural_language_query_endpoint(
    query_request: QueryRequest,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token) 
):
    """
    Answers a natural language query using a smart classification system:
    1. First classify if it's general conversation vs medical-specific
    2. Handle general conversation naturally with LLM
    3. For medical queries, use the document-based pipeline
    """
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not configured.")
        raise HTTPException(status_code=500, detail="Query processing not configured.")

    user_id = get_user_id_from_token(db_session=db, token_data=token_data)
    if not user_id:
       
        logger.error(f"Could not retrieve user_id from token for query: {query_request.query_text}")
        raise HTTPException(status_code=403, detail="User not found or invalid token.")

    logger.info(f"Processing query: '{query_request.query_text}' for user_id: {user_id}")

    
    general_response = await classify_and_handle_general_query(
        api_key=settings.GEMINI_API_KEY,  
        query_text=query_request.query_text
    )
    
    if general_response:
        logger.info(f"Handled as general conversation: {query_request.query_text}")
        return NaturalLanguageQueryResponse(
            query_text=query_request.query_text,
            answer=general_response,
            relevant_document_ids=[]
        )

    
    logger.info(f"Processing as medical query: {query_request.query_text}")

    try:
       
        logger.debug("Step 1: Extracting filters from query...")
        filter_json_str = await extract_query_filters_with_gemini(
            api_key=settings.GEMINI_API_KEY,  # Keep for now until ai_processors is updated
            query_text=query_request.query_text
        )

        if filter_json_str is None:
            logger.error(f"LLM filter extraction failed for query: {query_request.query_text}")
            raise HTTPException(status_code=500, detail="Failed to analyze query for filtering.")

        try:
            raw_filters = json.loads(filter_json_str)
            logger.debug(f"Raw LLM filters: {raw_filters}")
            
            # Validate using Pydantic schema
            validated_filters = ExtractedFilters(**raw_filters)
            extracted_filters = validated_filters.dict(exclude_none=True)
            logger.info(f"Validated filters: {extracted_filters}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON filters from LLM: {filter_json_str}, error: {e}")
            raise HTTPException(status_code=500, detail="AI returned malformed filter data")
        except Exception as e:
            logger.error(f"Failed to validate LLM filters: {raw_filters}, error: {e}")
            raise HTTPException(status_code=500, detail="AI returned invalid filter format")

        
        logger.debug("Step 2: Retrieving filtered documents...")
        
        
        # Conceptual filtering based on extracted filters (will be moved to repository)
        query_filters = {}
        if extracted_filters.get("document_type"):
             query_filters["document_type"] = extracted_filters["document_type"]
        if extracted_filters.get("date_range"):
            resolved_range = resolve_date_range(extracted_filters["date_range"])
            if resolved_range:
                query_filters["document_date_range"] = resolved_range # Use a key the repo understands
        
        if extracted_filters.get("tags_include_any"):
            query_filters["tags_include_any"] = extracted_filters["tags_include_any"]
        
        filtered_documents = await run_in_threadpool(
            document_repo.get_multi_by_filters, 
            db=db, 
            user_id=user_id, 
            filters=query_filters
        )

        if not filtered_documents:
            logger.info(f"No documents found matching filters for user_id: {user_id}")
            return NaturalLanguageQueryResponse(
                query_text=query_request.query_text,
                answer="I couldn't find any documents matching your specific criteria. You might want to broaden your search, or try uploading some medical documents first so I can help analyze your health data.",
                relevant_document_ids=[] 
            )

       
        logger.debug(f"Step 3: Preparing context from {len(filtered_documents)} documents and generating answer...")
        
        all_medical_events = []
        context_document_ids: List[uuid.UUID] = [] 

        for doc in filtered_documents:
            
            extracted_data = await run_in_threadpool(
                extracted_data_repo.get_by_document_id, 
                db=db, 
                document_id=doc.document_id
            )
            if extracted_data and extracted_data.content:
                
                medical_events_from_doc = extracted_data.content.get("medical_events")
                if isinstance(medical_events_from_doc, list):
                    all_medical_events.extend(medical_events_from_doc)
                    context_document_ids.append(doc.document_id) 
                else:
                    logger.warning(f"Document {doc.document_id} has content but no 'medical_events' list or it's not a list.")
            else:
                logger.warning(f"No ExtractedData or no content for document_id: {doc.document_id}")


        if not all_medical_events: 
            logger.warning(f"Filtered documents found, but no extractable medical_events for query: {query_request.query_text}")
            
            return NaturalLanguageQueryResponse(
                query_text=query_request.query_text,
                answer="I found some documents that might match, but I couldn't retrieve the specific medical details needed to answer your question from them.",
                relevant_document_ids=[doc.document_id for doc in filtered_documents]
            )
        
        
        MAX_CONTEXT_CHARS = 800000  
        
        json_data_context_str = json.dumps(all_medical_events, indent=2)
        
        if len(json_data_context_str) > MAX_CONTEXT_CHARS:
            logger.warning(f"Context size ({len(json_data_context_str)} chars) exceeds limit, intelligently truncating")
            
            
            truncated_events = all_medical_events
            while len(json.dumps(truncated_events, indent=2)) > MAX_CONTEXT_CHARS and truncated_events:
                
                remove_count = max(1, len(truncated_events) // 10)
                truncated_events = truncated_events[remove_count:]
            
            json_data_context_str = json.dumps(truncated_events, indent=2)
            logger.info(f"Truncated from {len(all_medical_events)} to {len(truncated_events)} medical events")

        
        llm_answer = await answer_query_with_filtered_context_gemini(
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
            relevant_document_ids=context_document_ids 
        )
    
    except HTTPException:
        
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error for query '{query_request.query_text}': {e}")
        raise HTTPException(status_code=500, detail="Failed to parse AI response data")
    except ValueError as e:
        logger.error(f"Value error during query processing for '{query_request.query_text}': {e}")
        raise HTTPException(status_code=400, detail="Invalid input data format") 
    except ConnectionError as e:
        logger.error(f"Connection error during query processing for '{query_request.query_text}': {e}")
        raise HTTPException(status_code=503, detail="External service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error during query processing for '{query_request.query_text}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the query")

