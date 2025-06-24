import os
from typing import List, Optional, Union
import logging

from pydantic import PostgresDsn, field_validator, AnyHttpUrl, ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore'
    )
    
    # Core application settings
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    PROJECT_NAME: str = "Medical Data Hub API"
    
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React Native development server
        "http://localhost:19006",  # Expo web
        "exp://localhost:19000",   # Expo Go app
        "http://192.168.1.2:8082", # Expo development build
        "http://192.168.1.2:8081", # Alternative Expo port
        "http://192.168.1.2:8083", # Another Expo port
        "http://localhost:8082",   # Localhost version
        "http://localhost:8081",   # Alternative localhost port
        "http://localhost:8083",   # Another localhost port
    ]
    
    # Authentication settings
    SUPABASE_URL: Optional[AnyHttpUrl] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    
    # Database settings
    DATABASE_URL: Optional[Union[PostgresDsn, str]] = None
    ASYNC_DATABASE_URL: Optional[str] = None 
    
    # Security settings
    SECURITY_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  
    RATE_LIMIT_DEFAULT: str = "60/minute"  
    
   
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    GCP_STORAGE_BUCKET: str = os.getenv("GCP_STORAGE_BUCKET", "")

    
    DOCUMENT_AI_PROCESSOR_LOCATION: Optional[str] = os.getenv("DOC_AI_LOCATION")
    DOCUMENT_AI_PROCESSOR_ID: Optional[str] = os.getenv("DOC_AI_PROCESSOR_ID")

    
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")

    # Google Cloud Storage (GCS) - Kept for potential compatibility
    GCS_BUCKET_NAME: Optional[str] = None

    @field_validator("DATABASE_URL", mode='before')
    @classmethod
    def assemble_db_connection(cls, v: Optional[str]) -> Union[PostgresDsn, str]:
        environment = os.getenv("ENVIRONMENT", "development")
        
        if isinstance(v, str):
            if environment == "test":
                return v 
            else:
                try:
                    
                    return PostgresDsn(v)
                except ValueError as e:
                    raise ValueError(f"Invalid DATABASE_URL for {environment} environment: {v}. Must be a valid PostgreSQL DSN. Error: {e}")
        
        if environment == "test" and not v:
             raise ValueError("DATABASE_URL must be provided for the test environment (e.g., sqlite:///./test.db)")
        
        
        if environment != "test" and not v:
            raise ValueError("Missing PostgreSQL connection parameters or direct DATABASE_URL for non-test environment")
        
       
        if environment == "test":
            logger = logging.getLogger(__name__)
            logger.warning("DATABASE_URL not explicitly set for test environment, defaulting to in-memory SQLite. This might not be intended for all tests.")
            return "sqlite:///./test_default.db"

        return v

    @field_validator("ASYNC_DATABASE_URL", mode='before')
    @classmethod
    def assemble_async_db_connection(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            if not v.startswith("postgresql+asyncpg://"):
                raise ValueError("ASYNC_DATABASE_URL must use the 'postgresql+asyncpg://' scheme.")
            return v
        
        
        sync_db_url_str = os.getenv("DATABASE_URL")
        
        if sync_db_url_str and sync_db_url_str.startswith("postgresql://"):
            return sync_db_url_str.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif sync_db_url_str and sync_db_url_str.startswith("sqlite:///") and os.getenv("ENVIRONMENT") == "test":
            return sync_db_url_str.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        
        logger = logging.getLogger(__name__)
        logger.warning(
            "ASYNC_DATABASE_URL not explicitly set and could not be derived from DATABASE_URL. "
            "Async database operations will not be available unless it's configured."
        )
        return None

settings = Settings() 

 