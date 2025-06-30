import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import Generator, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.sql import text

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

# Define separate Base classes for sync and async to avoid engine mixing
Base = declarative_base()  # For synchronous operations
AsyncBase = declarative_base()  # For asynchronous operations


engine = create_engine(str(settings.DATABASE_URL), pool_pre_ping=True)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
       
else:
    logger.warning("ASYNC_DATABASE_URL not configured. Asynchronous database features will be unavailable.")

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides async database session with automatic transaction management.
    Commits on success, rolls back on exception.
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Async database session not initialized. Check ASYNC_DATABASE_URL configuration.")
    async with AsyncSessionLocal() as session:
        try:
            
            await session.execute(text("SET search_path TO public, extensions"))
            yield session
            # Auto-commit successful transactions
            await session.commit()
        except Exception:
            
            await session.rollback()
            raise
        finally:
            await session.close()

@asynccontextmanager
async def get_async_db_manual() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for manual transaction control. 
    Caller is responsible for commit/rollback.
    Use this when you need explicit transaction boundaries.
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Async database session not initialized. Check ASYNC_DATABASE_URL configuration.")
    async with AsyncSessionLocal() as session:
        try:
            
            await session.execute(text("SET search_path TO public, extensions"))
            yield session
        finally:
            await session.close()
