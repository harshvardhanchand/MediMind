import os
from typing import List, Optional, Union

from pydantic import PostgresDsn, validator, AnyHttpUrl
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Core application settings
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    PROJECT_NAME: str = "Medical Data Hub API"
    API_V1_STR: str = "/api/v1"
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React Native development server
        "http://localhost:19006",  # Expo web
        "exp://localhost:19000",   # Expo Go app
    ]
    
    # Authentication settings
    SUPABASE_URL: Optional[AnyHttpUrl] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    
    # Database settings
    DATABASE_URL: Optional[PostgresDsn] = None
    
    # Security settings
    SECURITY_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 8 days
    RATE_LIMIT_DEFAULT: str = "60/minute"  # Default rate limit
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # GCP settings
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    GCP_STORAGE_BUCKET: str = os.getenv("GCP_STORAGE_BUCKET", "")

    # Document AI specific settings
    DOCUMENT_AI_PROCESSOR_LOCATION: Optional[str] = os.getenv("DOCUMENT_AI_PROCESSOR_LOCATION")
    DOCUMENT_AI_PROCESSOR_ID: Optional[str] = os.getenv("DOCUMENT_AI_PROCESSOR_ID")

    # Gemini API Key
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")

    # Google Cloud Storage (GCS) - Kept for potential compatibility
    GCS_BUCKET_NAME: Optional[str] = None

    @validator("DATABASE_URL", pre=True, always=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v # Use direct DATABASE_URL if provided
        
        # Build from components if DATABASE_URL not provided directly
        user = values.get("POSTGRES_USER")
        password = values.get("POSTGRES_PASSWORD")
        server = values.get("POSTGRES_SERVER")
        db_name = values.get("POSTGRES_DB")
        if all([user, password, server, db_name]):
            # Use a synchronous scheme like 'postgresql' or 'postgresql+psycopg2'
            # Using 'postgresql' which usually defaults to psycopg2 if installed.
            return str(PostgresDsn.build(
                scheme="postgresql",
                username=user,
                password=password,
                host=server,
                path=f"/{db_name}",
            ))
        
        # If neither direct URL nor all components are available, raise error.
        # This makes DATABASE_URL effectively required via one of the methods.
        raise ValueError("Missing PostgreSQL connection parameters or direct DATABASE_URL")

    # Reverted Pydantic V1 style Config class
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = 'ignore'

settings = Settings() 