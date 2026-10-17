import logging
import json
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, List, Dict, Any, Optional
from app.db.repositories import get_trip_repository
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
    repo = get_trip_repository()
    trip = repo.get_trip(state["trip_id"], 'demo-user')
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
