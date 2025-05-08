import uuid
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException
import os

# Ensure environment variables are set
os.environ["DATABASE_URL"] = "postgresql://fake:fake@localhost/fakedb"
os.environ["SUPABASE_URL"] = "https://test-unit.supabase.co"
os.environ["SUPABASE_KEY"] = "test-unit-key"
os.environ["SUPABASE_JWT_SECRET"] = "test-unit-jwt-secret"

# Mock settings before importing app modules
with patch("app.core.config.settings") as mock_settings:
    mock_settings.DATABASE_URL = os.environ["DATABASE_URL"] 
    mock_settings.ENVIRONMENT = "test"
    
    # Now import the modules
    from app.api.v1.endpoints.extracted_data import (
        get_extracted_data,
        update_extracted_data_status,
        update_extracted_data_content,
        get_extraction_details,
        get_user_id_from_token
    )
    from app.models.extracted_data import ReviewStatus
    from app.schemas.extracted_data import ExtractedDataStatusUpdate, ExtractedDataContentUpdate

# Test data
TEST_DOC_ID = uuid.uuid4()
TEST_USER_ID = uuid.uuid4()
TEST_WRONG_USER_ID = uuid.uuid4()
TEST_TOKEN_DATA = {"sub": "test-supabase-id"}

@pytest.fixture
def mock_document():
    """Create a mock document with specified user_id."""
    doc = MagicMock()
    doc.document_id = TEST_DOC_ID
    doc.user_id = TEST_USER_ID
    return doc

@pytest.fixture
def mock_extracted_data():
    """Create a mock extracted data object."""
    data = MagicMock()
    data.extracted_data_id = uuid.uuid4()
    data.document_id = TEST_DOC_ID
    data.content = {"test": "data"}
    data.raw_text = "Test raw text"
    data.review_status = ReviewStatus.PENDING_REVIEW
    return data

