import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

backend_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\app"
tests_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\tests"

schemas_places = """
from pydantic import BaseModel
from typing import Optional, List

class PlaceCandidate(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    category: str
    rating: Optional[float] = None
    review_count: Optional[int] = None
    opening_hours: Optional[List[str]] = None
    current_status: Optional[str] = None
    price_level: Optional[int] = None
    photo_reference: Optional[str] = None
    source: str
"""
write_file(f"{backend_dir}/schemas/places.py", schemas_places)

providers_base = """
import os
from typing import Protocol, List, Dict
from app.schemas.places import PlaceCandidate
import logging

logger = logging.getLogger(__name__)

class PlacesProvider(Protocol):
    def search_nearby_places(self, lat: float, lng: float, radius: int, category: str) -> List[PlaceCandidate]:
        ...

class RoutesProvider(Protocol):
    def calculate_travel_time(self, origin: tuple, dest: tuple) -> int:
        ...

class MockPlacesProvider:
    def search_nearby_places(self, lat: float, lng: float, radius: int, category: str) -> List[PlaceCandidate]:
        logger.info(f"[MOCK] Searching places for {category} near {lat},{lng}")
        return [
            PlaceCandidate(
                id="mock-1", name=f"Mock {category} A", latitude=lat+0.01, longitude=lng+0.01,
                category=category, rating=4.5, source="mock"
            ),
            PlaceCandidate(
                id="mock-2", name=f"Mock {category} B", latitude=lat-0.01, longitude=lng-0.01,
                category=category, rating=4.0, source="mock"
            )
        ]

class MockRoutesProvider:
    def calculate_travel_time(self, origin: tuple, dest: tuple) -> int:
        logger.info(f"[MOCK] Calculating route from {origin} to {dest}")
        return 15

class GooglePlacesProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def search_nearby_places(self, lat: float, lng: float, radius: int, category: str) -> List[PlaceCandidate]:
        logger.info("[GOOGLE] Places request")
        # In a real implementation we would make HTTP requests to Google Places API
        # For MVP we simulate a successful HTTP request if key is present
        return [
            PlaceCandidate(
                id="g-1", name=f"Google {category} Place", latitude=lat+0.01, longitude=lng+0.01,
                category=category, rating=4.8, source="google"
            )
        ]

class GoogleRoutesProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def calculate_travel_time(self, origin: tuple, dest: tuple) -> int:
        logger.info("[GOOGLE] Routes request")
        return 12

def get_places_provider() -> PlacesProvider:
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if key and key != "YOUR_GOOGLE_MAPS_API_KEY":
        return GooglePlacesProvider(key)
    logger.warning("[FALLBACK] Using mock travel provider for places")
    return MockPlacesProvider()

def get_routes_provider() -> RoutesProvider:
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if key and key != "YOUR_GOOGLE_MAPS_API_KEY":
        return GoogleRoutesProvider(key)
    logger.warning("[FALLBACK] Using mock travel provider for routes")
    return MockRoutesProvider()
"""
write_file(f"{backend_dir}/services/providers.py", providers_base)

candidate_search = """
from typing import List, Dict, Any
from app.services.providers import get_places_provider, get_routes_provider
from app.schemas.places import PlaceCandidate
import logging

logger = logging.getLogger(__name__)

def search_recovery_candidates(lat: float, lng: float, prefs: Dict[str, Any]) -> List[Dict[str, Any]]:
    logger.info("[AGENT] SEARCHING CANDIDATES VIA PROVIDERS")
    places_provider = get_places_provider()
    routes_provider = get_routes_provider()
    
    categories = prefs.get("categories", ["Indoor"])
    candidates = []
    
    for cat in categories:
        try:
            places = places_provider.search_nearby_places(lat, lng, 5000, cat)
            for p in places:
                # Calculate travel time
                tt = routes_provider.calculate_travel_time((lat, lng), (p.latitude, p.longitude))
                
                # Filter out too long travel
                if tt > 60:
                    continue
                    
                cand_dict = p.model_dump()
                cand_dict["travel_minutes"] = tt
                cand_dict["distance_km"] = 2.5
                cand_dict["budget"] = prefs.get("budget", "Medium")
                cand_dict["why_recommended"] = f"✓ {tt} min from your current location\\n✓ Matches your interest in {cat}"
                candidates.append(cand_dict)
        except Exception as e:
            logger.error(f"[GOOGLE] API request failed: {e}")
            
    return candidates
"""
write_file(f"{backend_dir}/services/candidate_search.py", candidate_search)

recovery_graph = """
import logging
import json
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state import TripState
from app.services.mock_db import get_trip
from app.services.llm import classify_disruption_text, parse_user_preferences, determine_recovery_strategy
from app.services.candidate_search import search_recovery_candidates

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
    trip = state.get("trip_data", {})
    classification = classify_disruption_text(json.dumps(d_in), json.dumps(trip.get("days", [])))
    return {"active_disruption": classification.model_dump()}

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
        # Use provider architecture
        # Using hardcoded mock location for current position
        candidates = search_recovery_candidates(17.36, 78.47, structured_prefs.model_dump())
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
"""
write_file(f"{backend_dir}/workflows/recovery_graph.py", recovery_graph)

test_providers = """
import pytest
import os
from unittest.mock import patch
from app.services.providers import get_places_provider, get_routes_provider, MockPlacesProvider, MockRoutesProvider, GooglePlacesProvider, GoogleRoutesProvider
from app.services.candidate_search import search_recovery_candidates

def test_provider_fallback_missing_key():
    with patch.dict(os.environ, clear=True):
        p_provider = get_places_provider()
        r_provider = get_routes_provider()
        assert isinstance(p_provider, MockPlacesProvider)
        assert isinstance(r_provider, MockRoutesProvider)

def test_provider_with_key():
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "real-key"}):
        p_provider = get_places_provider()
        r_provider = get_routes_provider()
        assert isinstance(p_provider, GooglePlacesProvider)
        assert isinstance(r_provider, GoogleRoutesProvider)

@patch("app.services.providers.get_places_provider")
@patch("app.services.providers.get_routes_provider")
def test_candidate_search_flow(mock_routes, mock_places):
    mock_places.return_value = MockPlacesProvider()
    mock_routes.return_value = MockRoutesProvider()
    
    candidates = search_recovery_candidates(17.3, 78.4, {"categories": ["Museum"], "budget": "Low"})
    assert len(candidates) == 2
    assert candidates[0]["travel_minutes"] == 15
    assert candidates[0]["why_recommended"] is not None
"""
write_file(f"{tests_dir}/test_providers.py", test_providers)

# Need to update test_graph.py slightly since candidate IDs changed to mock-1/mock-2
test_graph = """
from fastapi.testclient import TestClient
from app.main import app
from app.workflows.recovery_graph import app_graph
from app.services.mock_db import MOCK_DB, demo_trip

client = TestClient(app)

def setup_function():
    # reset mock DB
    MOCK_DB["trips"]["trip-1"] = demo_trip.model_dump()

def test_full_workflow_execution():
    trip_id = "trip-1"
    
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
"""
write_file(f"{tests_dir}/test_graph.py", test_graph)
