from fastapi.testclient import TestClient
from app.main import app
from app.services.mock_db import MOCK_DB, demo_trip

client = TestClient(app)

def setup_function():
    MOCK_DB["trips"]["trip-graph"] = demo_trip.model_dump()

def test_shift_future_stops():
    trip_id = "trip-graph"
    # Delay by 15 mins
    req = {"stop_id": "stop-1", "minutes": 15}
    res = client.post(f"/api/trips/{trip_id}/shift", json=req)
    assert res.status_code == 200
    trip = res.json()["trip"]
    # Check if time is shifted (since demo starts at 09:30 normally)
    # The first stop should be 09:45 if it was UPCOMING/PLANNED.
    assert trip["days"][0]["stops"][0]["start_time"] != "09:30"

def test_skip_next_stop():
    trip_id = "trip-graph"
    req = {"stop_id": "stop-1"}
    res = client.post(f"/api/trips/{trip_id}/skip", json=req)
    assert res.status_code == 200
    # verify
    res = client.get(f"/api/trips/{trip_id}")
    trip = res.json()
    assert trip["days"][0]["stops"][0]["status"] == "SKIPPED"

def test_weather_disruption():
    trip_id = "trip-graph"
    req = {"type": "WEATHER_DISRUPTION", "affected_stop_id": "stop-4"}
    res = client.post(f"/api/trips/{trip_id}/simulate-disruption", json=req)
    assert res.status_code == 200
    state = res.json()["state"]
    assert "active_disruption" in state

def test_normal_delay_alternative_search():
    trip_id = "trip-graph"
    req = {"type": "NORMAL_DELAY", "affected_stop_id": "stop-4"}
    res = client.post(f"/api/trips/{trip_id}/simulate-disruption", json=req)
    assert res.status_code == 200
    state = res.json()["state"]
    assert state["active_disruption"]["type"] == "NORMAL_DELAY"
    assert state["active_disruption"]["type"] != "WEATHER_DISRUPTION"
