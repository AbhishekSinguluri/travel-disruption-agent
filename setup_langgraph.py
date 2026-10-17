import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

backend_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\app"
tests_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\tests"

# --- AGENT STATE ---
agent_state = """
from typing import TypedDict, List, Optional, Dict, Any

class TripState(TypedDict):
    trip_id: str
    trip_data: Optional[Dict[str, Any]]
    disruption_input: Optional[Dict[str, Any]]
    active_disruption: Optional[Dict[str, Any]]
    impact_analysis: Optional[Dict[str, Any]]
    user_preferences: Optional[Dict[str, Any]]
    candidate_alternatives: List[Dict[str, Any]]
    selected_candidate_id: Optional[str]
    revised_itinerary: Optional[List[Dict[str, Any]]]
    validation_errors: List[str]
"""
write_file(f"{backend_dir}/agents/state.py", agent_state)

# --- RECOVERY GRAPH ---
recovery_graph = """
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state import TripState
from app.services.mock_db import get_trip
from app.schemas.disruption import RecoveryCandidate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_disruption(state: TripState) -> TripState:
    print("[AGENT] DETECT_DISRUPTION")
    trip_id = state.get("trip_id")
    trip = get_trip(trip_id)
    return {"trip_data": trip}

def classify_disruption(state: TripState) -> TripState:
    print("[AGENT] CLASSIFY_DISRUPTION")
    d_in = state.get("disruption_input", {})
    return {"active_disruption": d_in}

def assess_impact(state: TripState) -> TripState:
    print("[AGENT] ASSESS_IMPACT")
    d_act = state.get("active_disruption", {})
    impact = {
        "affected_stop_id": d_act.get("affected_stop_id"),
        "message": "Beach visit is unavailable because of heavy rain. Your 17:00 shopping plan is still feasible."
    }
    return {"impact_analysis": impact}

def determine_recovery(state: TripState) -> TripState:
    print("[AGENT] DETERMINE_RECOVERY")
    return {} # Determine what parameters we need

def search_alternatives(state: TripState) -> TripState:
    print("[AGENT] SEARCH_ALTERNATIVES")
    prefs = state.get("user_preferences")
    candidates = []
    if prefs:
        candidates = [
            {
                "id": "cand-1", "name": "Salar Jung Museum", "category": "Indoor", "description": "Famous art museum",
                "latitude": 17.37, "longitude": 78.48, "distance_km": 2.5, "travel_minutes": 15,
                "opening_time": "10:00", "closing_time": "17:00", "estimated_duration_minutes": 120,
                "budget": "Low", "rating": 4.8, "weather_suitable": True, "next_stop_compatible": True,
                "why_recommended": "Indoor activity, fits your time window perfectly."
            },
            {
                "id": "cand-2", "name": "Indoor Art Gallery", "category": "Culture", "description": "Local contemporary art",
                "latitude": 17.38, "longitude": 78.47, "distance_km": 3.0, "travel_minutes": 20,
                "opening_time": "11:00", "closing_time": "18:00", "estimated_duration_minutes": 90,
                "budget": "Medium", "rating": 4.5, "weather_suitable": True, "next_stop_compatible": True,
                "why_recommended": "Close to your next shopping location."
            }
        ]
    return {"candidate_alternatives": candidates}

def validate_alternatives(state: TripState) -> TripState:
    print("[AGENT] VALIDATE_ALTERNATIVES")
    return {}

def wait_for_user_selection(state: TripState) -> TripState:
    print("[AGENT] WAIT_FOR_USER_SELECTION")
    return {}

def replan(state: TripState) -> TripState:
    print("[AGENT] REPLAN")
    trip = state["trip_data"]
    stop_id = state["active_disruption"]["affected_stop_id"]
    cand_id = state.get("selected_candidate_id")
    cands = state.get("candidate_alternatives", [])
    
    cand = next((c for c in cands if c['id'] == cand_id), None)
    if not cand:
        return {"validation_errors": ["Candidate not found"]}
        
    updated_days = []
    for day in trip['days']:
        new_stops = []
        for stop in day['stops']:
            s = dict(stop)
            if s['id'] == stop_id:
                s['title'] = cand['name']
                s['category'] = cand['category']
                s['location_name'] = cand['name']
                s['status'] = "REPLACED"
                s['notes'] = "Replaced due to disruption."
            new_stops.append(s)
        d = dict(day)
        d['stops'] = new_stops
        updated_days.append(d)
        
    return {"revised_itinerary": updated_days, "validation_errors": []}

def validate_replan(state: TripState) -> TripState:
    print("[AGENT] VALIDATE_REPLAN")
    return {}

def update_state(state: TripState) -> TripState:
    print("[AGENT] UPDATE_STATE")
    from app.services.mock_db import update_trip
    trip = state["trip_data"]
    trip['days'] = state["revised_itinerary"]
    update_trip(state["trip_id"], trip)
    return {}

workflow = StateGraph(TripState)

workflow.add_node("DETECT_DISRUPTION", detect_disruption)
workflow.add_node("CLASSIFY_DISRUPTION", classify_disruption)
workflow.add_node("ASSESS_IMPACT", assess_impact)
workflow.add_node("DETERMINE_RECOVERY", determine_recovery)
workflow.add_node("SEARCH_ALTERNATIVES", search_alternatives)
workflow.add_node("VALIDATE_ALTERNATIVES", validate_alternatives)
workflow.add_node("WAIT_FOR_USER_SELECTION", wait_for_user_selection)
workflow.add_node("REPLAN", replan)
workflow.add_node("VALIDATE_REPLAN", validate_replan)
workflow.add_node("UPDATE_STATE", update_state)

workflow.add_edge("DETECT_DISRUPTION", "CLASSIFY_DISRUPTION")
workflow.add_edge("CLASSIFY_DISRUPTION", "ASSESS_IMPACT")
workflow.add_edge("ASSESS_IMPACT", "DETERMINE_RECOVERY")
workflow.add_edge("DETERMINE_RECOVERY", "WAIT_FOR_USER_SELECTION")

# Define edges from wait_for_user_selection based on what is available
def route_from_wait(state: TripState):
    if state.get("selected_candidate_id"):
        return "REPLAN"
    if state.get("user_preferences"):
        return "SEARCH_ALTERNATIVES"
    return END

workflow.add_conditional_edges("WAIT_FOR_USER_SELECTION", route_from_wait)

workflow.add_edge("SEARCH_ALTERNATIVES", "VALIDATE_ALTERNATIVES")
workflow.add_edge("VALIDATE_ALTERNATIVES", "WAIT_FOR_USER_SELECTION")

workflow.add_edge("REPLAN", "VALIDATE_REPLAN")
workflow.add_edge("VALIDATE_REPLAN", "UPDATE_STATE")
workflow.add_edge("UPDATE_STATE", END)

workflow.set_entry_point("DETECT_DISRUPTION")

# Add memory
memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory, interrupt_before=["WAIT_FOR_USER_SELECTION"])
"""
write_file(f"{backend_dir}/workflows/recovery_graph.py", recovery_graph)

