from fastapi import APIRouter
from app.api.endpoints import users, medications, documents, query, extracted_data, health_readings, medical_analysis, symptoms
from app.routers import notifications


api_router = APIRouter()


api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(medications.router, prefix="/medications", tags=["medications"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(extracted_data.router, prefix="/extracted_data", tags=["extracted_data"])
api_router.include_router(query.router, prefix="/query", tags=["query"])
api_router.include_router(health_readings.router, prefix="/health_readings", tags=["health_readings"])
api_router.include_router(symptoms.router, prefix="/symptoms", tags=["symptoms"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(medical_analysis.router, prefix="/medical-analysis", tags=["medical-analysis"])