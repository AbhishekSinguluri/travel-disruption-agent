import logging
import math
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Dict, Any, Optional
from app.db.repositories import get_trip_repository
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
    repo = get_trip_repository()
    trip = repo.get_trip(state["trip_id"], "demo-user")
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
        repo = get_trip_repository()
        trip = repo.get_trip(state["trip_id"], "demo-user")
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
