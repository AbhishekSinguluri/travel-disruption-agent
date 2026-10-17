import os
import logging
from typing import Protocol, List, Dict, Any, Optional
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
from app.services.mock_db import MOCK_DB

logger = logging.getLogger(__name__)

class TripRepository(Protocol):
    def get_trip(self, trip_id: str, user_id: str) -> Optional[Dict[str, Any]]: ...
    def update_trip(self, trip_id: str, trip_data: Dict[str, Any], user_id: str) -> None: ...
    def delete_trip(self, trip_id: str, user_id: str) -> None: ...
    def list_trips(self, user_id: str) -> List[Dict[str, Any]]: ...
    def log_event(self, trip_id: str, event_type: str, payload: Dict[str, Any]) -> None: ...
    def get_events(self, trip_id: str) -> List[Dict[str, Any]]: ...

import sqlite3
import json

class InMemoryTripRepository:
    def __init__(self):
        import os
        self.db_path = os.path.join(os.path.dirname(__file__), "..", "..", "trips.db")
        self._init_db()
        
    def _get_conn(self):
        return sqlite3.connect(self.db_path)
        
    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trips (
                    trip_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    trip_data TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS init_state (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.commit()
            
            cur = conn.execute("SELECT value FROM init_state WHERE key = 'mock_loaded'")
            if not cur.fetchone():
                for mt in MOCK_DB["trips"].values():
                    conn.execute("INSERT OR REPLACE INTO trips (trip_id, user_id, trip_data) VALUES (?, ?, ?)",
                                 (mt["id"], mt.get("user_id", "demo-user"), json.dumps(mt)))
                conn.execute("INSERT INTO init_state (key, value) VALUES ('mock_loaded', '1')")
                conn.commit()

    def get_trip(self, trip_id: str, user_id: str = "demo-user") -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT trip_data FROM trips WHERE trip_id = ?", (trip_id,))
            row = cur.fetchone()
            if row:
                return json.loads(row[0])
            return None
        
    def update_trip(self, trip_id: str, trip_data: Dict[str, Any], user_id: str = "demo-user") -> None:
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO trips (trip_id, user_id, trip_data) VALUES (?, ?, ?)",
                         (trip_id, user_id, json.dumps(trip_data)))
            conn.commit()
        
    def delete_trip(self, trip_id: str, user_id: str = "demo-user") -> None:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM trips WHERE trip_id = ?", (trip_id,))
            conn.commit()
        
    def list_trips(self, user_id: str = "demo-user") -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT trip_data FROM trips")
            trips = [json.loads(row[0]) for row in cur.fetchall()]
            return trips
        
    def log_event(self, trip_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        if "events" not in MOCK_DB:
            MOCK_DB["events"] = []
        MOCK_DB["events"].append({"trip_id": trip_id, "event_type": event_type, "payload": payload})
        
    def get_events(self, trip_id: str) -> List[Dict[str, Any]]:
        return [e for e in MOCK_DB.get("events", []) if e["trip_id"] == trip_id]

class SupabaseTripRepository:
    def __init__(self, supabase_url: str, supabase_key: str):
        if not SUPABASE_AVAILABLE:
            raise ImportError("supabase module is not installed")
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
            self.client.table("trips").upsert({
                "id": trip_id,
                "user_id": user_id,
                "name": trip_data.get("name", "Trip"),
                "destination": trip_data.get("destination", "Unknown"),
                "start_date": trip_data.get("start_date", "2026-09-01"),
                "end_date": trip_data.get("end_date", "2026-09-05"),
                "days": trip_data.get("days", [])
            }).execute()
        except Exception as e:
            logger.error(f"[SUPABASE ERROR] update_trip: {e}")
            
    def delete_trip(self, trip_id: str, user_id: str) -> None:
        try:
            self.client.table("trips").delete().eq("id", trip_id).eq("user_id", user_id).execute()
        except Exception as e:
            logger.error(f"[SUPABASE ERROR] delete_trip: {e}")
        
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
    if SUPABASE_AVAILABLE and sb_url and sb_key and sb_url != "your_supabase_url_here":
        try:
            return SupabaseTripRepository(sb_url, sb_key)
        except ImportError:
            pass
    return InMemoryTripRepository()


class BookingRepository:
    def __init__(self):
        self.bookings = {}
        self.alerts = []
        
    def save_booking(self, booking_id: str, data: dict):
        self.bookings[booking_id] = data
        
    def get_booking(self, booking_id: str):
        return self.bookings.get(booking_id)
        
    def create_alert(self, alert: dict):
        self.alerts.append(alert)
        
    def get_alerts(self):
        return self.alerts

booking_repo = BookingRepository()
def get_booking_repository(): return booking_repo


class BookingRepository:
    def __init__(self):
        if "bookings" not in MOCK_DB:
            MOCK_DB["bookings"] = {}
        if "alerts" not in MOCK_DB:
            MOCK_DB["alerts"] = []
        if "monitoring" not in MOCK_DB:
            MOCK_DB["monitoring"] = {}
            
    def save_booking(self, booking: dict):
        MOCK_DB["bookings"][booking["id"]] = booking
        
    def list_bookings(self, user_id: str):
        return [b for b in MOCK_DB["bookings"].values() if b.get("user_id") == user_id or user_id == "demo-user"]
        
    def start_monitoring(self, booking_id: str):
        import datetime
        MOCK_DB["monitoring"][booking_id] = {
            "status": "ACTIVE",
            "last_checked": datetime.datetime.now().isoformat(),
            "next_check": (datetime.datetime.now() + datetime.timedelta(minutes=5)).isoformat()
        }
        
    def save_monitor(self, monitor_id: str, monitor_data: dict):
        MOCK_DB["monitoring"][monitor_id] = monitor_data
        
    def get_monitor(self, monitor_id: str):
        return MOCK_DB["monitoring"].get(monitor_id)
        
    def get_alerts(self, user_id: str):
        # Return mock alert if requested
        if len(MOCK_DB["alerts"]) == 0:
            import uuid, datetime
            MOCK_DB["alerts"].append({
                "id": str(uuid.uuid4()),
                "user_id": "demo-user",
                "booking_id": "mock-booking",
                "title": "FLIGHT DELAY",
                "message": "Air India AI 123 from Hyderabad to Delhi delayed. Original: 09:20. New: 11:10.",
                "severity": "HIGH",
                "read": False,
                "created_at": datetime.datetime.now().isoformat()
            })
        return MOCK_DB["alerts"]

def get_booking_repository():
    return BookingRepository()
