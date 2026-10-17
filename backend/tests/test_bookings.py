from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_booking_extraction():
    res = client.post("/api/bookings/extract", data={"text": "Air India AI 123"})
    assert res.status_code == 200
    data = res.json()
    assert data.get("flight_number") == "AI 123"
    
def test_gmail_mock_flow():
    ext_res = client.post("/api/bookings/extract", data={"text": "Air India AI 123"})
    b_id = ext_res.json().get("booking_id", "mock-booking")
    
    conn_res = client.get("/api/gmail/connect")
    assert conn_res.status_code == 500
    
    chk_res = client.post(f"/api/bookings/{b_id}/monitor")
    assert chk_res.json()["status"] == "ACTIVE"
    
    alerts_res = client.get("/api/alerts/")
    assert type(alerts_res.json()) == list
