from fastapi import APIRouter
# Removed auth from imports as backend auth endpoints are not used (Supabase client-side handles it)
from app.api.endpoints import users, medications, documents, query, extracted_data, health_readings, medical_analysis, symptoms
from app.routers import notifications

# This will be the main router for all API endpoints, mounted at /api
api_router = APIRouter()

# Include individual endpoint routers
# The prefixes here are relative to where api_router is mounted (e.g. /api)
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"]) # Removed auth router
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(medications.router, prefix="/medications", tags=["medications"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(extracted_data.router, prefix="/extracted_data", tags=["extracted_data"])
api_router.include_router(query.router, prefix="/query", tags=["query"])
api_router.include_router(health_readings.router, prefix="/health_readings", tags=["health_readings"])
api_router.include_router(symptoms.router, prefix="/symptoms", tags=["symptoms"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(medical_analysis.router, prefix="/medical-analysis", tags=["medical-analysis"])