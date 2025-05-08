import os
import pytest
from unittest.mock import patch, MagicMock

# Set environment variables for unit tests
os.environ["DATABASE_URL"] = "postgresql://fake:fake@localhost/fakedb"
os.environ["SUPABASE_URL"] = "https://test-unit.supabase.co"
os.environ["SUPABASE_KEY"] = "test-unit-key"
os.environ["SUPABASE_JWT_SECRET"] = "test-unit-jwt-secret"

# Don't use autouse=True to avoid conflicts with main conftest
@pytest.fixture(scope="module")
def unit_settings():
    """Override settings for unit tests"""
    with patch("app.core.config.settings") as mock_settings:
        mock_settings.DATABASE_URL = os.environ["DATABASE_URL"]
        mock_settings.ENVIRONMENT = "test"
        mock_settings.SUPABASE_URL = os.environ["SUPABASE_URL"]
        mock_settings.SUPABASE_KEY = os.environ["SUPABASE_KEY"]
        mock_settings.SUPABASE_JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]
        mock_settings.GCP_PROJECT_ID = "test-unit-project"
        mock_settings.DOCUMENT_AI_PROCESSOR_LOCATION = "us"
        mock_settings.DOCUMENT_AI_PROCESSOR_ID = "test-unit-processor"
        mock_settings.GEMINI_API_KEY = "test-unit-key"
        yield mock_settings

@pytest.fixture
def mock_db():
    """Provide a mock database session for unit tests"""
    db = MagicMock()
    yield db 