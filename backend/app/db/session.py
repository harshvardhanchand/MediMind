import logging
from typing import Generator, AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text

from app.core.config import settings

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# ORM base and synchronous engine/session
# -------------------------------------------------------------------
Base = declarative_base()

engine = create_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,
    poolclass=NullPool,
    execution_options={"compiled_cache_size": 0},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Sync DB session generator for FastAPI dependencies.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------------------------------------------
# Asynchronous engine/session setup
# -------------------------------------------------------------------
if settings.ASYNC_DATABASE_URL:
    try:
        async_engine = create_async_engine(
            str(settings.ASYNC_DATABASE_URL),
            poolclass=NullPool,
            connect_args={"statement_cache_size": 0},
        )
        AsyncSessionLocal = sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        logger.info("Asynchronous database engine initialized successfully.")
    except Exception:
        logger.error(
            "Failed to initialize asynchronous database engine",
            exc_info=True,
        )
        AsyncSessionLocal = None
else:
    logger.warning("ASYNC_DATABASE_URL not configured; async features unavailable.")
    AsyncSessionLocal = None


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async DB session generator for FastAPI dependencies.
    Handles BEGIN/COMMIT/ROLLBACK and sets the search_path.
    """
    if AsyncSessionLocal is None:
        raise RuntimeError(
            "Async DB not configured. Check settings.ASYNC_DATABASE_URL."
        )
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # adjust schema search path if needed
            await session.execute(text("SET search_path TO public, extensions"))
            yield session
