import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

logger = logging.getLogger(__name__)

# Ensure the DATABASE_URL uses an async driver (e.g., postgresql+asyncpg)
async_db_url = settings.DATABASE_URL
if not async_db_url.startswith("postgresql+asyncpg"):
    if async_db_url.startswith("postgresql"): 
        # Attempt to replace sync driver with asyncpg
        async_db_url = async_db_url.replace("postgresql+psycopg2", "postgresql+asyncpg", 1)
        async_db_url = async_db_url.replace("postgresql", "postgresql+asyncpg", 1) # If no driver specified
        logger.warning(f"DATABASE_URL did not specify async driver. Assuming asyncpg: {async_db_url}")
    else:
        raise ValueError("DATABASE_URL is not configured for PostgreSQL or asyncpg")

# Create async engine
engine = create_async_engine(
    async_db_url,
    pool_pre_ping=True,
    pool_size=10,         # Adjust pool size as needed
    max_overflow=20,
    echo=settings.ENVIRONMENT == "development" # Log SQL in dev
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False, # Recommended for async sessions
    autocommit=False, 
    autoflush=False
)

# Base class for SQLAlchemy models
Base = declarative_base()

async def get_db() -> AsyncSession:
    """
    Get an async database session from the pool.
    
    Designed as a FastAPI dependency.
    Yields a session and ensures it's closed afterwards.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Optional: Add a function to create tables (useful for initial setup/tests without Alembic)
# async def init_db():
#     async with engine.begin() as conn:
#         # await conn.run_sync(Base.metadata.drop_all)
#         await conn.run_sync(Base.metadata.create_all) 