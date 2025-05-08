import uuid
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.repositories.document_repo import DocumentRepository
from app.main import app
from app.models.document import Document, DocumentType, ProcessingStatus
from app.models.extracted_data import ExtractedData, ReviewStatus
from app.models.user import User
from app.repositories.extracted_data_repo import ExtractedDataRepository
from app.core.auth import verify_token

# Override auth for testing
@pytest.fixture(autouse=True)
def mock_auth():
    """Override the auth dependency for all tests in this module."""
    original = app.dependency_overrides.get(verify_token)
    # Create a mock token with a valid sub claim
    app.dependency_overrides[verify_token] = lambda: {"sub": "test-supabase-id"}
    yield
    # Restore original dependency or remove override
    if original:
        app.dependency_overrides[verify_token] = original
    else:
        app.dependency_overrides.pop(verify_token, None)

@pytest.fixture
def test_client():
    """Create a FastAPI TestClient."""
    return TestClient(app)

@pytest.fixture
def test_db(db_session: Session):
    """Create a test database session."""
    return db_session

@pytest.fixture
def test_user(test_db: Session):
    """Create a test user."""
    user = User(
        user_id=uuid.uuid4(),
        supabase_id="test-supabase-id",
        email="test@example.com",
        full_name="Test User"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    yield user
    # Cleanup
    test_db.delete(user)
    test_db.commit()

@pytest.fixture
def test_document(test_db: Session, test_user):
    """Create a test document."""
    document = Document(
        document_id=uuid.uuid4(),
        user_id=test_user.user_id,
        original_filename="test.pdf",
        document_type=DocumentType.PRESCRIPTION,
        storage_path="test/path.pdf",
        processing_status=ProcessingStatus.PROCESSED,
        file_metadata={"type": "application/pdf", "size": 1024}
    )
    test_db.add(document)
    test_db.commit()
    test_db.refresh(document)
    yield document
    # Cleanup
    test_db.delete(document)
    test_db.commit()

@pytest.fixture
def test_extracted_data(test_db: Session, test_document):
    """Create test extracted data."""
    extracted_data = ExtractedData(
        extracted_data_id=uuid.uuid4(),
        document_id=test_document.document_id,
        content={"test": "data", "medical_events": [{"event_type": "Medication", "description": "Test Med"}]},
        raw_text="Test prescription for patient",
        review_status=ReviewStatus.PENDING_REVIEW
    )
    test_db.add(extracted_data)
    test_db.commit()
    test_db.refresh(extracted_data)
    yield extracted_data
    # Cleanup
    test_db.delete(extracted_data)
    test_db.commit()

class TestExtractedDataAPI:
    """Integration tests for the extracted data API endpoints."""

    def test_get_extracted_data(self, test_client, test_extracted_data):
        """Test getting extracted data for a document."""
        response = test_client.get(f"/api/v1/extracted_data/{test_extracted_data.document_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == str(test_extracted_data.document_id)
        assert data["content"] == test_extracted_data.content
        assert data["raw_text"] == test_extracted_data.raw_text
        assert data["review_status"] == test_extracted_data.review_status.value

    def test_get_nonexistent_extracted_data(self, test_client):
        """Test getting extracted data for a nonexistent document."""
        nonexistent_id = uuid.uuid4()
        response = test_client.get(f"/api/v1/extracted_data/{nonexistent_id}")
        
        assert response.status_code == 404

    def test_update_review_status(self, test_client, test_extracted_data):
        """Test updating the review status of extracted data."""
        new_status = ReviewStatus.REVIEWED_APPROVED.value
        response = test_client.put(
            f"/api/v1/extracted_data/{test_extracted_data.document_id}/status",
            json={"review_status": new_status}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["review_status"] == new_status

    def test_update_content(self, test_client, test_extracted_data):
        """Test updating the content of extracted data."""
        new_content = {
            "medical_events": [
                {"event_type": "Medication", "description": "Updated Med", "value": "10mg"}
            ]
        }
        response = test_client.put(
            f"/api/v1/extracted_data/{test_extracted_data.document_id}/content",
            json={"content": new_content}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == new_content
        assert data["review_status"] == ReviewStatus.REVIEWED_CORRECTED.value

    def test_get_extraction_details(self, test_client, test_extracted_data, test_document):
        """Test getting combined document and extraction details."""
        response = test_client.get(f"/api/v1/extracted_data/all/{test_extracted_data.document_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "document" in data
        assert "extracted_data" in data
        assert data["document"]["document_id"] == str(test_document.document_id)
        assert data["extracted_data"]["extracted_data_id"] == str(test_extracted_data.extracted_data_id)

    def test_unauthorized_access(self, test_client, test_db, test_extracted_data):
        """Test attempting to access another user's document."""
        # Create another user
        other_user = User(
            user_id=uuid.uuid4(),
            supabase_id="other-supabase-id",
            email="other@example.com",
            full_name="Other User"
        )
        test_db.add(other_user)
        
        # Create a document for the other user
        other_document = Document(
            document_id=uuid.uuid4(),
            user_id=other_user.user_id,  # Different user
            original_filename="other.pdf",
            document_type=DocumentType.PRESCRIPTION,
            storage_path="other/path.pdf",
            processing_status=ProcessingStatus.PROCESSED
        )
        test_db.add(other_document)
        
        # Create extracted data for the other document
        other_extracted_data = ExtractedData(
            extracted_data_id=uuid.uuid4(),
            document_id=other_document.document_id,
            content={"test": "other data"},
            raw_text="Other user's data",
            review_status=ReviewStatus.PENDING_REVIEW
        )
        test_db.add(other_extracted_data)
        test_db.commit()
        
        # Try to access the other user's data (should be forbidden)
        response = test_client.get(f"/api/v1/extracted_data/{other_document.document_id}")
        
        # Cleanup
        test_db.delete(other_extracted_data)
        test_db.delete(other_document)
        test_db.delete(other_user)
        test_db.commit()
        
        # Should get 403 Forbidden
        assert response.status_code == 403 