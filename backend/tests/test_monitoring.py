from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_simulate_endpoint():
    res = client.post("/api/monitor/trip-1/simulate", json={"event": "start", "value": 0})
    assert res.status_code == 200
