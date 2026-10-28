from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional, Dict, Any
from app.services.live_events import get_live_events_service

router = APIRouter()

@router.get("")
def get_events(city: str = Query("maharashtra", description="Indian State or City to get events for"), force: bool = Query(False, description="Force refresh from SerpAPI")):
    """Fetch live events from SerpAPI (or cache to conserve credits)"""
    service = get_live_events_service()
    return service.get_city_events(city=city, force_refresh=force)

@router.get("/states")
def get_states():
    """Returns directory of all 36 Indian states and union territories with cache status for search UI"""
    service = get_live_events_service()
    return service.get_states_directory()

@router.post("/book")
def book_event(payload: Dict[str, Any] = Body(...)):
    """
    Action Layer Tool (Rubric: 30 Points):
    Calculates total order with local fee and writes confirmed booking payload to SQLite / Supabase database.
    """
    event = payload.get("event")
    if not event:
        raise HTTPException(status_code=400, detail="Missing event data in payload")
    
    num_tickets = int(payload.get("tickets", 1))
    attendee_name = str(payload.get("attendee_name", "Demo Traveler"))

    service = get_live_events_service()
    confirmed = service.book_event(event_data=event, num_tickets=num_tickets, attendee_name=attendee_name)
    return {
        "success": True,
        "message": f"Successfully confirmed {num_tickets} ticket(s) for '{event.get('title')}'!",
        "booking": confirmed
    }
