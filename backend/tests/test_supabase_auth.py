import pytest
import jwt
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import db_url
from backend.app.config import settings
from backend.app.auth import get_current_user

client = TestClient(app)

def test_database_url_normalization():
    sample_postgres_url = "postgres://postgres:mypassword@db.supabase.co:5432/postgres"
    if sample_postgres_url.startswith("postgres://"):
        normalized = sample_postgres_url.replace("postgres://", "postgresql://", 1)
    assert normalized.startswith("postgresql://")

def test_unauthenticated_request_falls_back_to_default_user():
    response = client.get("/api/settings/status")
    assert response.status_code == 200
    data = response.json()
    assert data["active_user"]["id"] == settings.default_user_id
    assert "supabase_configured" in data

def test_authenticated_supabase_jwt_sync():
    # Create test JWT payload matching Supabase Auth token format
    test_uid = "sb-user-uuid-987654"
    payload = {
        "sub": test_uid,
        "email": "student_test@supabase.io",
        "user_metadata": {
            "full_name": "Supabase Test Student"
        },
        "role": "authenticated"
    }
    
    # Generate token
    secret = settings.supabase_jwt_secret or "dummy_secret_for_test"
    token = jwt.encode(payload, secret, algorithm="HS256")
    
    response = client.get(
        "/api/settings/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["active_user"]["id"] == test_uid
    assert data["active_user"]["email"] == "student_test@supabase.io"
    assert data["active_user"]["name"] == "Supabase Test Student"

def test_invalid_bearer_token():
    response = client.get(
        "/api/settings/status",
        headers={"Authorization": "Bearer not-a-valid-jwt-token"}
    )
    assert response.status_code == 401
    assert "Invalid or expired Supabase authentication token" in response.json()["detail"]
