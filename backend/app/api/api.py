from fastapi import APIRouter
from app.api.endpoints import health, me, documents, extracted_data, symptoms
from app.api.endpoints import query

api_router = APIRouter()


api_router.include_router(health.router, prefix="/health", tags=["health"])


api_router.include_router(me.router, prefix="/me", tags=["me"])


api_router.include_router(documents.router, prefix="/documents", tags=["documents"])


api_router.include_router(extracted_data.router, prefix="/extracted_data", tags=["extracted_data"])


api_router.include_router(symptoms.router, prefix="/symptoms", tags=["symptoms"])


api_router.include_router(query.router, prefix="/query", tags=["query"]) 