# --- UPDATE API TRIPS ---
api_trips = """
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
from app.services.mock_db import get_trip, MOCK_DB
from app.workflows.recovery_graph import app_graph

router = APIRouter()

@router.get("/demo")
def get_demo_trip():
    return get_trip("trip-1")

class DisruptionReq(BaseModel):
    type: str
    affected_stop_id: str

@router.post("/{trip_id}/simulate-disruption")
def simulate_disruption(trip_id: str, req: DisruptionReq):
    thread = {"configurable": {"thread_id": trip_id}}
    state_update = {
        "trip_id": trip_id,
        "disruption_input": req.model_dump()
    }
    for event in app_graph.stream(state_update, config=thread):
        pass
    
    current_state = app_graph.get_state(thread).values
    return {"impact": current_state.get("impact_analysis")}

class PrefReq(BaseModel):
    categories: List[str]
    budget: str

@router.post("/{trip_id}/recovery/preferences")
def submit_preferences(trip_id: str, req: PrefReq):
    thread = {"configurable": {"thread_id": trip_id}}
    state_update = {
        "user_preferences": req.model_dump()
    }
    app_graph.update_state(thread, state_update, as_node="WAIT_FOR_USER_SELECTION")
    
    for event in app_graph.stream(None, config=thread):
        pass
        
    current_state = app_graph.get_state(thread).values
    return {"candidates": current_state.get("candidate_alternatives", [])}

class SelectReq(BaseModel):
    candidate_id: str

@router.post("/{trip_id}/recovery/select")
def select_candidate(trip_id: str, req: SelectReq):
    thread = {"configurable": {"thread_id": trip_id}}
    state_update = {
        "selected_candidate_id": req.candidate_id
    }
    app_graph.update_state(thread, state_update, as_node="WAIT_FOR_USER_SELECTION")
    
    for event in app_graph.stream(None, config=thread):
        pass
        
    current_state = app_graph.get_state(thread).values
    trip_data = current_state.get("trip_data")
    updated_stops = trip_data["days"][0]["stops"]
    
    return {"success": True, "conflicts": [], "updated_stops": updated_stops}
"""
write_file(f"{backend_dir}/api/trips.py", api_trips)

# --- TESTS ---
test_graph = """
from fastapi.testclient import TestClient
from app.main import app
from app.workflows.recovery_graph import app_graph
from app.services.mock_db import MOCK_DB, demo_trip

client = TestClient(app)

def setup_function():
    # reset mock DB
    MOCK_DB["trips"]["trip-1"] = demo_trip.model_dump()

def test_graph_construction():
    assert app_graph is not None

def test_full_workflow_execution():
    trip_id = "trip-1"
    
    # 1. Simulate disruption
    req = {"type": "WEATHER_DISRUPTION", "affected_stop_id": "stop-4"}
    res = client.post(f"/api/trips/{trip_id}/simulate-disruption", json=req)
    assert res.status_code == 200
    assert res.json()["impact"]["affected_stop_id"] == "stop-4"
    
    # 2. Preferences
    pref_req = {"categories": ["Indoor"], "budget": "Low"}
    res = client.post(f"/api/trips/{trip_id}/recovery/preferences", json=pref_req)
    assert res.status_code == 200
    assert len(res.json()["candidates"]) == 2
    
    # 3. Select candidate
    select_req = {"candidate_id": "cand-1"}
    res = client.post(f"/api/trips/{trip_id}/recovery/select", json=select_req)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] == True
    
    # Verify replan behavior
    updated_stops = data["updated_stops"]
    replaced_stop = next(s for s in updated_stops if s["id"] == "stop-4")
    assert replaced_stop["status"] == "REPLACED"
    assert replaced_stop["title"] == "Salar Jung Museum"
    
    # Unaffected stop unchanged
    shopping = next(s for s in updated_stops if s["id"] == "stop-5")
    assert shopping["status"] == "PLANNED"
    assert shopping["title"] == "Shopping"
"""
write_file(f"{tests_dir}/test_graph.py", test_graph)
