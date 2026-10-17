from fastapi.testclient import TestClient
from app.main import app
from app.services.mock_db import MOCK_DB

client = TestClient(app)

def test_full_e2e_demo_flow():
    # 1. IMPORT
    import_res = client.post("/api/import/text", json={"text": "Day 1 9AM Hotel, 10AM Beach"})
    assert import_res.status_code == 200
    extracted = import_res.json()
    assert extracted["name"] != ""
    
    # 2. SAVE (Create trip)
    create_res = client.post("/api/trips/", json=extracted)
    assert create_res.status_code == 200
    trip_id = create_res.json()["id"]
    
    # 3. VALIDATE
    # Our mocked endpoints return validation summaries
    val_res = client.post(f"/api/trips/{trip_id}/validate")
    assert val_res.status_code == 200
    
    # 4. MONITOR (Activate)
    # The monitoring endpoints check status
    mon_res = client.post(f"/api/monitor/{trip_id}/simulate", json={"event": "start"})
    assert mon_res.status_code == 200
    
    # 5. DETECT DISRUPTION
    disrupt_req = {"type": "WEATHER_DISRUPTION", "affected_stop_id": "stop-4"}
    disrupt_res = client.post(f"/api/trips/{trip_id}/simulate-disruption", json=disrupt_req)
    assert disrupt_res.status_code == 200
    assert "impact" in disrupt_res.json()
    
    # 6. USER RESPONDS BY VOICE -> INTENT
    # 7. UNDERSTAND INTENT
    intent_res = client.post("/api/voice/intent", json={"text": "Find me something indoors"})
    assert intent_res.status_code == 200
    intent = intent_res.json()["intent"]
    # Usually maps to FIND_ALTERNATIVE or REPORT_DELAY
    
    # 8. FIND REAL ALTERNATIVES (via preferences)
    pref_req = {"categories": ["Indoor"]}
    pref_res = client.post(f"/api/trips/{trip_id}/recovery/preferences", json=pref_req)
    assert pref_res.status_code == 200
    cands = pref_res.json()["candidates"]
    assert len(cands) > 0
    cand_id = cands[0]["id"]
    
    # 9. USER CONFIRMS -> REPLAN
    select_req = {"candidate_id": cand_id}
    select_res = client.post(f"/api/trips/{trip_id}/recovery/select", json=select_req)
    assert select_res.status_code == 200
    assert select_res.json()["success"] == True
    
    # 10. CONTINUE MONITORING (Check map state / get trip)
    get_res = client.get(f"/api/trips/{trip_id}")
    assert get_res.status_code == 200
    updated_trip = get_res.json()
    assert updated_trip["name"] == extracted["name"]
