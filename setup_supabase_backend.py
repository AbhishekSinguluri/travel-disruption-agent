import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

backend_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\app"
tests_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\tests"

# --- ENV ---
env_update = """
# Supabase
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
DATABASE_URL=your_postgres_db_url_here
"""
with open(r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\.env.example", "a") as f:
    f.write(env_update)

# --- DATABASE SCHEMA (SQL) ---
sql = """
-- Table: trips
CREATE TABLE IF NOT EXISTS trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL, -- references auth.users
    name TEXT NOT NULL,
    destination TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'PLANNING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: trip_days
CREATE TABLE IF NOT EXISTS trip_days (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    day_number INT NOT NULL
);

-- Table: itinerary_stops
CREATE TABLE IF NOT EXISTS itinerary_stops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_day_id UUID NOT NULL REFERENCES trip_days(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    location_name TEXT NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_minutes INT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PLANNED',
    priority TEXT,
    notes TEXT,
    external_place_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: trip_events
CREATE TABLE IF NOT EXISTS trip_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    stop_id UUID,
    payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row Level Security (RLS)
ALTER TABLE trips ENABLE ROW LEVEL SECURITY;
ALTER TABLE trip_days ENABLE ROW LEVEL SECURITY;
ALTER TABLE itinerary_stops ENABLE ROW LEVEL SECURITY;
ALTER TABLE trip_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only access their own trips" ON trips
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can only access days of their trips" ON trip_days
    FOR ALL USING (trip_id IN (SELECT id FROM trips WHERE user_id = auth.uid()));

CREATE POLICY "Users can only access stops of their trips" ON itinerary_stops
    FOR ALL USING (trip_day_id IN (SELECT id FROM trip_days WHERE trip_id IN (SELECT id FROM trips WHERE user_id = auth.uid())));

CREATE POLICY "Users can only access events of their trips" ON trip_events
    FOR ALL USING (trip_id IN (SELECT id FROM trips WHERE user_id = auth.uid()));
"""
write_file(f"{backend_dir}/db/schema.sql", sql)

# --- REPOSITORIES ---
repositories = """
import os
import logging
from typing import Protocol, List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class TripRepository(Protocol):
    def get_trip(self, trip_id: str, user_id: str) -> Optional[Dict[str, Any]]: ...
    def update_trip(self, trip_id: str, trip_data: Dict[str, Any], user_id: str) -> None: ...
    def list_trips(self, user_id: str) -> List[Dict[str, Any]]: ...
    def log_event(self, trip_id: str, event_type: str, payload: Dict[str, Any]) -> None: ...
    def get_events(self, trip_id: str) -> List[Dict[str, Any]]: ...

# Using the old mock db as in-memory
from app.services.mock_db import MOCK_DB

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
        self.url = supabase_url
        self.key = supabase_key
        # Normally use supabase-py client here
        
    def get_trip(self, trip_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        logger.info(f"[SUPABASE] Fetching trip {trip_id} for user {user_id}")
        return None
        
    def update_trip(self, trip_id: str, trip_data: Dict[str, Any], user_id: str) -> None:
        pass
        
    def list_trips(self, user_id: str) -> List[Dict[str, Any]]:
        return []
        
    def log_event(self, trip_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        pass
        
    def get_events(self, trip_id: str) -> List[Dict[str, Any]]:
        return []

def get_trip_repository() -> TripRepository:
    sb_url = os.getenv("SUPABASE_URL")
    sb_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if sb_url and sb_key and sb_url != "your_supabase_url_here":
        return SupabaseTripRepository(sb_url, sb_key)
    return InMemoryTripRepository()
"""
write_file(f"{backend_dir}/db/repositories.py", repositories)

test_repo = """
from app.db.repositories import get_trip_repository, InMemoryTripRepository
import os
from unittest.mock import patch

def test_repo_fallback():
    with patch.dict(os.environ, clear=True):
        repo = get_trip_repository()
        assert isinstance(repo, InMemoryTripRepository)

def test_trip_events():
    repo = InMemoryTripRepository()
    repo.log_event("trip-1", "TEST_EVENT", {"data": 123})
    events = repo.get_events("trip-1")
    assert len(events) > 0
    assert events[-1]["event_type"] == "TEST_EVENT"
"""
write_file(f"{tests_dir}/test_repositories.py", test_repo)

# Patch mock_db logic across files to use get_trip_repository() instead of mock_db directly
import glob

for filepath in glob.glob(f"{backend_dir}/workflows/*.py") + [f"{backend_dir}/api/trips.py"]:
    with open(filepath, 'r') as f:
        content = f.read()
    
    if "from app.services.mock_db import get_trip, update_trip" in content:
        content = content.replace("from app.services.mock_db import get_trip, update_trip", "from app.db.repositories import get_trip_repository")
        content = content.replace("trip = get_trip(trip_id)", "repo = get_trip_repository()\n    trip = repo.get_trip(trip_id, 'demo-user')")
        content = content.replace("update_trip(state[\"trip_id\"], trip)", "repo = get_trip_repository()\n    repo.update_trip(state[\"trip_id\"], trip, 'demo-user')")
        write_file(filepath, content)
    elif "from app.services.mock_db import get_trip" in content:
        content = content.replace("from app.services.mock_db import get_trip", "from app.db.repositories import get_trip_repository")
        content = content.replace("trip = get_trip(trip_id)", "repo = get_trip_repository()\n    trip = repo.get_trip(trip_id, 'demo-user')")
        content = content.replace("trip = get_trip(state[\"trip_id\"])", "repo = get_trip_repository()\n    trip = repo.get_trip(state[\"trip_id\"], 'demo-user')")
        write_file(filepath, content)
        
    if "api/trips.py" in filepath:
        content = content.replace("from app.services.mock_db import get_trip, MOCK_DB", "from app.db.repositories import get_trip_repository")
        content = content.replace("get_trip(\"trip-1\")", "get_trip_repository().get_trip(\"trip-1\", \"demo-user\")")
        write_file(filepath, content)

"""
write_file(f"{backend_dir}/scripts/seed_demo.py", "print('Seed script ready')")
"""
