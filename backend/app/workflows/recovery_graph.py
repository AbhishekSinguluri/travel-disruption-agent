import logging
import json
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state import TripState
from app.db.repositories import get_trip_repository
from app.services.llm import classify_disruption_text, parse_user_preferences, determine_recovery_strategy
from app.services.candidate_search import search_recovery_candidates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_disruption(state: TripState) -> TripState:
    print("[AGENT] DETECT_DISRUPTION")
    trip_id = state.get("trip_id")
    repo = get_trip_repository()
    trip = repo.get_trip(trip_id, 'demo-user')
    return {"trip_data": trip}

def classify_disruption(state: TripState) -> TripState:
    print("[AGENT] CLASSIFY_DISRUPTION")
    d_in = state.get("disruption_input", {})
    trip = state.get("trip_data", {})
    classification = classify_disruption_text(json.dumps(d_in), json.dumps(trip.get("days", [])))
    cls_dump = classification.model_dump()
    if d_in.get("affected_stop_id"):
        cls_dump["affected_stop_id"] = d_in["affected_stop_id"]
    return {"active_disruption": cls_dump, "candidate_alternatives": []}

def assess_impact(state: TripState) -> TripState:
    print("[AGENT] ASSESS_IMPACT")
    d_act = state.get("active_disruption", {})
    impact = {
        "affected_stop_id": d_act.get("affected_stop_id"),
        "message": f"{d_act.get('reason', 'Disruption')}. Your next plans are feasible."
    }
    return {"impact_analysis": impact}

def determine_recovery(state: TripState) -> TripState:
    print("[AGENT] DETERMINE_RECOVERY")
    impact = state.get("impact_analysis", {})
    strategy = determine_recovery_strategy(json.dumps(impact))
    impact["strategy"] = strategy.model_dump()
    return {"impact_analysis": impact}

def search_alternatives(state: TripState) -> TripState:
    print("[AGENT] SEARCH_ALTERNATIVES")
    prefs_raw = state.get("user_preferences")
    candidates = []
    if prefs_raw:
        structured_prefs = parse_user_preferences(json.dumps(prefs_raw))
        
        trip = state.get("trip_data")
        affected_stop_id = state.get("active_disruption", {}).get("affected_stop_id")
        
        lat, lng = 17.36, 78.47
        if trip and affected_stop_id:
            for day in trip.get("days", []):
                for stop in day.get("stops", []):
                    if stop.get("id") == affected_stop_id:
                        if stop.get("latitude") and stop.get("longitude"):
                            lat, lng = stop["latitude"], stop["longitude"]
                            
        # Use provider architecture
        disruption_type = state.get("active_disruption", {}).get("type", "NORMAL_DELAY")
        candidates = search_recovery_candidates(lat, lng, structured_prefs.model_dump(), disruption_type)
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
                if 'latitude' in cand and cand['latitude']:
                    s['latitude'] = cand['latitude']
                if 'longitude' in cand and cand['longitude']:
                    s['longitude'] = cand['longitude']
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
    return {"trip_data": trip}

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

memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory, interrupt_before=["WAIT_FOR_USER_SELECTION"])
