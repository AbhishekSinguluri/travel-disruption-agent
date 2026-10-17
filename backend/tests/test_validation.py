from fastapi.testclient import TestClient
from app.main import app
from app.services.mock_db import MOCK_DB, demo_trip

client = TestClient(app)

def test_validate_valid_trip():
    MOCK_DB["trips"]["trip-val"] = demo_trip.model_dump()
    res = client.post("/api/trips/trip-val/validate")
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert "issues" in data
