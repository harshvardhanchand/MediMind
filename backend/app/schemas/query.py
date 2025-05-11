from pydantic import BaseModel
from typing import List, Optional
import uuid


class QueryRequest(BaseModel):
    query_text: str

class NaturalLanguageQueryResponse(BaseModel):
    query_text: str
    answer: str
    relevant_document_ids: Optional[List[uuid.UUID]] = None
    # We could add an optional field here too if the LLM provides source snippets or confidence
    # For now, keeping it simple. 