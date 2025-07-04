"""
Integration tests for the Natural Language Query API endpoint.
"""
import uuid
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, AsyncMock, Mock # AsyncMock for async LLM calls, Mock for verify_token
from datetime import date # Import date for document_date

from app.main import app 
from app.core.auth import verify_token # Import the actual verify_token
from app.models.user import User
from app.models.document import Document, DocumentType, ProcessingStatus
from app.models.extracted_data import ExtractedData, ReviewStatus
from app.schemas.query import QueryRequest, NaturalLanguageQueryResponse
from app.core.config import settings

# Fixture to override auth for all tests in this module
@pytest.fixture(autouse=True)
def mock_auth_override(monkeypatch):
    mock_user_id = uuid.uuid4() # Consistent mock user_id for tests

    def mock_get_user_id_replacement(db_session: Session, token_data: dict):
        return mock_user_id

    monkeypatch.setattr("app.core.auth.get_user_id_from_token", mock_get_user_id_replacement)
    
    yield mock_user_id # Yield the id so other fixtures can use it


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)

# We'll reuse db_session from conftest.py

@pytest.fixture
def test_user(db_session: Session, mock_auth_override):
    # mock_auth_override now IS the user_id yielded by the fixture
    actual_mock_user_id = mock_auth_override 

    user = User(
        user_id=actual_mock_user_id, # Use the ID from the mock
        supabase_id="test-supabase-id-query-user", # Needs to be unique if other tests create users
        email="query_test_user@example.com"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    yield user
    # Cleanup
    db_session.delete(user)
    db_session.commit()

# --- Test Data Fixtures (Documents, ExtractedData) ---
# These will be more complex and varied per test case, 
# so we might define them within test classes or as more specific fixtures later.

# Example: A basic document fixture
@pytest.fixture
def sample_document(db_session: Session, test_user: User) :
    doc = Document(
        user_id=test_user.user_id,
        original_filename="sample_report.pdf",
        document_type=DocumentType.LAB_RESULT,
        storage_path=f"test_docs/{uuid.uuid4()}.pdf",
        processing_status=ProcessingStatus.COMPLETED, # Assume processed for NLQ
        document_date=date(2023, 1, 15),
        source_name="General Hospital",
        tags=["lab", "blood_test"],
        metadata_overrides=None 
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    yield doc
    db_session.delete(doc)
    db_session.commit()

@pytest.fixture
def sample_extracted_data(db_session: Session, sample_document: Document):
    ed = ExtractedData(
        document_id=sample_document.document_id,
        content={
            "extracted_metadata": {
                "document_date": "2023-01-15",
                "source_name": "General Hospital",
                "tags": ["lab", "blood_test"]
            },
            "medical_events": [
                {"event_type": "LabResult", "description": "Glucose", "value": "100", "units": "mg/dL"}
            ]
        },
        raw_text="Glucose 100 mg/dL on 2023-01-15 from General Hospital.",
        review_status=ReviewStatus.PENDING_REVIEW
    )
    db_session.add(ed)
    db_session.commit()
    db_session.refresh(ed)
    yield ed
    db_session.delete(ed)
    db_session.commit()


# --- Main Test Class ---
class TestNaturalLanguageQueryAPI:

    @patch("app.api.endpoints.query.extract_query_filters_with_gemini", new_callable=AsyncMock)
    @patch("app.api.endpoints.query.answer_query_with_filtered_context_gemini", new_callable=AsyncMock)
    def test_simple_query_success(
        self,
        mock_answer_llm: AsyncMock,
        mock_filter_llm: AsyncMock,
        test_client: TestClient,
        test_user: User, # Ensures user exists via mock_auth_override
        sample_document: Document, # Creates a document
        sample_extracted_data: ExtractedData # Creates its extracted data
    ):
        # 1. Setup an API Key (temporarily for the test if not globally set)
        original_api_key = settings.GEMINI_API_KEY
        settings.GEMINI_API_KEY = "test_api_key_for_nlq"
        
        # 2. Configure Mocks
        mock_filter_llm.return_value = "{}" # LLM1: No specific filters, returns all docs for user
        mock_answer_llm.return_value = "This is a test answer based on your documents." # LLM3: Mocked answer

        # 3. Prepare Request
        query = "Tell me about my health."
        request_payload = QueryRequest(query_text=query).model_dump()

        # 4. Make API Call
        response = test_client.post("/api/v1/query/", json=request_payload)

        # 5. Assertions
        assert response.status_code == 200
        response_data = NaturalLanguageQueryResponse(**response.json())
        assert response_data.query_text == query
        assert response_data.answer == "This is a test answer based on your documents."

        # Assert LLM calls
        mock_filter_llm.assert_called_once_with(
            api_key="test_api_key_for_nlq",
            query_text=query
        )
        
        # Construct expected context for answer_llm
        # In this simple case, it's just the medical_events from sample_extracted_data
        expected_context_json = json.dumps([
            {"event_type": "LabResult", "description": "Glucose", "value": "100", "units": "mg/dL"}
        ], indent=2)
        
        mock_answer_llm.assert_called_once_with(
            api_key="test_api_key_for_nlq",
            query_text=query,
            json_data_context=expected_context_json
        )

        # Restore original API key if it was changed
        settings.GEMINI_API_KEY = original_api_key

    # Additional test cases can be added:
    # - Query with specific filters (date, tags, source_name)
    # - Query where metadata_overrides affect filtering
    # - No documents found
    # - Documents found, but no medical_events
    # - LLM1 (filter extraction) fails (returns None) -> 500 error
    # - LLM3 (answering) fails (returns None) -> 500 error
    # - GEMINI_API_KEY not configured -> 500 error
    # - Test with multiple documents and ensure context aggregation

    # @patch("app.core.auth.verify_token") # Removed patch decorator
    def test_gemini_api_key_not_configured(self, test_client: TestClient): # Removed mock_verify_token from args
        
        # Dummy verify_token function for overriding
        async def mock_verify_token_dependency():
            return {"sub": "test-user-sub-for-gemini-test", "role": "authenticated"}

        # Override the dependency
        app.dependency_overrides[verify_token] = mock_verify_token_dependency

        original_api_key = settings.GEMINI_API_KEY
        settings.GEMINI_API_KEY = None # Simulate not configured
        
        query = "Any query"
        request_payload = QueryRequest(query_text=query).model_dump()
        
        # Send a dummy Authorization header; TestClient might still require it for HTTPBearer presence
        # although the verify_token logic itself is now fully mocked.
        headers = {"Authorization": "Bearer dummytoken"}
        response = test_client.post("/api/v1/query/", json=request_payload, headers=headers)
        
        assert response.status_code == 500, f"Expected 500, got {response.status_code}. Response: {response.text}"
        assert response.json() == {"detail": "Query processing not configured."}
        
        settings.GEMINI_API_KEY = original_api_key # Restore

        # Clean up the dependency override
        del app.dependency_overrides[verify_token]

    # def test_another_case_example(self): # Example structure for other tests
    #     pass 