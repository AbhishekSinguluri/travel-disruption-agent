from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
import json
from app.schemas.monitoring import LocationUpdate
from app.workflows.monitoring_graph import mon_graph
from app.db.repositories import get_trip_repository
import math

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

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000 # radius of earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

@router.post("/{trip_id}/location")
async def update_location(trip_id: str, loc: LocationUpdate):
    repo = get_trip_repository()
    # Try getting the trip
    trip = repo.get_trip(trip_id, "demo-user") # Hack for MVP without token
    action_required = None
    
    if trip:
        # Check proximity to next stop
        next_stop = None
        for d in trip.get("days", []):
            for s in d.get("stops", []):
                if s.get("status") == "UPCOMING":
                    next_stop = s
                    break
            if next_stop: break
            
        if next_stop and next_stop.get("latitude") and next_stop.get("longitude"):
            dist = haversine(loc.latitude, loc.longitude, next_stop["latitude"], next_stop["longitude"])
            if dist < 100: # within 100 meters
                next_stop["status"] = "ARRIVED"
                repo.update_trip(trip_id, trip, "demo-user")
                action_required = "STOP_NEARBY"
                await broadcast_event("stop_nearby", {"stop_id": next_stop["id"], "message": f"You have arrived at {next_stop['title']}."})
    
    await broadcast_event("location_updated", loc.model_dump())
    return {"status": "ok", "action": action_required}

@router.post("/booking/activate")
async def activate_booking_monitor(booking: dict):
    from app.db.repositories import get_booking_repository
    import uuid
    import datetime
    repo = get_booking_repository()
    
    # Store monitor
    monitor_id = str(uuid.uuid4())
    user_id = "demo-user"
    
    # We expect booking to be the summary JSON returned from extract
    monitor_state = {
        "monitor_id": monitor_id,
        "user_id": user_id,
        "provider": booking.get("provider"),
        "service_number": booking.get("flight_number") or booking.get("service_number"),
        "booking_reference": booking.get("booking_reference"),
        "origin": booking.get("departure_location"),
        "destination": booking.get("arrival_location"),
        "travel_date": booking.get("departure_time") or booking.get("travel_date"),
        "baseline_booking": booking,
        "status": "ACTIVE",
        "created_at": datetime.datetime.now().isoformat(),
        "last_checked_at": None,
        "processed_message_ids": []
    }
    
    # Save the monitor state to repo
    if hasattr(repo, "save_monitor"):
        repo.save_monitor(monitor_id, monitor_state)
    elif hasattr(repo, "monitors"):
        repo.monitors[monitor_id] = monitor_state
        
    return {"status": "ACTIVE", "monitor_id": monitor_id, "monitor": monitor_state}
class MonitorSettings(BaseModel):
    enabled: bool
    interval_seconds: int = None

@router.get("/status")
async def get_monitor_status():
    try:
        from app.services.booking_monitor import get_monitor_service
        service = get_monitor_service()
        from app.db.repositories import get_booking_repository
        repo = get_booking_repository()
        
        active_monitors_count = 0
        if hasattr(repo, "monitors"):
            active_monitors_count = sum(1 for m in repo.monitors.values() if m.get("status") == "ACTIVE")
        else:
            from app.services.mock_db import MOCK_DB
            monitors = MOCK_DB.get("monitoring", {})
            active_monitors_count = sum(1 for m in monitors.values() if m.get("status") == "ACTIVE")
            
        return {
            "enabled": service.enabled,
            "interval_seconds": service.interval_seconds,
            "active_monitors": active_monitors_count,
            "last_check_at": service.last_check_at,
            "next_check_at": service.next_check_at,
            "last_check_status": service.last_check_status,
            "last_error": service.last_error
        }
    except Exception as e:
        import logging
        logging.error(f"Error getting monitor status: {e}")
        return {"enabled": False, "active_monitors": 0, "error": str(e)}

@router.post("/settings")
async def set_monitor_settings(settings: MonitorSettings):
    from app.services.booking_monitor import get_monitor_service
    service = get_monitor_service()
    service.configure(enabled=settings.enabled, interval_seconds=settings.interval_seconds)
    return {"status": "ok", "enabled": service.enabled, "interval_seconds": service.interval_seconds}


