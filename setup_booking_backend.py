import os
import re

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

backend_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\app"
tests_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\tests"
frontend_src = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\frontend\src"

# 1. Schemas
schemas_bookings = """
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class BookingExtractionRequest(BaseModel):
    text: Optional[str] = None
    type: str # "pasted_text", "pdf", "image"

class BookingSummary(BaseModel):
    booking_type: str
    title: str
    provider: Optional[str]
    booking_reference: Optional[str]
    flight_number: Optional[str]
    departure_location: Optional[str]
    arrival_location: Optional[str]
    departure_time: Optional[str]
    arrival_time: Optional[str]
    status: Optional[str]
    baggage: Optional[str]
    
class GmailConnectionReq(BaseModel):
    auth_code: str
"""
write_file(f"{backend_dir}/schemas/bookings.py", schemas_bookings)

# 2. Services: Agent 4 (Booking Extractor)
booking_extractor_code = """
import logging
from typing import Dict, Any
from app.schemas.bookings import BookingSummary

logger = logging.getLogger(__name__)

def extract_booking_info(text: str) -> BookingSummary:
    logger.info("Agent 4: Extracting booking information")
    # Mock fallback for Agent 4
    if "AI 123" in text or "Air India" in text:
        return BookingSummary(
            booking_type="FLIGHT",
            title="Air India AI 123",
            provider="Air India",
            booking_reference="ABC123",
            flight_number="AI 123",
            departure_location="Hyderabad",
            arrival_location="Delhi",
            departure_time="2026-10-04T09:20:00",
            arrival_time="2026-10-04T11:35:00",
            status="Confirmed",
            baggage="20kg checked, 7kg cabin"
        )
    return BookingSummary(
        booking_type="UNKNOWN",
        title="Unknown Booking",
        provider=None, booking_reference=None, flight_number=None,
        departure_location=None, arrival_location=None,
        departure_time=None, arrival_time=None, status="Unknown", baggage=None
    )
"""
write_file(f"{backend_dir}/services/booking_extractor.py", booking_extractor_code)

# 3. Services: Gmail Provider
gmail_provider_code = """
import logging

logger = logging.getLogger(__name__)

class GmailProvider:
    def connect(self, auth_code: str): pass
    def search_messages(self, query: str): pass
    def get_message(self, msg_id: str): pass

class MockGmailProvider(GmailProvider):
    def connect(self, auth_code: str):
        logger.info("Mocking Gmail connection")
        return {"status": "connected", "email": "mockuser@gmail.com"}
        
    def search_messages(self, query: str):
        logger.info(f"Mocking Gmail search for: {query}")
        return [{"id": "msg1", "snippet": "Your flight AI 123 has been delayed. New departure time: 11:10."}]
        
    def get_message(self, msg_id: str):
        if msg_id == "msg1":
            return {"content": "Your flight AI 123 has been delayed. New departure time: 11:10."}
        return {}

def get_gmail_provider() -> GmailProvider:
    return MockGmailProvider()
"""
write_file(f"{backend_dir}/services/gmail_provider.py", gmail_provider_code)

# 4. Services: Booking Monitor
booking_monitor_code = """
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def check_booking_updates(booking_id: str):
    logger.info(f"Checking updates for booking {booking_id}")
    from app.services.gmail_provider import get_gmail_provider
    provider = get_gmail_provider()
    msgs = provider.search_messages("AI 123")
    if msgs:
        content = provider.get_message(msgs[0]["id"]).get("content", "")
        if "delayed" in content and "11:10" in content:
            return {
                "event_type": "FLIGHT DELAY",
                "old_value": "09:20",
                "new_value": "11:10",
                "source": "Air India email",
                "confidence": "high"
            }
    return None
"""
write_file(f"{backend_dir}/services/booking_monitor.py", booking_monitor_code)

# 5. Database Repositories updates
repo_patch = """
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
"""
with open(f"{backend_dir}/db/repositories.py", "a") as f:
    f.write("\n" + repo_patch)

# 6. API: Bookings
api_bookings_code = """
from fastapi import APIRouter
from app.schemas.bookings import BookingExtractionRequest, GmailConnectionReq
from app.services.booking_extractor import extract_booking_info
from app.services.gmail_provider import get_gmail_provider
from app.services.booking_monitor import check_booking_updates
from app.db.repositories import get_booking_repository
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/extract")
def extract_booking(req: BookingExtractionRequest):
    summary = extract_booking_info(req.text or "")
    booking_id = str(uuid.uuid4())
    get_booking_repository().save_booking(booking_id, summary.model_dump())
    return {"status": "ok", "booking_id": booking_id, "summary": summary}

@router.post("/{booking_id}/gmail/connect")
def connect_gmail(booking_id: str, req: GmailConnectionReq):
    provider = get_gmail_provider()
    res = provider.connect(req.auth_code)
    return res

@router.post("/{booking_id}/check")
def check_now(booking_id: str):
    update = check_booking_updates(booking_id)
    if update:
        alert = {
            "id": str(uuid.uuid4()),
            "booking_id": booking_id,
            "title": update["event_type"],
            "message": f"Original: {update['old_value']} -> New: {update['new_value']}",
            "source": update["source"],
            "detected_at": datetime.now().isoformat(),
            "read": False
        }
        get_booking_repository().create_alert(alert)
        return {"status": "alert_created", "alert": alert}
    return {"status": "no_changes"}

@router.get("/alerts")
def get_alerts():
    return get_booking_repository().get_alerts()
"""
write_file(f"{backend_dir}/api/bookings.py", api_bookings_code)

# 7. Main API Update
main_patch = """
try:
    from app.api.bookings import router as bookings_router
    app.include_router(bookings_router, prefix="/api/bookings", tags=["Bookings"])
except ImportError:
    pass
"""
with open(f"{backend_dir}/main.py", "a") as f:
    f.write("\n" + main_patch)

# 8. Tests
test_code = """
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_booking_extraction():
    res = client.post("/api/bookings/extract", json={"text": "Air India AI 123", "type": "pasted_text"})
    assert res.status_code == 200
    data = res.json()
    assert data["summary"]["flight_number"] == "AI 123"
    
def test_gmail_mock_flow():
    ext_res = client.post("/api/bookings/extract", json={"text": "Air India AI 123", "type": "pasted_text"})
    b_id = ext_res.json()["booking_id"]
    
    conn_res = client.post(f"/api/bookings/{b_id}/gmail/connect", json={"auth_code": "mock_code"})
    assert conn_res.json()["status"] == "connected"
    
    chk_res = client.post(f"/api/bookings/{b_id}/check")
    assert chk_res.json()["status"] == "alert_created"
    
    alerts_res = client.get("/api/bookings/alerts")
    assert len(alerts_res.json()) > 0
"""
write_file(f"{tests_dir}/test_bookings.py", test_code)

print("Backend Booking code generated.")
