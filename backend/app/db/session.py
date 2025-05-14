import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import Generator, AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

# Define Base here
Base = declarative_base()

# Use create_engine for synchronous connection with the DATABASE_URL from settings
# Ensure settings.DATABASE_URL provides a sync DSN (e.g., postgresql://... or postgresql+psycopg2://...)
engine = create_engine(str(settings.DATABASE_URL), pool_pre_ping=True)

# Use sessionmaker for synchronous sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Synchronous dependency provider
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ASYNCHRONOUS SETUP
async_engine = None
AsyncSessionLocal = None

if settings.ASYNC_DATABASE_URL:
    try:
        async_engine = create_async_engine(str(settings.ASYNC_DATABASE_URL), pool_pre_ping=True)
        AsyncSessionLocal = sessionmaker(
            bind=async_engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
        )
        logger.info("Asynchronous database engine initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize asynchronous database engine: {e}", exc_info=True)
        # async_engine and AsyncSessionLocal will remain None, preventing async DB operations
else:
    logger.warning("ASYNC_DATABASE_URL not configured. Asynchronous database features will be unavailable.")

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    if AsyncSessionLocal is None:
        raise RuntimeError("Async database session not initialized. Check ASYNC_DATABASE_URL configuration.")
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # For async, commit is often handled by the caller or at the end of a unit of work.
            # await session.commit() # Typically not here in get_async_db
        except Exception:
            # await session.rollback() # Rollback on exception
            raise
        finally:
            await session.close() # Ensure session is closed

# Optional: Add a function to create tables (useful for initial setup/tests without Alembic)
# def init_db():
#     Base.metadata.create_all(bind=engine) 