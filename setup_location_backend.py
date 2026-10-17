import os
import re

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

backend_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\app"
tests_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\tests"

# --- SCHEMAS ---
schemas_monitoring = """
from pydantic import BaseModel
from typing import Optional

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    accuracy: float
    timestamp: str

class LocationResponse(BaseModel):
    status: str
    distance_to_stop: Optional[float] = None
    estimated_travel_time: Optional[int] = None
    nearby: bool = False
"""
write_file(f"{backend_dir}/schemas/monitoring.py", schemas_monitoring)

# --- MONITORING GRAPH UPDATE ---
monitoring_graph_content = """
import logging
import math
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Dict, Any, Optional
from app.services.mock_db import get_trip, update_trip
from app.services.providers import get_routes_provider

logger = logging.getLogger(__name__)

ARRIVAL_RADIUS_METERS = 100

def calculate_distance(lat1, lon1, lat2, lon2):
    # Haversine formula
    R = 6371e3
    phi1 = lat1 * math.pi/180
    phi2 = lat2 * math.pi/180
    dphi = (lat2-lat1) * math.pi/180
    dlambda = (lon2-lon1) * math.pi/180
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

class MonitoringState(TypedDict):
    trip_id: str
    simulated_time: str
    current_stop_id: Optional[str]
    current_location: Optional[Dict[str, Any]]
    delay_minutes: int
    weather_alert: Optional[Dict[str, Any]]
    action_required: Optional[str]
    nearby: bool

def check_location(state: MonitoringState):
    logger.info("[MONITOR] CHECK_LOCATION")
    # This node is triggered when location updates
    loc = state.get("current_location")
    if not loc:
        return {}
    return {}

def check_proximity(state: MonitoringState):
    logger.info("[MONITOR] CHECK_PROXIMITY")
    loc = state.get("current_location")
    if not loc:
        return {}
    trip = get_trip(state["trip_id"])
    if not trip: return {}
    
    stop_id = state.get("current_stop_id")
    # find current stop
    target_stop = None
    for day in trip.get("days", []):
        for stop in day.get("stops", []):
            if stop["id"] == stop_id:
                target_stop = stop
                break
                
    if not target_stop:
        return {}
        
    dist = calculate_distance(loc["latitude"], loc["longitude"], target_stop["latitude"], target_stop["longitude"])
    nearby = dist <= ARRIVAL_RADIUS_METERS
    
    action = None
    if nearby and not state.get("nearby"):
        action = "STOP_NEARBY"
        
    return {"nearby": nearby, "action_required": action if action else state.get("action_required")}

def check_timing(state: MonitoringState):
    logger.info("[MONITOR] CHECK_TIMING")
    loc = state.get("current_location")
    delay = state.get("delay_minutes", 0)
    
    # Simple deterministic delay logic
    # If loc is available, estimate travel time
    if loc and state.get("current_stop_id"):
        trip = get_trip(state["trip_id"])
        target_stop = None
        for day in trip.get("days", []):
            for stop in day.get("stops", []):
                if stop["id"] == state["current_stop_id"]:
                    target_stop = stop
                    break
        if target_stop:
            routes = get_routes_provider()
            tt = routes.calculate_travel_time((loc["latitude"], loc["longitude"]), (target_stop["latitude"], target_stop["longitude"]))
            # simplistic delay calculation
            delay = tt
    
    action = state.get("action_required")
    if delay >= 10 and not action:
        action = "USER_DELAY"
    return {"delay_minutes": delay, "action_required": action}

def check_weather(state: MonitoringState):
    logger.info("[MONITOR] CHECK_WEATHER")
    action = state.get("action_required")
    if state.get("weather_alert") and not action:
        return {"action_required": "WEATHER_WARNING"}
    return {}

workflow = StateGraph(MonitoringState)
workflow.add_node("CHECK_LOCATION", check_location)
workflow.add_node("CHECK_PROXIMITY", check_proximity)
workflow.add_node("CHECK_TIMING", check_timing)
workflow.add_node("CHECK_WEATHER", check_weather)

workflow.add_edge("CHECK_LOCATION", "CHECK_PROXIMITY")
workflow.add_edge("CHECK_PROXIMITY", "CHECK_TIMING")
workflow.add_edge("CHECK_TIMING", "CHECK_WEATHER")
workflow.add_edge("CHECK_WEATHER", END)
workflow.set_entry_point("CHECK_LOCATION")
mon_graph = workflow.compile()
"""
write_file(f"{backend_dir}/workflows/monitoring_graph.py", monitoring_graph_content)

# --- API UPDATE ---
api_monitoring_patch = """
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
import json
from app.schemas.monitoring import LocationUpdate
from app.workflows.monitoring_graph import mon_graph

router = APIRouter()

active_connections = []

@router.websocket("/ws/{trip_id}")
async def websocket_endpoint(websocket: WebSocket, trip_id: str):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_event(event_type: str, payload: dict):
    msg = json.dumps({"type": event_type, "payload": payload})
    for connection in active_connections:
        await connection.send_text(msg)

class SimReq(BaseModel):
    event: str
    value: int = 0

@router.post("/{trip_id}/simulate")
async def simulate_event(trip_id: str, req: SimReq):
    if req.event == "start":
        await broadcast_event("trip_started", {})
    elif req.event == "delay":
        await broadcast_event("delay_detected", {"minutes": req.value, "message": f"You're about {req.value} minutes behind schedule."})
    elif req.event == "weather":
        await broadcast_event("weather_warning", {"message": "Heavy rain is expected around your 14:00 outdoor activity."})
    return {"status": "ok"}

@router.post("/{trip_id}/location")
async def update_location(trip_id: str, loc: LocationUpdate):
    # Pass to monitoring graph
    state = mon_graph.invoke({
        "trip_id": trip_id,
        "current_location": loc.model_dump(),
        "current_stop_id": "stop-4", # Mock for MVP
        "simulated_time": "14:00"
    })
    
    await broadcast_event("location_updated", loc.model_dump())
    
    if state.get("action_required") == "STOP_NEARBY":
        await broadcast_event("stop_nearby", {"stop_id": "stop-4", "message": "You're near the current destination."})
    elif state.get("action_required") == "USER_DELAY":
        await broadcast_event("delay_detected", {"minutes": state.get("delay_minutes", 15), "message": "You are falling behind schedule."})
        
    return {"status": "ok", "action": state.get("action_required")}
"""
write_file(f"{backend_dir}/api/monitoring.py", api_monitoring_patch)

# --- TESTS ---
test_location = """
from fastapi.testclient import TestClient
from app.main import app
from app.services.mock_db import MOCK_DB, demo_trip

client = TestClient(app)

def test_location_update():
    MOCK_DB["trips"]["trip-loc"] = demo_trip.model_dump()
    loc = {
        "latitude": 17.3,
        "longitude": 78.4,
        "accuracy": 10.0,
        "timestamp": "2026-10-01T14:00:00Z"
    }
    res = client.post("/api/monitor/trip-loc/location", json=loc)
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
"""
write_file(f"{tests_dir}/test_location.py", test_location)
