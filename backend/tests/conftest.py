import os
import pytest
from unittest.mock import patch

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables before tests run."""
    # Set mock environment variables for testing
    os.environ["SUPABASE_URL"] = "https://example.supabase.co"
    os.environ["SUPABASE_KEY"] = "dummy_api_key"
    os.environ["SUPABASE_JWT_SECRET"] = "your_test_jwt_secret"
    
    # Force reload of settings to pick up test environment variables
    with patch("app.core.config.settings"):
        from app.core import config
        yield
        
    # Cleanup (optional)
    del os.environ["SUPABASE_URL"]
    del os.environ["SUPABASE_KEY"]
    del os.environ["SUPABASE_JWT_SECRET"] 