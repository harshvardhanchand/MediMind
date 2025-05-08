import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import Generator

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

# Optional: Add a function to create tables (useful for initial setup/tests without Alembic)
# def init_db():
#     Base.metadata.create_all(bind=engine) 