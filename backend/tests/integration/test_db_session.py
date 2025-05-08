import os
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from unittest.mock import patch, MagicMock

from app.repositories.document_repo import document_repo
from app.main import app # Import your main app instance
from app.db.session import get_db
from app.models import User # Import User model if needed for foreign key relation

# We might need a fixture to create a dummy user if document creation requires it
# For now, let's just try reading

# Define a temporary test endpoint within the app for testing purposes
@app.get("/_test_db_connection")
async def test_db_connection(db: AsyncSession = Depends(get_db)):
    """Temporary endpoint to test async db connection and basic query."""
    try:
        # Perform a simple async query using the repository
        # Replace with an actual user_id if needed, or perform a simpler query
        # For now, let's try counting documents (might be 0)
        # Need to adjust the repo or use a direct query
        from sqlalchemy.future import select
        from app.models import Document
        stmt = select(Document).limit(1)
        result = await db.execute(stmt)
        first_doc = result.scalar_one_or_none()
        # We don't care about the result, just that it doesn't raise an error
        return {"status": "ok", "found_doc": first_doc is not None}
    except Exception as e:
        # If any exception occurs during DB interaction, fail the test implicitly
        # by raising it or returning an error status
        return {"status": "error", "detail": str(e)}

# Use the existing TestClient configured for the main app
client = TestClient(app)

@pytest.mark.asyncio # Mark test as async
async def test_async_db_dependency():
    """Test that the get_db dependency provides a working AsyncSession."""
    response = client.get("/_test_db_connection")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    # Add more assertions if needed based on expected data

# Cleanup the temporary endpoint after tests (optional but good practice)
# This requires careful handling, maybe using pytest fixtures or app modifications
# For simplicity, we'll leave it for now, but be aware it's added to your app 