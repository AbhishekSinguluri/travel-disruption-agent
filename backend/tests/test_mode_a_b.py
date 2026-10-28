import pytest
from app.schemas.booking import CanonicalBooking, GmailReadIntent
from app.services.booking_extractor import BookingExtractor
from fastapi.testclient import TestClient
from app.main import app

def test_intent_conversational():
    extractor = BookingExtractor()
    res = extractor.extract_intent_or_booking("check my recent emails")
    assert res.mode == "READ_GMAIL"

def test_intent_structured():
    extractor = BookingExtractor()
    res = extractor.extract_intent_or_booking("Here is my booking ref X123")
    assert res.mode == "STRUCTURED_BOOKING"

def test_api_extract_text_mode_a():
    client = TestClient(app)
    response = client.post("/api/bookings/extract", data={"text": "check my recent emails"})
    assert response.status_code == 200
    data = response.json()
    assert ("Gmail" in data["status"]) or ("Extracted" in data["status"])

def test_api_extract_text_mode_b():
    client = TestClient(app)
    response = client.post("/api/bookings/extract", data={"text": "Booking ref X123 for Flight AI 123"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Confirmed" # Mock status

def test_api_extract_pdf():
    client = TestClient(app)
    response = client.post("/api/bookings/extract", files={"file": ("test.pdf", b"dummy pdf", "application/pdf")})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Error"
    
def test_api_extract_image():
    client = TestClient(app)
    response = client.post("/api/bookings/extract", files={"file": ("test.png", b"dummy image", "image/png")})
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "Mock"
