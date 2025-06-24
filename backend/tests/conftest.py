import os
os.environ["ENVIRONMENT"] = "test" 

import pytest
import pytest_asyncio
import uuid 
from typing import AsyncGenerator, Dict, Any 
from unittest.mock import patch


os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test.db")


os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test-key"
os.environ["SUPABASE_JWT_SECRET"] = "test-jwt-secret"


@pytest.fixture(scope="session", autouse=True)
def patch_settings():
    """Patch settings before any imports"""
    with patch("app.core.config.settings") as mock_settings:
        mock_settings.ENVIRONMENT = "test"
        mock_settings.DATABASE_URL = os.environ["DATABASE_URL"]
        
        if mock_settings.DATABASE_URL.startswith("sqlite:///"):
            mock_settings.ASYNC_DATABASE_URL = mock_settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        elif mock_settings.DATABASE_URL.startswith("postgresql://"):
            mock_settings.ASYNC_DATABASE_URL = mock_settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        else:
           
            mock_settings.ASYNC_DATABASE_URL = None 

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
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.db.session import Base 
from app.models.user import User 
from app.main import app 
from app.core.auth import verify_token 



@pytest.fixture(scope="session")
def engine():
    """Create a test database engine"""
    test_db_url = os.environ["DATABASE_URL"]
    engine = create_engine(test_db_url, poolclass=NullPool)
    yield engine
    
    
    if test_db_url.startswith("sqlite"):
        try:
            os.remove("./test.db")
        except OSError:
            pass

@pytest.fixture(scope="session")
def tables(engine): 
    """Create all tables in the test database before tests and drop after."""
    Base.metadata.create_all(bind=engine) 
    yield
    Base.metadata.drop_all(bind=engine) 

@pytest.fixture
def db_session(engine, tables):
    """Create a new database session for a test"""
    connection = engine.connect()
    transaction = connection.begin()
    
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

   
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

# ASYNC TEST FIXTURES (new)
@pytest_asyncio.fixture(scope="function")
async def async_test_engine():
    """Create a test async database engine."""
    # settings should be patched by now by patch_settings fixture
    from app.core.config import settings as patched_settings
    if not patched_settings.ASYNC_DATABASE_URL:
        pytest.skip("ASYNC_DATABASE_URL not configured for tests, skipping async tests.")
    
    engine = create_async_engine(str(patched_settings.ASYNC_DATABASE_URL), poolclass=NullPool)
    yield engine
    await engine.dispose()
    # For SQLite, clean up the async file after tests if a separate one was used
    if str(patched_settings.ASYNC_DATABASE_URL).startswith("sqlite+aiosqlite:///./test_async.db"):
        try:
            os.remove("./test_async.db")
        except OSError:
            pass 

@pytest_asyncio.fixture(scope="function")
async def async_tables(async_test_engine):
    """Create all tables in the test async database before tests and drop after."""
    async with async_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def async_db_session(async_test_engine, async_tables) -> AsyncGenerator[AsyncSession, None]:
    """Create a new async database session for a test with transaction rollback."""
    connection = await async_test_engine.connect()
    transaction = await connection.begin()
    
    AsyncTestSessionLocal = sessionmaker(
        bind=connection, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
    )
    session = AsyncTestSessionLocal()
    
    # Begin nested transaction if supported by DB and driver, or manage rollback carefully
    # For simplicity, we'll rely on the outer transaction rollback

    yield session
    
    await session.close()
    if transaction.is_active:
        await transaction.rollback()
    await connection.close()

@pytest_asyncio.fixture
async def test_user_in_db(async_db_session: AsyncSession) -> User:
    """Fixture to create and return a test user in the async database."""
    user_data = {
        "user_id": uuid.uuid4(),
        "supabase_id": f"test-supabase-id-{uuid.uuid4()}",
        "email": f"testuser_{uuid.uuid4()}@example.com",
        # Add other required fields for your User model if any
    }
    user = User(**user_data)
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)
    return user

@pytest.fixture(scope="function") # This fixture doesn't need to be async itself
def mock_auth_valid_user(test_user_in_db: User): # Depends on the async test_user_in_db
    """Mocks verify_token to simulate a valid authenticated user."""
    # This fixture will run in the asyncio event loop if the test function is async
    # and test_user_in_db (an async fixture) is resolved.
    original_dependency = app.dependency_overrides.get(verify_token)
    
    def mock_verify_token_valid() -> Dict[str, Any]:
        return {"sub": test_user_in_db.supabase_id, "email": test_user_in_db.email}

    app.dependency_overrides[verify_token] = mock_verify_token_valid
    yield 
    if original_dependency:
        app.dependency_overrides[verify_token] = original_dependency
    else:
        app.dependency_overrides.pop(verify_token, None)

@pytest.fixture(scope="function") # This fixture also doesn't need to be async
def mock_auth_invalid_sub():
    """Mocks verify_token to simulate a token with a missing 'sub' claim."""
    original_dependency = app.dependency_overrides.get(verify_token)
    
    def mock_verify_token_invalid() -> Dict[str, Any]:
        return {"email": "test@example.com"} # Missing 'sub'

    app.dependency_overrides[verify_token] = mock_verify_token_invalid
    yield
    if original_dependency:
        app.dependency_overrides[verify_token] = original_dependency
    else:
        app.dependency_overrides.pop(verify_token, None) 