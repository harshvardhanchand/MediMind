from fastapi import APIRouter
from app.api.endpoints import health, me, documents, extracted_data, symptoms
from app.api.endpoints import query

api_router = APIRouter()

# Health check
api_router.include_router(health.router, prefix="/health", tags=["health"])

# User endpoints
api_router.include_router(me.router, prefix="/me", tags=["me"])

# Document endpoints
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

# ExtractedData endpoints
api_router.include_router(extracted_data.router, prefix="/extracted_data", tags=["extracted_data"])

# Symptoms endpoints
api_router.include_router(symptoms.router, prefix="/symptoms", tags=["symptoms"])

# Query interpretation endpoint
api_router.include_router(query.router, prefix="/query", tags=["query"]) 