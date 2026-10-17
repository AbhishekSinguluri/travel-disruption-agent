from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_no_oauth_connection():
    # Because user bypass is active in demo mode, but no Gmail creds are in repo
    response = client.get("/api/gmail/status")
    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is False
    assert data["email"] is None
    assert data["provider"] == "none"

def test_mock_provider_behavior():
    # Even if mock provider returns connected=true internally, 
    # the user-facing status endpoint strictly respects the repo (OAuth).
    response = client.get("/api/gmail/status")
    assert response.status_code == 200
    assert response.json()["connected"] is False

def test_demo_auth_does_not_imply_gmail():
    # We are authenticated with ROAM (demo), but Gmail isn't connected automatically.
    response = client.get("/api/gmail/status")
    assert response.status_code == 200
    assert response.json()["connected"] is False

def test_disconnect():
    response = client.post("/api/gmail/disconnect")
    assert response.status_code == 200
    
    status_response = client.get("/api/gmail/status")
    assert status_response.json()["connected"] is False
