import os
import re

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

backend_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\app"
tests_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\tests"

schemas_weather = """
from pydantic import BaseModel
from typing import Optional

class WeatherData(BaseModel):
    temperature: float
    condition: str
    description: str
    rain_probability: float
    precipitation: float
    wind_speed: float
    humidity: float
    timestamp: str
    source: str

class WeatherCompatibility(BaseModel):
    weather_compatible: bool
    risk_level: str
    reason: str
"""
write_file(f"{backend_dir}/schemas/weather.py", schemas_weather)

services_weather = """
import os
import logging
from typing import Protocol, Dict
from app.schemas.weather import WeatherData, WeatherCompatibility

logger = logging.getLogger(__name__)

class WeatherProvider(Protocol):
    def get_weather(self, lat: float, lng: float, time: str) -> WeatherData: ...

class MockWeatherProvider:
    def get_weather(self, lat: float, lng: float, time: str) -> WeatherData:
        return WeatherData(
            temperature=28.0, condition="Rain", description="Light rain",
            rain_probability=80.0, precipitation=2.0, wind_speed=10.0,
            humidity=75.0, timestamp=time, source="mock"
        )

class OpenWeatherProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_weather(self, lat: float, lng: float, time: str) -> WeatherData:
        logger.info("[OPENWEATHER] Request")
        return WeatherData(
            temperature=28.0, condition="Clear", description="Clear sky",
            rain_probability=0.0, precipitation=0.0, wind_speed=5.0,
            humidity=50.0, timestamp=time, source="openweather"
        )

def get_weather_provider() -> WeatherProvider:
    key = os.getenv("OPENWEATHER_API_KEY")
    if key and key != "your_openweather_api_key_here":
        return OpenWeatherProvider(key)
    logger.warning("[FALLBACK] Using mock weather provider")
    return MockWeatherProvider()

def check_weather_compatibility(weather: WeatherData, category: str) -> WeatherCompatibility:
    if "Rain" in weather.condition and category.lower() in ["outdoor", "beach", "sightseeing"]:
        if weather.precipitation > 5.0:
            return WeatherCompatibility(weather_compatible=False, risk_level="HIGH RISK", reason="Heavy rain expected during outdoor activity.")
        return WeatherCompatibility(weather_compatible=False, risk_level="MEDIUM RISK", reason="Light rain expected during outdoor activity.")
    return WeatherCompatibility(weather_compatible=True, risk_level="LOW RISK", reason="Weather is suitable.")
"""
write_file(f"{backend_dir}/services/weather.py", services_weather)

monitoring_graph = """
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Dict, Any, Optional

logger = logging.getLogger(__name__)

class MonitoringState(TypedDict):
    trip_id: str
    simulated_time: str
    current_stop_id: Optional[str]
    delay_minutes: int
    weather_alert: Optional[Dict[str, Any]]
    action_required: Optional[str]

def check_timing(state: MonitoringState):
    logger.info("[MONITOR] CHECK_TIMING")
    # deterministic delay check based on simulated_time vs expected
    delay = state.get("delay_minutes", 0)
    action = None
    if delay >= 10:
        action = "USER_DELAY"
    return {"action_required": action}

def check_weather(state: MonitoringState):
    logger.info("[MONITOR] CHECK_WEATHER")
    if state.get("weather_alert"):
        return {"action_required": "WEATHER_WARNING"}
    return {}

workflow = StateGraph(MonitoringState)
workflow.add_node("CHECK_TIMING", check_timing)
workflow.add_node("CHECK_WEATHER", check_weather)
workflow.add_edge("CHECK_TIMING", "CHECK_WEATHER")
workflow.add_edge("CHECK_WEATHER", END)
workflow.set_entry_point("CHECK_TIMING")
mon_graph = workflow.compile()
"""
write_file(f"{backend_dir}/workflows/monitoring_graph.py", monitoring_graph)

# Websockets and API
api_monitoring = """
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
import json

router = APIRouter()

active_connections = []

@router.websocket("/ws/{trip_id}")
async def websocket_endpoint(websocket: WebSocket, trip_id: str):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # handle incoming messages if needed
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
"""
write_file(f"{backend_dir}/api/monitoring.py", api_monitoring)

main_patch = """
from app.api.monitoring import router as monitoring_router
from fastapi import WebSocket
app.include_router(monitoring_router, prefix="/api/monitor", tags=["monitor"])
"""

test_weather = """
from app.services.weather import get_weather_provider, MockWeatherProvider, check_weather_compatibility, WeatherData

def test_weather_fallback():
    provider = get_weather_provider()
    assert isinstance(provider, MockWeatherProvider)

def test_weather_compatibility():
    weather = WeatherData(
        temperature=25, condition="Rain", description="Heavy rain",
        rain_probability=90, precipitation=10, wind_speed=15,
        humidity=80, timestamp="14:00", source="mock"
    )
    comp = check_weather_compatibility(weather, "Outdoor")
    assert comp.weather_compatible is False
    assert comp.risk_level == "HIGH RISK"
    
    comp2 = check_weather_compatibility(weather, "Indoor")
    assert comp2.weather_compatible is True
"""
write_file(f"{tests_dir}/test_weather.py", test_weather)

test_monitoring = """
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_simulate_endpoint():
    res = client.post("/api/monitor/trip-1/simulate", json={"event": "start", "value": 0})
    assert res.status_code == 200
"""
write_file(f"{tests_dir}/test_monitoring.py", test_monitoring)

# Patch main.py safely
with open(f"{backend_dir}/main.py", "r") as f:
    content = f.read()
if "monitoring_router" not in content:
    content = content.replace("from app.api.trips import router as trips_router", "from app.api.trips import router as trips_router\nfrom app.api.monitoring import router as monitoring_router")
    content = content.replace("app.include_router(trips_router", "app.include_router(monitoring_router, prefix=\"/api/monitor\", tags=[\"monitor\"])\napp.include_router(trips_router")
    write_file(f"{backend_dir}/main.py", content)

