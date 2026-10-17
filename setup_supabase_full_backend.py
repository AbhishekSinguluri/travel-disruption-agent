import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

backend_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\app"
tests_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\tests"

# --- AUTH DEPENDENCY ---
auth_py = """
import os
import logging
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from pydantic import BaseModel

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

class User(BaseModel):
    id: str
    email: str
    is_demo: bool = False

def get_supabase_client() -> Client | None:
    sb_url = os.getenv("SUPABASE_URL")
    sb_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if sb_url and sb_key and sb_url != "your_supabase_url_here":
        return create_client(sb_url, sb_key)
    return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> User:
    client = get_supabase_client()
    
    if not client:
        # Demo mode bypass
        logger.info("[AUTH] Using Demo Mode user bypass")
        return User(id="demo-user", email="demo@example.com", is_demo=True)
        
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization token")
        
    try:
        # Validate JWT using the client
        res = client.auth.get_user(credentials.credentials)
        if not res or not res.user:
            raise HTTPException(status_code=401, detail="Invalid authorization token")
        return User(id=res.user.id, email=res.user.email)
    except Exception as e:
        logger.error(f"[AUTH ERROR] {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
"""
write_file(f"{backend_dir}/api/auth.py", auth_py)

# --- REPOSITORIES PATCH ---
# We patch repositories to actually use supabase
repos_patch = """
import os
import logging
from typing import Protocol, List, Dict, Any, Optional
from supabase import create_client
from app.services.mock_db import MOCK_DB

logger = logging.getLogger(__name__)

class TripRepository(Protocol):
    def get_trip(self, trip_id: str, user_id: str) -> Optional[Dict[str, Any]]: ...
    def update_trip(self, trip_id: str, trip_data: Dict[str, Any], user_id: str) -> None: ...
    def list_trips(self, user_id: str) -> List[Dict[str, Any]]: ...
    def log_event(self, trip_id: str, event_type: str, payload: Dict[str, Any]) -> None: ...
    def get_events(self, trip_id: str) -> List[Dict[str, Any]]: ...

class InMemoryTripRepository:
    def get_trip(self, trip_id: str, user_id: str = "demo-user") -> Optional[Dict[str, Any]]:
        return MOCK_DB["trips"].get(trip_id)
        
    def update_trip(self, trip_id: str, trip_data: Dict[str, Any], user_id: str = "demo-user") -> None:
        MOCK_DB["trips"][trip_id] = trip_data
        
    def list_trips(self, user_id: str = "demo-user") -> List[Dict[str, Any]]:
        return list(MOCK_DB["trips"].values())
        
    def log_event(self, trip_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        if "events" not in MOCK_DB:
            MOCK_DB["events"] = []
        MOCK_DB["events"].append({"trip_id": trip_id, "event_type": event_type, "payload": payload})
        
    def get_events(self, trip_id: str) -> List[Dict[str, Any]]:
        return [e for e in MOCK_DB.get("events", []) if e["trip_id"] == trip_id]

class SupabaseTripRepository:
    def __init__(self, supabase_url: str, supabase_key: str):
        self.client = create_client(supabase_url, supabase_key)
        
    def get_trip(self, trip_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            res = self.client.table("trips").select("*").eq("id", trip_id).eq("user_id", user_id).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"[SUPABASE ERROR] get_trip: {e}")
            return None
        
    def update_trip(self, trip_id: str, trip_data: Dict[str, Any], user_id: str) -> None:
        try:
            # Upsert trip basics (demo mapping, MVP simplified)
            self.client.table("trips").upsert({
                "id": trip_id,
                "user_id": user_id,
                "name": trip_data.get("name", "Trip"),
                "destination": trip_data.get("destination", "Unknown"),
                "start_date": "2026-09-01",
                "end_date": "2026-09-05"
            }).execute()
        except Exception as e:
            logger.error(f"[SUPABASE ERROR] update_trip: {e}")
        
    def list_trips(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            res = self.client.table("trips").select("*").eq("user_id", user_id).execute()
            return res.data
        except Exception as e:
            logger.error(f"[SUPABASE ERROR] list_trips: {e}")
            return []
        
    def log_event(self, trip_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        try:
            self.client.table("trip_events").insert({
                "trip_id": trip_id,
                "event_type": event_type,
                "payload": payload
            }).execute()
        except Exception as e:
            logger.error(f"[SUPABASE ERROR] log_event: {e}")
        
    def get_events(self, trip_id: str) -> List[Dict[str, Any]]:
        try:
            res = self.client.table("trip_events").select("*").eq("trip_id", trip_id).execute()
            return res.data
        except Exception as e:
            logger.error(f"[SUPABASE ERROR] get_events: {e}")
            return []

def get_trip_repository() -> TripRepository:
    sb_url = os.getenv("SUPABASE_URL")
    sb_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if sb_url and sb_key and sb_url != "your_supabase_url_here":
        return SupabaseTripRepository(sb_url, sb_key)
    return InMemoryTripRepository()
"""
write_file(f"{backend_dir}/db/repositories.py", repos_patch)

# Patch trips router to use User dependency
trips_router_patch = """
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.db.repositories import get_trip_repository
from app.api.auth import get_current_user, User
import uuid

router = APIRouter()

@router.get("/")
def list_trips(user: User = Depends(get_current_user)):
    repo = get_trip_repository()
    return repo.list_trips(user.id)

@router.get("/{trip_id}")
def get_trip(trip_id: str, user: User = Depends(get_current_user)):
    repo = get_trip_repository()
    trip = repo.get_trip(trip_id, user.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@router.post("/")
def create_trip(trip_data: dict, user: User = Depends(get_current_user)):
    repo = get_trip_repository()
    trip_id = str(uuid.uuid4())
    repo.update_trip(trip_id, trip_data, user.id)
    return {"id": trip_id, "status": "created"}
"""
write_file(f"{backend_dir}/api/trips.py", trips_router_patch)

# Auth tests
test_auth = """
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
"""
write_file(f"{tests_dir}/test_auth.py", test_auth)
