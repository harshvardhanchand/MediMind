from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    query_text: str

class NaturalLanguageQueryResponse(BaseModel):
    query_text: str
    answer: str
    # We could add an optional field here too if the LLM provides source snippets or confidence
    # For now, keeping it simple. 