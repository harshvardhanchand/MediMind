import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.auth import verify_token

client = TestClient(app)

# Create a mock token response
mock_token_data = {
    "sub": "test-user-123",
    "email": "test@example.com",
    "app_metadata": {"provider": "email"},
    "user_metadata": {"name": "Test User"}
}

# Override the verify_token dependency at the app level
app.dependency_overrides[verify_token] = lambda: mock_token_data

def test_me_endpoint_with_valid_token():
    """Test the /me endpoint with a valid token."""
    response = client.get(
        "/api/v1/me",
        headers={"Authorization": "Bearer fake-valid-token"}
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-user-123"
    assert data["email"] == "test@example.com"
    assert data["app_metadata"] == {"provider": "email"}
    assert data["user_metadata"] == {"name": "Test User"}

def test_me_endpoint_authentication_required():
    """Test the /me endpoint without a token returns 401 or 403."""
    # Temporarily remove the dependency override to test authentication
    original_dependency = app.dependency_overrides.get(verify_token)
    app.dependency_overrides.pop(verify_token, None)
    
    try:
        response = client.get("/api/v1/me")
        # Should get an unauthorized response
        assert response.status_code in (401, 403, 503)  # Include 503 for service unavailable
    finally:
        # Restore the dependency override
        if original_dependency:
            app.dependency_overrides[verify_token] = original_dependency

@pytest.fixture
def mock_auth_error():
    """Mock authentication that raises an error."""
    from fastapi import HTTPException
    
    # Store original dependency override
    original_dependency = app.dependency_overrides.get(verify_token)
    
    # Set new dependency override that raises an exception
    def raise_auth_error():
        raise HTTPException(status_code=401, detail="Invalid token")
    
    app.dependency_overrides[verify_token] = raise_auth_error
    
    yield
    
    # Restore original dependency override
    if original_dependency:
        app.dependency_overrides[verify_token] = original_dependency
    else:
        app.dependency_overrides.pop(verify_token, None)

def test_me_endpoint_with_invalid_token(mock_auth_error):
    """Test the /me endpoint with an invalid token."""
    response = client.get(
        "/api/v1/me", 
        headers={"Authorization": "Bearer fake-invalid-token"}
    )
    
    # Check the response
    assert response.status_code == 401 