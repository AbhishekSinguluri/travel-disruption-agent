import os
import re

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

backend_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\app"
tests_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\tests"

# --- SCHEMAS ---
schemas_val = """
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ValidationIssue(BaseModel):
    id: str
    severity: str
    type: str
    stop_id: Optional[str] = None
    message: str
    details: str
    suggested_action: Optional[str] = None

class ValidationResult(BaseModel):
    valid: bool
    issues: List[ValidationIssue]
    validated_stops: List[Dict[str, Any]]
    summary: Dict[str, Any]
"""
write_file(f"{backend_dir}/schemas/validation.py", schemas_val)

# --- WORKFLOW ---
validation_graph = """
import logging
import json
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, List, Dict, Any, Optional
from app.services.mock_db import get_trip
from app.services.providers import get_routes_provider
from app.schemas.validation import ValidationIssue

logger = logging.getLogger(__name__)

class ValidationState(TypedDict):
    trip_id: str
    trip_data: Optional[Dict[str, Any]]
    issues: List[Dict[str, Any]]
    summary: Dict[str, Any]
    is_valid: bool

def ingest(state: ValidationState):
    logger.info("[AGENT] INGEST")
    trip = get_trip(state["trip_id"])
    return {"trip_data": trip, "issues": [], "summary": {}}

def validate_places(state: ValidationState):
    logger.info("[AGENT] VALIDATE_PLACES")
    # Mock place validation
    issues = state.get("issues", [])
    trip = state.get("trip_data")
    if not trip: return {}
    for day in trip.get("days", []):
        for stop in day.get("stops", []):
            if stop.get("status") == "CLOSED":
                issues.append({
                    "id": f"issue-place-{stop['id']}",
                    "severity": "CONFLICT",
                    "type": "PLACE_CLOSED",
                    "stop_id": stop['id'],
                    "message": f"{stop['title']} is permanently closed.",
                    "details": "Google Places reports this location as permanently closed.",
                    "suggested_action": "Replace this stop."
                })
    return {"issues": issues}

def validate_hours(state: ValidationState):
    logger.info("[AGENT] VALIDATE_HOURS")
    issues = state.get("issues", [])
    # Add a mock hours warning if we wanted to
    return {"issues": issues}

def validate_routes(state: ValidationState):
    logger.info("[AGENT] VALIDATE_ROUTES")
    issues = state.get("issues", [])
    trip = state.get("trip_data")
    if not trip: return {}
    routes_provider = get_routes_provider()
    
    for day in trip.get("days", []):
        stops = day.get("stops", [])
        for i in range(len(stops) - 1):
            s1 = stops[i]
            s2 = stops[i+1]
            try:
                tt = routes_provider.calculate_travel_time((s1['latitude'], s1['longitude']), (s2['latitude'], s2['longitude']))
                if tt > 60:
                    issues.append({
                        "id": f"issue-route-{s1['id']}",
                        "severity": "WARNING",
                        "type": "TRAVEL_TIME",
                        "stop_id": s1['id'],
                        "message": f"Long travel time to {s2['title']}.",
                        "details": f"Estimated travel time is {tt} minutes.",
                        "suggested_action": "Consider adjusting schedule."
                    })
            except Exception:
                pass
    return {"issues": issues}

def validate_conflicts(state: ValidationState):
    logger.info("[AGENT] VALIDATE_CONFLICTS")
    return {}

def summarize(state: ValidationState):
    logger.info("[AGENT] SUMMARIZE")
    issues = state.get("issues", [])
    has_conflict = any(i['severity'] == 'CONFLICT' for i in issues)
    has_warning = any(i['severity'] == 'WARNING' for i in issues)
    
    summary = {
        "status": "INVALID" if has_conflict else "NEEDS_REVIEW" if has_warning else "VALID",
        "total_issues": len(issues)
    }
    return {"summary": summary, "is_valid": not has_conflict}

workflow = StateGraph(ValidationState)
workflow.add_node("INGEST", ingest)
workflow.add_node("VALIDATE_PLACES", validate_places)
workflow.add_node("VALIDATE_HOURS", validate_hours)
workflow.add_node("VALIDATE_ROUTES", validate_routes)
workflow.add_node("VALIDATE_CONFLICTS", validate_conflicts)
workflow.add_node("SUMMARIZE", summarize)

workflow.add_edge("INGEST", "VALIDATE_PLACES")
workflow.add_edge("VALIDATE_PLACES", "VALIDATE_HOURS")
workflow.add_edge("VALIDATE_HOURS", "VALIDATE_ROUTES")
workflow.add_edge("VALIDATE_ROUTES", "VALIDATE_CONFLICTS")
workflow.add_edge("VALIDATE_CONFLICTS", "SUMMARIZE")
workflow.add_edge("SUMMARIZE", END)
workflow.set_entry_point("INGEST")

val_graph = workflow.compile()
"""
write_file(f"{backend_dir}/workflows/validation_graph.py", validation_graph)

# --- API UPDATE ---
api_path = f"{backend_dir}/api/trips.py"
with open(api_path, 'r', encoding='utf-8') as f:
    api_content = f.read()

if "from app.workflows.validation_graph import val_graph" not in api_content:
    api_content = "from app.workflows.validation_graph import val_graph\n" + api_content
    val_endpoint = """
@router.post("/{trip_id}/validate")
def validate_trip(trip_id: str):
    state = val_graph.invoke({"trip_id": trip_id})
    return {
        "valid": state.get("is_valid", True),
        "issues": state.get("issues", []),
        "validated_stops": state.get("trip_data", {}).get("days", [])[0].get("stops", []) if state.get("trip_data") else [],
        "summary": state.get("summary", {})
    }
"""
    api_content += val_endpoint
    write_file(api_path, api_content)

# --- TESTS ---
test_val = """
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
"""
write_file(f"{tests_dir}/test_validation.py", test_val)
