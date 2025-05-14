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
    ASYNC_DATABASE_URL: Optional[str] = None # Added for async operations
    
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
        
        if isinstance(v, str):
            if environment == "test":
                return v 
            else:
                try:
                    # Attempt to parse as PostgresDsn. If it fails, Pydantic handles the error.
                    return PostgresDsn(v)
                except ValueError as e: # Catch Pydantic's validation error if v is not a valid PostgresDsn
                    raise ValueError(f"Invalid DATABASE_URL for {environment} environment: {v}. Must be a valid PostgreSQL DSN. Error: {e}")
        
        # This part of building from components is likely fine as it returns PostgresDsn directly
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

    @validator("ASYNC_DATABASE_URL", pre=True, always=True)
    def assemble_async_db_connection(cls, v: Optional[str], values: dict) -> Optional[str]:
        if isinstance(v, str):
            if not v.startswith("postgresql+asyncpg://"):
                raise ValueError("ASYNC_DATABASE_URL must use the 'postgresql+asyncpg://' scheme.")
            return v
        
        sync_db_url_value = values.get("DATABASE_URL")
        
        # sync_db_url_value at this point (after assemble_db_connection validator has run)
        # will be either a Pydantic PostgresDsn object or a string (for test env).
        # We need its string representation to modify the scheme.
        
        sync_db_url_str: Optional[str] = None
        if hasattr(sync_db_url_value, '__str__'): # Check if it's a Pydantic DSN object or similar
            sync_db_url_str = str(sync_db_url_value)
        elif isinstance(sync_db_url_value, str):
            sync_db_url_str = sync_db_url_value

        if sync_db_url_str and sync_db_url_str.startswith("postgresql://"):
            return sync_db_url_str.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif sync_db_url_str and sync_db_url_str.startswith("sqlite:///") and values.get("ENVIRONMENT") == "test":
            # If deriving from a synchronous SQLite URL for tests
            return sync_db_url_str.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        
        logger = logging.getLogger(__name__)
        logger.warning(
            "ASYNC_DATABASE_URL not explicitly set and could not be derived from DATABASE_URL. "
            "Async database operations will not be available unless it's configured."
        )
        return None

    # Reverted Pydantic V1 style Config class
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = 'ignore'

settings = Settings() 