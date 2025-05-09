import os
from typing import List, Optional, Union
import logging

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
    DATABASE_URL: Optional[Union[PostgresDsn, str]] = None
    
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
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> Union[PostgresDsn, str]:
        environment = values.get("ENVIRONMENT")
        
        # ---- TEMPORARY DEBUG PRINT ----
        # print(f"[CONFIG DEBUG] Raw DATABASE_URL (v): {v}") # Removed
        # print(f"[CONFIG DEBUG] Environment: {environment}") # Removed
        # ---- END TEMPORARY DEBUG PRINT ----

        if isinstance(v, str):
            # If DATABASE_URL is directly provided as a string
            if environment == "test":
                # For test environment, allow any string (e.g., sqlite URL)
                return v 
            else:
                # For other environments, it must be a valid PostgresDsn
                try:
                    return PostgresDsn(v)
                except Exception as e: # Catch Pydantic's validation error if v is not a valid PostgresDsn
                    raise ValueError(f"Invalid DATABASE_URL for {environment} environment: {v}. Must be a valid PostgreSQL DSN. Error: {e}")
        
        # Build from components if DATABASE_URL not provided directly (only for non-test environments)
        if environment != "test":
            user = values.get("POSTGRES_USER")
            password = values.get("POSTGRES_PASSWORD")
            server = values.get("POSTGRES_SERVER")
            db_name = values.get("POSTGRES_DB")
            if all([user, password, server, db_name]):
                return PostgresDsn.build(
                    scheme="postgresql",
                    username=user,
                    password=password,
                    host=server,
                    path=f"/{db_name}",
                )
        elif environment == "test" and not v: # If test env and no DATABASE_URL provided, this is an issue
             raise ValueError("DATABASE_URL must be provided for the test environment (e.g., sqlite:///./test.db)")
        
        # If not test env and connection cannot be assembled, raise error.
        if environment != "test":
            raise ValueError("Missing PostgreSQL connection parameters or direct DATABASE_URL for non-test environment")
        
        # Fallback for test environment if v was None initially (should be caught by the elif above)
        # This part of the logic might be redundant given the check above.
        # However, ensuring a string path if all else fails for test env.
        if environment == "test":
            # This case should ideally not be reached if .env.test provides a DATABASE_URL
            logger = logging.getLogger(__name__) # Local import to avoid circular dependency if logger uses settings
            logger.warning("DATABASE_URL not explicitly set for test environment, defaulting to in-memory SQLite. This might not be intended for all tests.")
            return "sqlite:///./test_default.db" # Or a specific default like "sqlite:///:memory:"

        # This line should ideally not be reached if logic is correct.
        raise ValueError("Could not determine DATABASE_URL")

    # Reverted Pydantic V1 style Config class
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = 'ignore'

settings = Settings() 