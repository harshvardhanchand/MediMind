"""
Repository modules for database access in the Medical Data Hub app.
This package contains repository classes for accessing and manipulating database entities.
"""

from .document_repo import document_repo, DocumentRepository
from .user_repo import user_repo, UserRepository
from .extracted_data_repo import ExtractedDataRepository

# Create instance for extracted_data_repo
from app.models.extracted_data import ExtractedData
from .extracted_data_repo import ExtractedDataRepository

# Note: extracted_data_repo requires a db session, so it's created on demand
# rather than as a singleton like document_repo and user_repo

__all__ = [
    "document_repo",
    "DocumentRepository",
    "user_repo",
    "UserRepository",
    "ExtractedDataRepository",
] 