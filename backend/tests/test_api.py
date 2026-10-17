from fastapi.testclient import TestClient
from app.main import app
import pytest
from app.services.mock_db import MOCK_DB, demo_trip

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_demo_trip():
    response = client.get("/api/trips/demo")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "trip-1"
    assert "days" in data

def test_simulate_disruption():
    MOCK_DB["trips"]["trip-api"] = demo_trip.model_dump()
    req = {"type": "WEATHER_DISRUPTION", "affected_stop_id": "stop-4"}
    response = client.post("/api/trips/trip-api/simulate-disruption", json=req)
    assert response.status_code == 200
    data = response.json()
    assert "impact" in data

def test_submit_preferences():
    # Requires simulate_disruption first due to mock_db state
    req = {"type": "WEATHER_DISRUPTION", "affected_stop_id": "stop-4"}
    client.post("/api/trips/trip-api/simulate-disruption", json=req)
    
    pref_req = {"categories": ["Indoor"], "budget": "Low"}
    response = client.post("/api/trips/trip-api/recovery/preferences", json=pref_req)
    assert response.status_code == 200
    data = response.json()
    assert "candidates" in data
    assert len(data["candidates"]) > 0

def test_select_candidate():
    # It must follow submit_preferences
    pref_req = {"categories": ["Indoor"], "budget": "Low"}
    res = client.post("/api/trips/trip-api/recovery/preferences", json=pref_req)
    cands = res.json().get("candidates", [])
    cand_id = cands[0]["id"] if cands else "mock-1"
    
    req = {"candidate_id": cand_id}
    response = client.post("/api/trips/trip-api/recovery/select", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
