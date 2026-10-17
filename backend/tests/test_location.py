from fastapi.testclient import TestClient
from app.main import app
from app.services.mock_db import MOCK_DB, demo_trip

client = TestClient(app)

def test_location_update():
    MOCK_DB["trips"]["trip-loc"] = demo_trip.model_dump()
    loc = {
        "latitude": 17.3,
        "longitude": 78.4,
        "accuracy": 10.0,
        "timestamp": "2026-10-01T14:00:00Z"
    }
    res = client.post("/api/monitor/trip-loc/location", json=loc)
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
