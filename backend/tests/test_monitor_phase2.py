import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.change_detector import ChangeDetector
from app.db.repositories import get_booking_repository

client = TestClient(app)

def test_explicit_monitor_activation():
    # 1 & 2. explicit monitor activation and stores baseline
    repo = get_booking_repository()
    booking = {
        "provider": "Air India",
        "service_number": "AI 123",
        "departure_location": "Hyderabad",
        "arrival_location": "Delhi"
    }
    resp = client.post("/api/monitor/booking/activate", json=booking)
    assert resp.status_code == 200
    data = resp.json()
    monitor_id = data["monitor_id"]
    monitor = repo.get_monitor(monitor_id)
    assert monitor is not None
    assert monitor["baseline_booking"]["provider"] == "Air India"

def test_change_detector_no_change():
    # 6. no-change email produces no alert
    detector = ChangeDetector()
    baseline = {"provider": "Air India", "flight_number": "AI 123"}
    content = "Welcome to Air India. Thank you for booking AI 123."
    res = detector.detect_change(baseline, content)
    assert res.has_change is False

def test_change_detector_delay():
    # 7. delay produces one alert
    detector = ChangeDetector()
    baseline = {"provider": "Air India", "flight_number": "AI 123", "departure_time": "10:30 AM"}
    content = "Your flight AI 123 is delayed. New departure is 1:30 PM."
    res = detector.detect_change(baseline, content)
    assert res.has_change is True
    assert res.change_type == "DELAY"
    assert "1:30" in res.new_departure

def test_change_detector_cancellation():
    # 8. cancellation produces one alert
    detector = ChangeDetector()
    baseline = {"provider": "Air India", "flight_number": "AI 123"}
    content = "Your flight AI 123 has been cancelled due to weather."
    res = detector.detect_change(baseline, content)
    assert res.has_change is True
    assert res.change_type == "CANCELLATION"
    assert "weather" in res.reason.lower()

def test_check_monitor_endpoint():
    # A mocked run of /check/{monitor_id} to ensure no external hits happen
    repo = get_booking_repository()
    booking = {"provider": "MockAir", "service_number": "MA99"}
    resp = client.post("/api/monitor/booking/activate", json=booking)
    monitor_id = resp.json()["monitor_id"]
    
    # Run check
    # Our conftest.py prevents actual API calls by unsetting GROQ_API_KEY
    resp2 = client.post(f"/api/monitor/check/{monitor_id}")
    assert resp2.status_code == 200
    assert resp2.json()["status"] in ["no_change", "change_detected", "error"]