@patch("app.api.v1.endpoints.extracted_data.get_user_id_from_token")
class TestExtractedDataEndpoints:
    
    @patch("app.api.v1.endpoints.extracted_data.document_repo")
    @patch("app.api.v1.endpoints.extracted_data.ExtractedDataRepository")
    def test_get_extracted_data_success(
        self, 
        mock_ext_repo, 
        mock_doc_repo, 
        mock_get_user_id,
        mock_document,
        mock_extracted_data
    ):
        # Setup mocks
        mock_get_user_id.return_value = TEST_USER_ID
        mock_doc_repo.get_document.return_value = mock_document
        mock_ext_repo.return_value.get_by_document_id.return_value = mock_extracted_data
        
        # Create a specific db_mock to use in both call and assertion
        db_mock = MagicMock()
        
        # Call function with our specific db_mock
        result = get_extracted_data(TEST_DOC_ID, db_mock, TEST_TOKEN_DATA)
        
        # Assertions - use the same db_mock
        mock_doc_repo.get_document.assert_called_once_with(db_mock, document_id=TEST_DOC_ID)
        mock_ext_repo.return_value.get_by_document_id.assert_called_once_with(TEST_DOC_ID)
        assert result == mock_extracted_data

    @patch("app.api.v1.endpoints.extracted_data.document_repo")
    @patch("app.api.v1.endpoints.extracted_data.ExtractedDataRepository")
    def test_get_extracted_data_document_not_found(
        self, 
        mock_ext_repo, 
        mock_doc_repo, 
        mock_get_user_id
    ):
        # Setup mocks
        mock_get_user_id.return_value = TEST_USER_ID
        mock_doc_repo.get_document.return_value = None
        
        # Call function and expect exception
        with pytest.raises(HTTPException) as exc:
            get_extracted_data(TEST_DOC_ID, MagicMock(), TEST_TOKEN_DATA)
        
        # Assertions
        assert exc.value.status_code == 404
        assert "Document not found" in exc.value.detail

    @patch("app.api.v1.endpoints.extracted_data.document_repo")
    def test_get_extracted_data_unauthorized(
        self, 
        mock_doc_repo, 
        mock_get_user_id,
        mock_document
    ):
        # Setup mocks
        mock_get_user_id.return_value = TEST_WRONG_USER_ID
        mock_document.user_id = TEST_USER_ID  # Different from TEST_WRONG_USER_ID
        mock_doc_repo.get_document.return_value = mock_document
        
        # Call function and expect exception
        with pytest.raises(HTTPException) as exc:
            get_extracted_data(TEST_DOC_ID, MagicMock(), TEST_TOKEN_DATA)
        
        # Assertions
        assert exc.value.status_code == 403
        assert "Not authorized" in exc.value.detail

    @patch("app.api.v1.endpoints.extracted_data.document_repo")
    @patch("app.api.v1.endpoints.extracted_data.ExtractedDataRepository")
    def test_update_status_success(
        self, 
        mock_ext_repo, 
        mock_doc_repo, 
        mock_get_user_id,
        mock_document,
        mock_extracted_data
    ):
        # Setup mocks
        mock_get_user_id.return_value = TEST_USER_ID
        mock_doc_repo.get_document.return_value = mock_document
        mock_ext_repo.return_value.update_review_status.return_value = mock_extracted_data
        
        # Create test status update
        status_update = ExtractedDataStatusUpdate(review_status=ReviewStatus.REVIEWED_APPROVED)
        
        # Create db_mock for consistent testing
        db_mock = MagicMock()
        
        # Call function
        result = update_extracted_data_status(TEST_DOC_ID, status_update, db_mock, TEST_TOKEN_DATA)
        
        # Assertions
        mock_doc_repo.get_document.assert_called_once_with(db_mock, document_id=TEST_DOC_ID)
        mock_ext_repo.return_value.update_review_status.assert_called_once_with(
            document_id=TEST_DOC_ID,
            review_status=ReviewStatus.REVIEWED_APPROVED,
            reviewed_by_user_id=TEST_USER_ID
        )
        assert result == mock_extracted_data

    @patch("app.api.v1.endpoints.extracted_data.document_repo")
    @patch("app.api.v1.endpoints.extracted_data.ExtractedDataRepository")
    def test_update_content_success(
        self, 
        mock_ext_repo, 
        mock_doc_repo, 
        mock_get_user_id,
        mock_document,
        mock_extracted_data
    ):
        # Setup mocks
        mock_get_user_id.return_value = TEST_USER_ID
        mock_doc_repo.get_document.return_value = mock_document
        mock_ext_repo.return_value.update_structured_content.return_value = mock_extracted_data
        mock_ext_repo.return_value.update_review_status.return_value = mock_extracted_data
        
        # Create test content update
        content_update = ExtractedDataContentUpdate(content={"updated": "content"})
        
        # Create db_mock for consistent testing
        db_mock = MagicMock()
        
        # Call function
        result = update_extracted_data_content(TEST_DOC_ID, content_update, db_mock, TEST_TOKEN_DATA)
        
        # Assertions
        mock_doc_repo.get_document.assert_called_once_with(db_mock, document_id=TEST_DOC_ID)
        mock_ext_repo.return_value.update_structured_content.assert_called_once_with(
            document_id=TEST_DOC_ID,
            content={"updated": "content"}
        )
        mock_ext_repo.return_value.update_review_status.assert_called_once()
        assert result == mock_extracted_data

@patch("app.api.v1.endpoints.extracted_data.user_repo")
class TestHelperFunctions:
    
    def test_get_user_id_from_token_success(self, mock_user_repo, mock_document):
        # Setup mocks
        mock_user = MagicMock()
        mock_user.user_id = TEST_USER_ID
        mock_user_repo.get_by_supabase_id_sync.return_value = mock_user
        
        # Create a specific db mock to use in both call and assertion
        db_mock = MagicMock()
        
        # Call function with our specific db mock
        result = get_user_id_from_token(db_mock, {"sub": "test-supabase-id"})
        
        # Assertions - use the same db_mock object
        mock_user_repo.get_by_supabase_id_sync.assert_called_once_with(
            db_mock, supabase_id="test-supabase-id"
        )
        assert result == TEST_USER_ID

    def test_get_user_id_from_token_invalid_token(self, mock_user_repo):
        # Call function with invalid token and expect exception
        with pytest.raises(HTTPException) as exc:
            get_user_id_from_token(MagicMock(), {})  # Empty token data
        
        # Assertions
        assert exc.value.status_code == 401
        assert "Invalid authentication token" in exc.value.detail

    def test_get_user_id_from_token_user_not_found(self, mock_user_repo):
        # Setup mocks
        mock_user_repo.get_by_supabase_id_sync.return_value = None
        
        # Call function with valid token but user not found
        with pytest.raises(HTTPException) as exc:
            get_user_id_from_token(MagicMock(), {"sub": "test-supabase-id"})
        
        # Assertions
        assert exc.value.status_code == 404
        assert "User not found" in exc.value.detail 