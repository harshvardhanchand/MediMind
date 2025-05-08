import os
import pytest
from unittest.mock import patch, Mock

# Set environment variables for tests
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test.db")
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test-key"
os.environ["SUPABASE_JWT_SECRET"] = "test-jwt-secret"

# Patch settings module
@pytest.fixture(scope="session", autouse=True)
def patch_settings():
    """Patch settings before any imports"""
    with patch("app.core.config.settings") as mock_settings:
        mock_settings.DATABASE_URL = os.environ["DATABASE_URL"]
        mock_settings.ENVIRONMENT = "test"
        mock_settings.SUPABASE_URL = os.environ["SUPABASE_URL"]
        mock_settings.SUPABASE_KEY = os.environ["SUPABASE_KEY"]
        mock_settings.SUPABASE_JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]
        mock_settings.GCP_PROJECT_ID = "test-project"
        mock_settings.DOCUMENT_AI_PROCESSOR_LOCATION = "us"
        mock_settings.DOCUMENT_AI_PROCESSOR_ID = "test-processor"
        mock_settings.GEMINI_API_KEY = "test-key"
        yield mock_settings

# Import SQLAlchemy modules
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Mock the Base object with its metadata
@pytest.fixture(scope="session")
def mock_base():
    """Create a mock for Base that will be used in tests"""
    with patch("app.db.session.Base") as mock_base:
        # Mock the metadata attribute with a create_all method
        mock_base.metadata = Mock()
        mock_base.metadata.create_all = Mock()
        mock_base.metadata.drop_all = Mock()
        yield mock_base

@pytest.fixture(scope="session")
def engine():
    """Create a test database engine"""
    test_db_url = os.environ["DATABASE_URL"]
    engine = create_engine(test_db_url, poolclass=NullPool)
    yield engine
    
    # For SQLite, clean up the file after tests
    if test_db_url.startswith("sqlite"):
        try:
            os.remove("./test.db")
        except OSError:
            pass

@pytest.fixture(scope="session")
def tables(engine, mock_base):
    """Create all tables in the test database"""
    # We're using the mock Base, just return
    yield

@pytest.fixture
def db_session(engine, tables):
    """Create a new database session for a test"""
    connection = engine.connect()
    transaction = connection.begin()
    
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    # Begin nested transaction
    nested = connection.begin_nested()
    
    yield session
    
    # Rollback all changes
    if nested.is_active:
        nested.rollback()
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client_session():
    """Mock client session for HTTP requests"""
    with patch("httpx.AsyncClient") as mock_client:
        yield mock_client 