@router.post("/check/{monitor_id}")
async def check_monitor(monitor_id: str):
    from app.db.repositories import get_booking_repository
    from app.services.gmail_provider import GmailProvider
    from app.services.change_detector import ChangeDetector
    import datetime
    import uuid
    
    repo = get_booking_repository()
    
    monitor = None
    if hasattr(repo, "get_monitor"):
        monitor = repo.get_monitor(monitor_id)
    elif hasattr(repo, "monitors") and monitor_id in repo.monitors:
        monitor = repo.monitors[monitor_id]
        
    if not monitor:
        return {"status": "error", "message": "Monitor not found"}
        
    baseline = monitor.get("baseline_booking", {})
    
    # 2. Build a narrow Gmail search
    operator = monitor.get("provider") or ""
    service_num = monitor.get("service_number") or ""
    booking_ref = monitor.get("booking_reference") or ""
    
    query_parts = ["newer_than:7d"]
    if operator: query_parts.append(f'"{operator}"')
    if service_num: query_parts.append(f'"{service_num}"')
    if booking_ref: query_parts.append(f'"{booking_ref}"')
    
    from app.services.gmail_provider import get_gmail_provider
    gmail = get_gmail_provider("demo-user")
    
    # 3. Search Gmail
    # We will use the search_messages method which already handles both Mock and Real providers
    messages = gmail.search_messages(" ".join(query_parts), days=7)
    
    if messages:
        # Check against processed_message_ids
        processed = monitor.get("processed_message_ids", [])
        
        # Find the first message that hasn't been processed yet
        new_messages = [m for m in messages if m['id'] not in processed]
        
        if new_messages:
            msg_id = new_messages[0]['id']
            full_msg = gmail.get_message(msg_id)
            content = full_msg.get("body", full_msg.get("snippet", ""))
            
            # 5. Compare new email with the stored baseline
            detector = ChangeDetector()
            result = detector.detect_change(baseline, content)
            
            # 6. Determine whether a meaningful booking change occurred
            if result.has_change:
                # create an alert
                alert = {
                    "id": str(uuid.uuid4()),
                    "monitor_id": monitor_id,
                    "user_id": "demo-user",
                    "alert_type": result.change_type,
                    "title": f"{operator} {service_num} - {result.change_type}",
                    "message": f"Updated departure: {result.new_departure}. Reason: {result.reason}",
                    "severity": "HIGH",
                    "source_message_id": msg_id,
                    "created_at": datetime.datetime.now().isoformat(),
                    "read": False,
                    # ENRICHED DETECTED EVENT
                    "provider": operator,
                    "service_number": service_num,
                    "booking_reference": booking_ref,
                    "origin": baseline.get("origin") or baseline.get("departure_location"),
                    "destination": baseline.get("destination") or baseline.get("arrival_location"),
                    "original_departure": result.original_departure or baseline.get("travel_date") or baseline.get("departure_time"),
                    "new_departure": result.new_departure,
                    "original_arrival": result.original_arrival or baseline.get("arrival_time"),
                    "new_arrival": result.new_arrival,
                    "reason": result.reason,
                    "delay_duration": result.delay_duration
                }
                
                # Check for duplicates
                existing_alerts = []
                if hasattr(repo, "alerts"):
                    existing_alerts = repo.alerts
                elif hasattr(repo, "get_alerts"):
                    existing_alerts = repo.get_alerts("demo-user")
                
                if not any(a.get("source_message_id") == msg_id and a.get("alert_type") == result.change_type for a in existing_alerts):
                        
                    # --- INTEGRATION WITH CORE RECOVERY WORKFLOW ---
                    trip_repo = get_trip_repository()
                    trips = trip_repo.list_trips("demo-user") if hasattr(trip_repo, "list_trips") else []
                    if hasattr(trip_repo, "trips") and isinstance(trip_repo.trips, dict):
                        trips = [t for t in trip_repo.trips.values() if t.get("user_id") == "demo-user"]
                    
                    from app.services.booking_matcher import match_booking_to_trip
                    active_trip = match_booking_to_trip(monitor, trips)
                    
                    if active_trip:
                        disruption_payload = {
                            "reason": result.reason,
                            "change_type": result.change_type,
                            "new_departure": result.new_departure,
                            "operator": operator,
                            "service_number": service_num,
                            "booking_reference": booking_ref
                        }
                        
                        from app.workflows.recovery_graph import app_graph as rec_graph
                        try:
                            import logging
                            logging.info(f"Invoking recovery graph for trip {active_trip['id']} due to match")
                            state = rec_graph.invoke({
                                "trip_id": active_trip["id"],
                                "disruption_input": disruption_payload
                            }, config={"configurable": {"thread_id": active_trip["id"]}})
                            
                            impact = state.get("impact_analysis")
                            if impact:
                                # Broadcast event to frontend to trigger recovery UI
                                await broadcast_event("recovery_required", {
                                    "trip_id": active_trip["id"],
                                    "impact": impact,
                                    "disruption": state.get("active_disruption")
                                })
                        except Exception as e:
                            import logging
                            logging.error(f"Failed to invoke recovery graph: {e}")
                    else:
                        import logging
                        logging.info("No definitive trip match found. Broadcasting alert without recovery.")
                    # -----------------------------------------------

                    from app.services.alert_intelligence import process_alert
                    structured_alert = process_alert(alert, active_trip).model_dump()
                    structured_alert["source_message_id"] = msg_id
                    
                    if hasattr(repo, "create_alert"):
                        repo.create_alert(structured_alert)
                    elif hasattr(repo, "alerts"):
                        repo.alerts.append(structured_alert)
                    else:
                        from app.services.mock_db import MOCK_DB
                        if "alerts" not in MOCK_DB: MOCK_DB["alerts"] = []
                        MOCK_DB["alerts"].append(structured_alert)

                    # Mark as processed only after successful completion
                    processed.append(msg_id)
                    monitor["processed_message_ids"] = processed
                    if hasattr(repo, "save_monitor"):
                        repo.save_monitor(monitor_id, monitor)

                    await broadcast_event("booking_alert", structured_alert)
                    return {"status": "change_detected", "alert": structured_alert}
            else:
                # Mark as processed if it's not a change so we don't keep analyzing it
                processed.append(msg_id)
                monitor["processed_message_ids"] = processed
                if hasattr(repo, "save_monitor"):
                    repo.save_monitor(monitor_id, monitor)

                    
    return {"status": "no_change"}
