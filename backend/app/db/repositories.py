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
        import os
        import sqlite3
        self.db_path = os.path.join(os.path.dirname(__file__), "..", "..", "trips.db")
        self._init_db()
        if "bookings" not in MOCK_DB:
            MOCK_DB["bookings"] = {}
        if "alerts" not in MOCK_DB:
            MOCK_DB["alerts"] = []
        if "monitoring" not in MOCK_DB:
            MOCK_DB["monitoring"] = {}
            
    def _get_conn(self):
        import sqlite3
        return sqlite3.connect(self.db_path, timeout=10)
        
    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    booking_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitors (
                    monitor_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    booking_id TEXT,
                    monitor_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    booking_id TEXT,
                    alert_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_booking(self, booking: dict) -> dict:
        import uuid
        import json
        b = dict(booking)
        user_id = b.get("user_id") or "demo-user"
        b["user_id"] = user_id
        
        # Duplicate detection using explicit booking reference and provider
        existing_id = None
        ref = b.get("booking_reference")
        prov = b.get("provider")
        
        if ref and ref != "N/A" and prov:
            with self._get_conn() as conn:
                cur = conn.execute("SELECT id, booking_data FROM bookings WHERE user_id = ?", (user_id,))
                for row in cur.fetchall():
                    try:
                        data = json.loads(row[1])
                        d_ref = data.get("booking_reference")
                        d_prov = data.get("provider")
                        if d_ref and d_ref != "N/A" and ref.strip().lower() == d_ref.strip().lower() and prov.strip().lower() == (d_prov or "").strip().lower():
                            existing_id = row[0]
                            break
                    except Exception:
                        pass

        booking_id = existing_id or b.get("id") or str(uuid.uuid4())
        b["id"] = booking_id

        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO bookings (id, user_id, booking_data) VALUES (?, ?, ?)",
                         (booking_id, user_id, json.dumps(b)))
            conn.commit()
            
        MOCK_DB["bookings"][booking_id] = b
        return b
        
    def get_booking(self, booking_id: str) -> Optional[dict]:
        import json
        with self._get_conn() as conn:
            cur = conn.execute("SELECT booking_data FROM bookings WHERE id = ?", (booking_id,))
            row = cur.fetchone()
            if row:
                return json.loads(row[0])
        return MOCK_DB["bookings"].get(booking_id)
        
    def list_bookings(self, user_id: str = "demo-user") -> List[dict]:
        import json
        bookings = []
        seen_ids = set()
        with self._get_conn() as conn:
            if user_id == "demo-user":
                cur = conn.execute("SELECT id, booking_data FROM bookings ORDER BY created_at DESC")
            else:
                cur = conn.execute("SELECT id, booking_data FROM bookings WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            for row in cur.fetchall():
                try:
                    data = json.loads(row[1])
                    b_id = row[0]
                    seen_ids.add(b_id)
                    
                    # Attach monitor status if exists
                    m_cur = conn.execute("SELECT monitor_data FROM monitors WHERE booking_id = ? OR monitor_id = ?", (b_id, b_id))
                    m_row = m_cur.fetchone()
                    if m_row:
                        m_data = json.loads(m_row[0])
                        data["monitoring_active"] = (m_data.get("status") == "ACTIVE")
                        data["monitor_id"] = m_data.get("monitor_id")
                        data["monitor_status"] = m_data.get("status", "ACTIVE")
                        data["last_checked_at"] = m_data.get("last_checked_at")
                    else:
                        m_in_memory = MOCK_DB.get("monitoring", {}).get(b_id)
                        if m_in_memory:
                            data["monitoring_active"] = (m_in_memory.get("status") == "ACTIVE")
                            data["monitor_id"] = b_id
                            data["monitor_status"] = m_in_memory.get("status", "ACTIVE")
                            data["last_checked_at"] = m_in_memory.get("last_checked")
                            
                    bookings.append(data)
                except Exception:
                    pass

        # Include any in-memory bookings from MOCK_DB not yet seen
        for b_id, b in MOCK_DB.get("bookings", {}).items():
            if b_id not in seen_ids and (b.get("user_id") == user_id or user_id == "demo-user"):
                bookings.append(b)
                
        return bookings

    def delete_booking(self, booking_id: str, user_id: str = "demo-user") -> bool:
        with self._get_conn() as conn:
            if user_id == "demo-user":
                conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
            else:
                conn.execute("DELETE FROM bookings WHERE id = ? AND user_id = ?", (booking_id, user_id))
            conn.execute("DELETE FROM monitors WHERE booking_id = ? OR monitor_id = ?", (booking_id, booking_id))
            conn.execute("DELETE FROM alerts WHERE booking_id = ?", (booking_id,))
            conn.commit()

        if booking_id in MOCK_DB.get("bookings", {}):
            del MOCK_DB["bookings"][booking_id]
        if booking_id in MOCK_DB.get("monitoring", {}):
            del MOCK_DB["monitoring"][booking_id]
        if "alerts" in MOCK_DB:
            MOCK_DB["alerts"] = [a for a in MOCK_DB["alerts"] if a.get("booking_id") != booking_id]
        return True
        
    def save_monitor(self, monitor_id: str, monitor_data: dict):
        import json
        booking_id = monitor_data.get("booking_id") or monitor_id
        user_id = monitor_data.get("user_id") or "demo-user"
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO monitors (monitor_id, user_id, booking_id, monitor_data) VALUES (?, ?, ?, ?)",
                         (monitor_id, user_id, booking_id, json.dumps(monitor_data)))
            # Update booking status if booking exists
            b_cur = conn.execute("SELECT booking_data FROM bookings WHERE id = ?", (booking_id,))
            b_row = b_cur.fetchone()
            if b_row:
                b_dict = json.loads(b_row[0])
                b_dict["monitoring_active"] = True
                b_dict["monitor_id"] = monitor_id
                b_dict["status"] = monitor_data.get("status", "ACTIVE")
                conn.execute("UPDATE bookings SET booking_data = ? WHERE id = ?", (json.dumps(b_dict), booking_id))
            conn.commit()
            
        MOCK_DB["monitoring"][monitor_id] = monitor_data
        
    def get_monitor(self, monitor_id: str) -> Optional[dict]:
        import json
        with self._get_conn() as conn:
            cur = conn.execute("SELECT monitor_data FROM monitors WHERE monitor_id = ? OR booking_id = ?", (monitor_id, monitor_id))
            row = cur.fetchone()
            if row:
                return json.loads(row[0])
        return MOCK_DB["monitoring"].get(monitor_id)
        
    def start_monitoring(self, booking_id: str):
        import datetime
        monitor_state = {
            "monitor_id": booking_id,
            "booking_id": booking_id,
            "status": "ACTIVE",
            "last_checked": datetime.datetime.now().isoformat(),
            "next_check": (datetime.datetime.now() + datetime.timedelta(minutes=5)).isoformat()
        }
        self.save_monitor(booking_id, monitor_state)
        
    def create_alert(self, alert: dict):
        import json
        import uuid
        alert_id = alert.get("id") or str(uuid.uuid4())
        booking_id = alert.get("booking_id") or alert.get("monitor_id") or ""
        user_id = alert.get("user_id") or "demo-user"
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO alerts (id, user_id, booking_id, alert_data) VALUES (?, ?, ?, ?)",
                         (alert_id, user_id, booking_id, json.dumps(alert)))
            conn.commit()
        if "alerts" not in MOCK_DB:
            MOCK_DB["alerts"] = []
        MOCK_DB["alerts"].append(alert)
        
    def get_alerts(self, user_id: str = "demo-user") -> List[dict]:
        import json
        alerts = []
        with self._get_conn() as conn:
            if user_id == "demo-user":
                cur = conn.execute("SELECT alert_data FROM alerts ORDER BY created_at DESC")
            else:
                cur = conn.execute("SELECT alert_data FROM alerts WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            for row in cur.fetchall():
                try:
                    alerts.append(json.loads(row[0]))
                except Exception:
                    pass
        if len(alerts) == 0 and len(MOCK_DB.get("alerts", [])) == 0:
            import uuid, datetime
            mock_alert = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "booking_id": "mock-booking",
                "title": "FLIGHT DELAY",
                "message": "Air India AI 123 from Hyderabad to Delhi delayed. Original: 09:20. New: 11:10.",
                "severity": "HIGH",
                "read": False,
                "created_at": datetime.datetime.now().isoformat()
            }
            alerts.append(mock_alert)
            MOCK_DB["alerts"].append(mock_alert)
        elif len(alerts) == 0:
            return MOCK_DB["alerts"]
        return alerts

_booking_repo_instance = None
def get_booking_repository() -> BookingRepository:
    global _booking_repo_instance
    if _booking_repo_instance is None:
        _booking_repo_instance = BookingRepository()
    return _booking_repo_instance
