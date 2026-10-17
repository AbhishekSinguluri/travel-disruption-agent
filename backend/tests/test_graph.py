from fastapi.testclient import TestClient
from app.main import app
from app.workflows.recovery_graph import app_graph
from app.services.mock_db import MOCK_DB, demo_trip

client = TestClient(app)

def setup_function():
    # reset mock DB
    MOCK_DB["trips"]["trip-graph"] = demo_trip.model_dump()

def test_full_workflow_execution():
    trip_id = "trip-graph"
    
    # 1. Simulate disruption
    req = {"type": "WEATHER_DISRUPTION", "affected_stop_id": "stop-4"}
    res = client.post(f"/api/trips/{trip_id}/simulate-disruption", json=req)
    assert res.status_code == 200
    
    # 2. Preferences
    pref_req = {"categories": ["Indoor"], "budget": "Low"}
    res = client.post(f"/api/trips/{trip_id}/recovery/preferences", json=pref_req)
    assert res.status_code == 200
    cands = res.json()["candidates"]
    assert len(cands) > 0
    cand_id = cands[0]["id"]
    
    # 3. Select candidate
    select_req = {"candidate_id": cand_id}
    res = client.post(f"/api/trips/{trip_id}/recovery/select", json=select_req)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] == True
