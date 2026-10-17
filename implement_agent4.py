import os

BACKEND_DIR = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend"
FRONTEND_DIR = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\frontend"

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {path}")

# 1. schemas/booking.py
booking_schema = """
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class Baggage(BaseModel):
    checked: Optional[str] = None
    cabin: Optional[str] = None

class BookingSchema(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    booking_type: str # FLIGHT, HOTEL, TRAIN, RESTAURANT
    title: str
    provider: Optional[str] = None
    booking_reference: Optional[str] = None
    flight_number: Optional[str] = None
    departure_location: Optional[str] = None
    arrival_location: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    status: str
    domestic_international: Optional[str] = None
    baggage: Optional[Baggage] = None
    raw_extraction_metadata: Optional[Dict[str, Any]] = None

class BookingEvent(BaseModel):
    id: Optional[str] = None
    booking_id: str
    event_type: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    source_message_id: str
    source_thread_id: Optional[str] = None
    detected_at: Optional[datetime] = None
    confidence: str

class BookingAlert(BaseModel):
    id: Optional[str] = None
    user_id: str
    booking_id: str
    event_id: str
    title: str
    message: str
    severity: str # LOW, MEDIUM, HIGH
    read: bool = False
    created_at: Optional[datetime] = None

class GmailConnection(BaseModel):
    id: Optional[str] = None
    user_id: str
    email: str
    provider: str = "gmail"
    encrypted_token_reference: str
"""

# 2. services/gmail_provider.py
gmail_provider = """
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class GmailProvider:
    def connect(self): ...
    def search_messages(self, query: str, days: int = 5) -> List[Dict[str, Any]]: ...
    def get_message(self, message_id: str) -> Dict[str, Any]: ...

class MockGmailProvider(GmailProvider):
    def connect(self):
        logger.info("[MOCK] Connected to Gmail")
        return {"status": "connected", "email": "demo@example.com"}
        
    def search_messages(self, query: str, days: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"[MOCK] Searching Gmail for '{query}' in last {days} days")
        # Simulating finding a booking email
        return [
            {
                "id": "msg-mock-1",
                "threadId": "thread-mock-1",
                "snippet": "Your Air India AI 123 flight booking from Hyderabad to Delhi is confirmed.",
                "subject": "Booking Confirmation: Air India AI 123",
                "date": "2026-10-01T10:00:00Z"
            }
        ]

    def get_message(self, message_id: str) -> Dict[str, Any]:
        logger.info(f"[MOCK] Getting message {message_id}")
        return {
            "id": message_id,
            "body": "Your Air India AI 123 flight originally scheduled for 09:20 has been delayed. The new departure time is 11:10."
        }

def get_gmail_provider(api_key: Optional[str] = None) -> GmailProvider:
    return MockGmailProvider()
"""

# 3. api/bookings.py
api_bookings = """
from fastapi import APIRouter
from app.schemas.booking import BookingSchema
from app.db.repositories import get_booking_repository
import uuid
import datetime

router = APIRouter()

@router.post("/extract")
async def extract_booking(text: str = None):
    # Mock extraction for Agent 4 MVP
    return {
        "booking_type": "FLIGHT",
        "title": "Air India AI 123",
        "provider": "Air India",
        "booking_reference": "ABC123",
        "flight_number": "AI 123",
        "departure_location": "Hyderabad",
        "arrival_location": "Delhi",
        "departure_time": "09:20",
        "arrival_time": "11:35",
        "status": "Confirmed",
        "domestic_international": "Domestic",
        "baggage": {"checked": "20 kg", "cabin": "7 kg"}
    }

@router.post("/")
async def create_booking(booking: BookingSchema):
    repo = get_booking_repository()
    booking.id = str(uuid.uuid4())
    repo.save_booking(booking.model_dump())
    return booking

@router.get("/")
async def list_bookings(user_id: str = "demo-user"):
    repo = get_booking_repository()
    return repo.list_bookings(user_id)

@router.post("/{booking_id}/monitor")
async def start_monitoring(booking_id: str):
    repo = get_booking_repository()
    repo.start_monitoring(booking_id)
    return {"status": "ACTIVE", "message": "Monitoring started"}
"""

# 4. api/gmail.py
api_gmail = """
from fastapi import APIRouter
from app.services.gmail_provider import get_gmail_provider

router = APIRouter()

@router.get("/connect")
async def connect_gmail():
    provider = get_gmail_provider()
    return provider.connect()

@router.get("/search")
async def search_gmail(query: str = ""):
    provider = get_gmail_provider()
    return provider.search_messages(query)
"""

# 5. api/alerts.py
api_alerts = """
from fastapi import APIRouter
from app.db.repositories import get_booking_repository

router = APIRouter()

@router.get("/")
async def get_alerts(user_id: str = "demo-user"):
    repo = get_booking_repository()
    return repo.get_alerts(user_id)
"""

# 6. app/db/repositories.py modification (append)
repo_append = """

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
"""

def main():
    write_file(os.path.join(BACKEND_DIR, "app/schemas/booking.py"), booking_schema)
    write_file(os.path.join(BACKEND_DIR, "app/services/gmail_provider.py"), gmail_provider)
    write_file(os.path.join(BACKEND_DIR, "app/api/bookings.py"), api_bookings)
    write_file(os.path.join(BACKEND_DIR, "app/api/gmail.py"), api_gmail)
    write_file(os.path.join(BACKEND_DIR, "app/api/alerts.py"), api_alerts)
    
    repo_path = os.path.join(BACKEND_DIR, "app/db/repositories.py")
    with open(repo_path, "a", encoding="utf-8") as f:
        f.write(repo_append)
    print("Appended to repositories.py")

if __name__ == "__main__":
    main()
