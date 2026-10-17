import os
from unittest.mock import patch, MagicMock
from app.api.auth import get_current_user, User
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import pytest

def test_auth_demo_mode():
    with patch.dict(os.environ, clear=True):
        user = get_current_user(None)
        assert user.is_demo == True
        assert user.id == "demo-user"

@patch('app.api.auth.get_supabase_client')
def test_auth_supabase_mode_missing_token(mock_client):
    mock = MagicMock()
    mock_client.return_value = mock
    with pytest.raises(HTTPException) as excinfo:
        get_current_user(None)
    assert excinfo.value.status_code == 401

@patch('app.api.auth.get_supabase_client')
def test_auth_supabase_mode_valid_token(mock_client):
    mock = MagicMock()
    mock_user = MagicMock()
    mock_user.user.id = "real-user-123"
    mock_user.user.email = "real@test.com"
    mock.auth.get_user.return_value = mock_user
    mock_client.return_value = mock
    
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
    user = get_current_user(creds)
    assert user.id == "real-user-123"
    assert user.is_demo == False
