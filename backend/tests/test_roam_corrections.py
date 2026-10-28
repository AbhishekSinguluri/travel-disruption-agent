from fastapi.testclient import TestClient
from app.main import app
from app.db.repositories import get_booking_repository

client = TestClient(app)

def test_booking_email_metadata_fields():
    # Test conversational Gmail search extraction
    res = client.post("/api/bookings/extract", data={"text": "Check my recent Air India emails"})
    assert res.status_code == 200
    data = res.json()
    assert "email_date" in data
    assert "email_time" in data
    assert "sender_email" in data
    assert data["email_date"] != ""
    assert data["email_time"] != ""
    assert "@" in data["sender_email"] or data["sender_email"] != ""

def test_multiple_bookings_persistence_and_independent_monitoring():
    repo = get_booking_repository()
    # 1. Search first booking (Flight)
    res1 = client.post("/api/bookings/extract", data={"text": "Air India AI 101 from HYD to DEL ref AI901", "user_id": "test-user-1"})
    assert res1.status_code == 200
    b1 = res1.json()
    b1_id = b1["id"]
    
    # 2. Search second booking (Train)
    res2 = client.post("/api/bookings/extract", data={"text": "IRCTC Train 12723 Telangana Express ref PNR88219", "user_id": "test-user-1"})
    assert res2.status_code == 200
    b2 = res2.json()
    b2_id = b2["id"]
    
    assert b1_id != b2_id, "Bookings must have distinct identifiers"
    
    # 3. Check list returns both bookings
    list_res = client.get("/api/bookings/?user_id=test-user-1")
    assert list_res.status_code == 200
    b_list = list_res.json()
    ids = [b["id"] for b in b_list]
    assert b1_id in ids
    assert b2_id in ids
    
    # 4. Activate monitoring on b1 only
    mon_res = client.post(f"/api/bookings/{b1_id}/monitor")
    assert mon_res.status_code == 200
    assert mon_res.json()["status"] == "ACTIVE"
    
    # 5. Delete b2
    del_res = client.delete(f"/api/bookings/{b2_id}?user_id=test-user-1")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"
    
    # 6. Verify b2 is gone and b1 remains
    list_res2 = client.get("/api/bookings/?user_id=test-user-1")
    ids2 = [b["id"] for b in list_res2.json()]
    assert b2_id not in ids2
    assert b1_id in ids2
    
    # Clean up b1
    client.delete(f"/api/bookings/{b1_id}?user_id=test-user-1")

def test_voice_transcribe_and_itinerary_import():
    # 1. Test voice transcribe endpoint
    files = {"file": ("recording.webm", b"mock audio bytes", "audio/webm")}
    res = client.post("/api/voice/transcribe", files=files)
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert "text" in res.json()
    
    # 2. Test itinerary text import (same workflow as voice Create Itinerary)
    voice_transcript = "Day 1 in Hyderabad: 10:00 AM visit Charminar, 01:00 PM lunch at Shadab, 04:00 PM visit Salar Jung Museum"
    import_res = client.post("/api/import/text", json={"text": voice_transcript})
    assert import_res.status_code == 200
    trip_data = import_res.json()
    assert "days" in trip_data
    assert len(trip_data["days"]) > 0
    stops = trip_data["days"][0].get("stops", [])
    assert len(stops) >= 1
