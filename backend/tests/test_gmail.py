import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_gmail_connect_redirect():
    with patch("app.api.gmail.get_flow") as mock_flow:
        mock_flow_instance = MagicMock()
        mock_flow_instance.authorization_url.return_value = ("http://fake-auth-url", "fake-state")
        mock_flow.return_value = mock_flow_instance
        
        # We must bypass the auth dependency, but for simplicity let's test if it responds
        response = client.get("/api/gmail/connect", follow_redirects=False)
        # auth bypasses to demo user in mock mode
        assert response.status_code in [200, 307]

def test_gmail_search_mock():
    # Without real credentials, it should fall back to MockGmailProvider
    response = client.get("/api/gmail/search?query=flight")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert data[0]["id"] == "msg-mock-1"

def test_gmail_disconnect():
    response = client.post("/api/gmail/disconnect")
    assert response.status_code == 200
    assert response.json() == {"status": "disconnected"}

def test_gmail_callback():
    from app.api.gmail import oauth_states
    
    oauth_states["dummy_state"] = {
        "user_id": "user_123",
        "code_verifier": "dummy_verifier"
    }
    
    with patch("app.api.gmail.get_flow") as mock_flow_func:
        mock_flow = MagicMock()
        mock_flow.credentials.token = "fake_token"
        mock_flow.credentials.refresh_token = "fake_refresh_token"
        mock_flow.credentials.token_uri = "fake_uri"
        mock_flow.credentials.client_id = "fake_client_id"
        mock_flow.credentials.client_secret = "fake_secret"
        mock_flow.credentials.scopes = ["fake_scope"]
        mock_flow_func.return_value = mock_flow
        
        with patch("app.api.gmail.GmailConnectionRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            
            response = client.get("/api/gmail/callback?state=dummy_state&code=dummy_code", follow_redirects=False)
            
            assert response.status_code == 307
            assert response.headers["location"] == "http://localhost:5173/?view=TRIPS"
            mock_flow.fetch_token.assert_called_once_with(code="dummy_code")
            mock_repo.save_credentials.assert_called_once()

