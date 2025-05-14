import pytest
from fastapi.testclient import TestClient
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app # Your FastAPI app
from app.schemas.user import UserRead # Your response schema
from app.models.user import User # To type hint if needed
from app.core.auth import verify_token # To override for specific tests if necessary
from typing import Dict, Any # For typing mock return

# TestClient is synchronous but handles async endpoints correctly
client = TestClient(app)

@pytest.mark.asyncio
async def test_get_me_success(
    test_user_in_db: User, # Fixture to ensure user exists & provides user data
    mock_auth_valid_user, # Fixture to mock auth with this user's sub
    # async_db_session is implicitly used by test_user_in_db if that fixture depends on it
):
    """Test successfully retrieving the current user's profile."""
    response = client.get("/api/users/me")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["user_id"] == str(test_user_in_db.user_id)
    assert data["supabase_id"] == test_user_in_db.supabase_id
    assert data["email"] == test_user_in_db.email
    # Add assertions for other fields in UserRead as defined in your schema
    assert "created_at" in data
    assert "updated_at" in data

@pytest.mark.asyncio
async def test_get_me_user_not_found_in_db(
    async_db_session: AsyncSession, # Added async_db_session fixture
    # This test ensures that if the token 'sub' doesn't match a user in the DB,
    # a 404 is returned. The mock_auth_valid_user fixture from conftest
    # uses test_user_in_db, which creates a user. To test this scenario,
    # we need a token 'sub' that *doesn't* match any user.
):
    """Test case where token is valid but user ID (sub) is not in the database."""
    # Temporarily override verify_token for this specific test case
    # to provide a supabase_id that won't be found.
    original_dependency = app.dependency_overrides.get(verify_token)
    
    non_existent_supabase_id = f"nonexistent-supabase-id-{uuid.uuid4()}"
    def mock_verify_token_nonexistent_sub() -> Dict[str, Any]:
        return {"sub": non_existent_supabase_id, "email": "ghost@example.com"}

    app.dependency_overrides[verify_token] = mock_verify_token_nonexistent_sub
    
    response = client.get("/api/users/me")
    
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "User not found in database"

    # Clean up the override
    if original_dependency:
        app.dependency_overrides[verify_token] = original_dependency
    else:
        app.dependency_overrides.pop(verify_token, None)

@pytest.mark.asyncio
async def test_get_me_invalid_token_missing_sub(
    mock_auth_invalid_sub, # Fixture that mocks a token missing 'sub'
):
    """Test case where the token is invalid (missing 'sub' claim)."""
    response = client.get("/api/users/me")

    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "Invalid token: Missing sub claim"

@pytest.mark.asyncio
async def test_get_me_unauthenticated(
    # No auth mocking fixture, so verify_token will run as is
    # or be a default mock if other tests haven't cleaned up their overrides properly.
    # To ensure a truly unauthenticated state, we can clear dependency_overrides for verify_token
    # or ensure verify_token itself would raise an auth error (e.g., if no Authorization header)
):
    """Test accessing /me without a valid Authorization header."""
    # Clear any existing override for verify_token to test FastAPI's default handling or real dep
    original_dependency = app.dependency_overrides.pop(verify_token, None)

    response = client.get("/api/users/me") # No Authorization header sent by TestClient by default
    
    # The actual status code depends on how verify_token and FastAPI handle missing/invalid tokens.
    # Typically, it would be 401 or 403 if the dependency itself raises HTTPException.
    # If verify_token is not robust enough and lets it pass, this test might fail or give unexpected results.
    # Assuming verify_token (or underlying Starlette/FastAPI) raises 401/403 for missing header.
    assert response.status_code in [401, 403], response.text 
    # Example detail, adjust based on actual error from verify_token for no header:
    # assert "Not authenticated" in response.json()["detail"] or "Missing Authorization Header" in response.json()["detail"]

    # Restore original dependency if it existed
    if original_dependency:
        app.dependency_overrides[verify_token] = original_dependency
 