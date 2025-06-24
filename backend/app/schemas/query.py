from pydantic import BaseModel
from typing import List, Optional
import uuid


class QueryRequest(BaseModel):
    query_text: str

class NaturalLanguageQueryResponse(BaseModel):
    query_text: str
    answer: str
    relevant_document_ids: Optional[List[uuid.UUID]] = None
   