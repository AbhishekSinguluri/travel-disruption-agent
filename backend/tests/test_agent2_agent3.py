import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.agents.builder import build_canonical_trip, resolve_location
from app.services.travel_companion import TravelCompanionService
from app.agents.companion import chat_with_companion

client = TestClient(app)

def test_resolve_location_generic():
    assert resolve_location("Lunch", "Food", "Hyderabad") is None
    assert resolve_location("lunch around Laad Bazaar", "Food", "Hyderabad") is None
    assert resolve_location("Dinner", "Food", "Hyderabad") is None
    assert resolve_location("Shopping", "Shopping", "Hyderabad") is None
    assert resolve_location("Free time", "Activity", "Hyderabad") is None
    
    charminar = resolve_location("Charminar", "Attraction", "Hyderabad")
    assert charminar is not None
    assert charminar.id is not None
    assert charminar.latitude is not None

    shadab = resolve_location("Lunch at Shadab Hotel", "Food", "Hyderabad")
    assert shadab is not None
    assert shadab.id is not None
    
    laad = resolve_location("Laad Bazaar", "Shopping", "Hyderabad")
    assert laad is not None
    assert laad.id is not None

    jewel = resolve_location("Dinner at Jewel of Nizam", "Food", "Hyderabad")
    assert jewel is not None
    assert jewel.id is not None
    
    assert resolve_location("breakfast at Taj Deccan", "Food", "Hyderabad") is not None
    assert resolve_location("Taj Deccan", "Hotel", "Hyderabad") is not None

def test_build_canonical_trip():
    messy_payload = {
        "id": "test-trip-123",
        "name": "Hyderabad Trip",
        "destination": "Hyderabad",
        "start_date": "2026-10-01",
        "end_date": "2026-10-03",
        "days": [
            {
                "date": "2026-10-01",
                "stops": [
                    {"title": "leave hotel", "location_name": "Taj Deccan, Banjara Hills", "category": "Hotel"},
                    {"title": "Charminar", "category": "Attraction"},
                    {"title": "lunch around Laad Bazaar", "category": "Food"}
                ]
            }
        ]
    }
    
    canonical = build_canonical_trip(messy_payload)
    
    assert canonical["id"] == "test-trip-123"
    assert canonical["name"] == "Hyderabad Trip"
    assert len(canonical["days"]) == 1
    
    stops = canonical["days"][0]["stops"]
    assert len(stops) == 3
    
    # Taj Deccan
    assert stops[0]["title"] == "leave hotel"
    assert stops[0]["latitude"] is not None
    assert stops[0]["longitude"] is not None
    assert stops[0]["address"] is not None
    
    # Charminar
    assert stops[1]["title"] == "Charminar"
    assert stops[1]["latitude"] is not None
    
    # Lunch around Laad Bazaar (Generic, so should not have coordinates from the place provider if it's considered generic)
    assert stops[2]["title"] == "lunch around Laad Bazaar"
    assert stops[2]["latitude"] is None

def test_travel_companion_service():
    trip_data = {
        "days": [{
            "id": "day-1",
            "stops": [
                {"id": "stop-1", "title": "Charminar", "status": "COMPLETED", "start_time": "10:00", "opening_hours": {"open": "09:00", "close": "17:30"}},
                {"id": "stop-2", "title": "Salar Jung Museum", "status": "UPCOMING", "start_time": "14:00", "opening_hours": {"open": "10:00", "close": "17:30"}},
                {"id": "stop-3", "title": "Dinner", "status": "UPCOMING"}
            ]
        }]
    }
    
    svc = TravelCompanionService(trip_data)
    next_s = svc.get_next_stop()
    assert next_s["title"] == "Salar Jung Museum"
    
    rem = svc.get_remaining_stops()
    assert len(rem) == 2
    
    hours = svc.get_opening_hours("stop-2")
    assert hours["close"] == "17:30"
    
    warnings = svc.generate_warnings()
    assert len(warnings) == 1
    assert "Salar Jung Museum" in warnings[0]

def test_companion_chat():
    trip_data = {
        "destination": "Hyderabad",
        "days": [{
            "id": "day-1",
            "stops": [
                {"id": "stop-1", "title": "Charminar", "status": "UPCOMING", "start_time": "10:00"}
            ]
        }]
    }
    
    reply = chat_with_companion(trip_data, "Skip Charminar")
    assert "Skipping Charminar" in reply
    assert "[ Skip Charminar ]" in reply
    
    reply = chat_with_companion(trip_data, "What is next?")
    assert "Charminar" in reply
    
    reply = chat_with_companion(trip_data, "When does it close?")
    assert "5:30 PM" in reply

def test_api_trip_update_status():
    trip_data = {
        "id": "test-trip-status",
        "destination": "Hyderabad",
        "name": "Test",
        "days": [{
            "id": "day-1",
            "stops": [
                {"id": "s1", "title": "Charminar", "status": "UPCOMING"}
            ]
        }]
    }
    
    # create trip
    res = client.post("/api/trips/", json=trip_data)
    assert res.status_code == 200
    
    # update status
    res = client.post("/api/trips/test-trip-status/stop/s1/status", json={"status": "ARRIVED"})
    assert res.status_code == 200
    
    # check
    res = client.get("/api/trips/test-trip-status")
    trip = res.json()
    assert trip["days"][0]["stops"][0]["status"] == "ARRIVED"

