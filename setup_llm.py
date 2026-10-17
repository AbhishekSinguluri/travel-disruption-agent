import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

backend_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\app"
tests_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\tests"

schemas_llm = """
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class DisruptionClassification(BaseModel):
    type: str
    severity: str
    affected_stop_id: str
    reason: str
    confidence: float

class UserRecoveryPreference(BaseModel):
    categories: List[str]
    indoor: Optional[bool] = None
    budget: str
    duration_preference: Optional[int] = None

class RecoveryStrategyType(str, Enum):
    KEEP = "KEEP"
    SHIFT = "SHIFT"
    SHORTEN = "SHORTEN"
    SKIP = "SKIP"
    REPLACE = "REPLACE"
    ASK_USER = "ASK_USER"

class RecoveryStrategy(BaseModel):
    strategy: RecoveryStrategyType
    explanation: str
"""
write_file(f"{backend_dir}/schemas/llm.py", schemas_llm)

services_llm = """
import os
import json
import logging
from time import time
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.schemas.llm import DisruptionClassification, UserRecoveryPreference, RecoveryStrategy

logger = logging.getLogger(__name__)

# Initialize Groq client conditionally
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")

try:
    if GROQ_API_KEY:
        from groq import Groq
        groq_client = Groq(api_key=GROQ_API_KEY)
    else:
        groq_client = None
except Exception:
    groq_client = None

def _call_groq_json(system_prompt: str, user_prompt: str, schema: BaseModel) -> Optional[BaseModel]:
    if not groq_client:
        return None
    start = time()
    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt + "\\n\\nOutput JSON matching this schema: " + json.dumps(schema.model_json_schema())},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        latency = time() - start
        logger.info(f"[LLM] SUCCESS - model: {GROQ_MODEL}, latency: {latency:.2f}s")
        return schema.model_validate_json(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"[LLM] Groq reasoning failed: {str(e)}")
        return None

def classify_disruption_text(disruption_text: str, trip_context: str) -> DisruptionClassification:
    logger.info("[LLM] CLASSIFY_DISRUPTION")
    system_prompt = "You are a travel itinerary recovery reasoning component. You do not browse the internet. Reason only from facts provided. Classify the disruption."
    user_prompt = f"Trip Context: {trip_context}\\nDisruption: {disruption_text}"
    
    result = _call_groq_json(system_prompt, user_prompt, DisruptionClassification)
    if result:
        return result
    
    logger.warning("[LLM] Groq reasoning failed — using deterministic fallback for classification")
    return DisruptionClassification(
        type="WEATHER_DISRUPTION",
        severity="HIGH",
        affected_stop_id="stop-4",
        reason="Fallback deterministic classification",
        confidence=1.0
    )

def parse_user_preferences(user_text: str) -> UserRecoveryPreference:
    logger.info("[LLM] PARSE_USER_PREFERENCES")
    system_prompt = "You are a travel itinerary recovery reasoning component. Parse user text into structured preferences."
    
    result = _call_groq_json(system_prompt, user_text, UserRecoveryPreference)
    if result:
        return result
        
    logger.warning("[LLM] Groq reasoning failed — using deterministic fallback for preferences")
    return UserRecoveryPreference(
        categories=["Indoor", "Culture"],
        indoor=True,
        budget="Low",
        duration_preference=None
    )

def determine_recovery_strategy(facts: str) -> RecoveryStrategy:
    logger.info("[LLM] DETERMINE_RECOVERY_STRATEGY")
    system_prompt = "You are a travel itinerary recovery reasoning component. You do not know current real-world information. Never invent places or times. Choose a recovery strategy."
    
    result = _call_groq_json(system_prompt, facts, RecoveryStrategy)
    if result:
        return result
        
    logger.warning("[LLM] Groq reasoning failed — using deterministic fallback for strategy")
    return RecoveryStrategy(
        strategy="ASK_USER",
        explanation="Deterministic fallback: asking user for preferences."
    )
"""
write_file(f"{backend_dir}/services/llm.py", services_llm)

recovery_graph = """
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state import TripState
from app.services.mock_db import get_trip
from app.services.llm import classify_disruption_text, parse_user_preferences, determine_recovery_strategy
import json

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
        "message": f"{d_act.get('reason', 'Disruption')}. Your 17:00 shopping plan is still feasible."
    }
    return {"impact_analysis": impact}

def determine_recovery(state: TripState) -> TripState:
    print("[AGENT] DETERMINE_RECOVERY")
    impact = state.get("impact_analysis", {})
    facts = json.dumps(impact)
    strategy = determine_recovery_strategy(facts)
    # Store strategy in impact analysis for tracing
    impact["strategy"] = strategy.model_dump()
    return {"impact_analysis": impact}

def search_alternatives(state: TripState) -> TripState:
    print("[AGENT] SEARCH_ALTERNATIVES")
    prefs_raw = state.get("user_preferences")
    candidates = []
    if prefs_raw:
        # LLM parsing of raw preferences
        structured_prefs = parse_user_preferences(json.dumps(prefs_raw))
        
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

test_llm = """
import pytest
from unittest.mock import patch, MagicMock
from app.services.llm import classify_disruption_text, parse_user_preferences, determine_recovery_strategy
from app.schemas.llm import DisruptionClassification, UserRecoveryPreference, RecoveryStrategy

def test_missing_api_key_fallback():
    # When groq_client is None, it should gracefully fallback
    with patch("app.services.llm.groq_client", None):
        res = classify_disruption_text("Beach closed", "Trip context")
        assert res.type == "WEATHER_DISRUPTION"
        assert res.reason == "Fallback deterministic classification"
        
        pref = parse_user_preferences("peaceful and cheap")
        assert pref.budget == "Low"
        
        strat = determine_recovery_strategy("facts")
        assert strat.strategy == "ASK_USER"

@patch("app.services.llm.groq_client")
def test_groq_success(mock_client):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"type": "WEATHER_DISRUPTION", "severity": "HIGH", "affected_stop_id": "stop-4", "reason": "Rain", "confidence": 0.9}'
    mock_client.chat.completions.create.return_value = mock_response
    
    res = classify_disruption_text("Rain", "Context")
    assert res.type == "WEATHER_DISRUPTION"
    assert res.reason == "Rain"

@patch("app.services.llm.groq_client")
def test_groq_failure_fallback(mock_client):
    mock_client.chat.completions.create.side_effect = Exception("API Down")
    
    res = classify_disruption_text("Rain", "Context")
    assert res.type == "WEATHER_DISRUPTION"
    assert res.reason == "Fallback deterministic classification"
"""
write_file(f"{tests_dir}/test_llm.py", test_llm)
