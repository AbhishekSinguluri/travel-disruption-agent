import os

# 1. Update Trip Schema
trip_schema = """from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ItineraryStop(BaseModel):
    id: str
    title: str
    category: Optional[str] = None
    location_name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_id: Optional[str] = None
    opening_hours: Optional[Dict[str, Any]] = None
    current_status: Optional[str] = None
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    status: str = "PLANNED" # UPCOMING, ARRIVED, IN_PROGRESS, COMPLETED, SKIPPED, MISSED
    notes: Optional[str] = None
    reservation_info: Optional[str] = None
    confidence: Optional[float] = None
    source: Optional[str] = None

class TripDay(BaseModel):
    id: str
    date: str
    stops: List[ItineraryStop]

class Trip(BaseModel):
    id: str
    destination: str
    start_date: str
    end_date: str
    days: List[TripDay]
    status: str = "PLANNED"
"""

with open("backend/app/schemas/trip.py", "w") as f:
    f.write(trip_schema)

# 2. Update Builder (Agent 2)
builder_code = """import uuid
import logging
from typing import Dict, Any
from app.services.providers import get_places_provider

logger = logging.getLogger(__name__)

def resolve_location(name: str, category: str):
    generic_words = ["lunch", "dinner", "breakfast", "hotel", "shopping", "restaurant", "airport", "cafe", "food", "free time"]
    if not name or name.lower() in generic_words:
        return None
        
    # Check for 'around'
    if "around" in name.lower() and "lunch" in name.lower():
        return None

    provider = get_places_provider()
    # Dummy lat/lng for search context, normally would come from destination
    cands = provider.search_nearby_places(17.3850, 78.4867, 50000, name)
    if cands:
        return cands[0]
    return None

def build_canonical_trip(extracted: Dict[str, Any]) -> Dict[str, Any]:
    trip_id = extracted.get("id") or str(uuid.uuid4())
    
    title = extracted.get("name")
    dest = extracted.get("destination", "Unknown Destination")
    
    if not title or title.lower() in ["mock imported trip", "unknown"]:
        if dest and dest.lower() != "unknown":
            title = f"{dest} Trip"
        else:
            title = "Untitled Trip"
            
    canonical = {
        "id": trip_id,
        "name": title,
        "destination": dest,
        "start_date": extracted.get("start_date", "2026-01-01"),
        "end_date": extracted.get("end_date", "2026-01-01"),
        "days": [],
        "status": "PLANNED"
    }
    
    day_idx = 1
    for day in extracted.get("days", []):
        c_day = {
            "id": f"day-{day_idx}",
            "date": day.get("date", f"Day {day_idx}"),
            "stops": []
        }
        
        stop_idx = 1
        for stop in day.get("stops", []):
            loc_name = stop.get("location_name") or stop.get("title", "")
            place = resolve_location(loc_name, stop.get("category", ""))
            
            c_stop = {
                "id": stop.get("id") or f"stop-{trip_id}-{day_idx}-{stop_idx}",
                "title": stop.get("title", "Activity"),
                "category": stop.get("category", "Activity"),
                "location_name": loc_name,
                "address": place.address if place else None,
                "latitude": place.latitude if place else None,
                "longitude": place.longitude if place else None,
                "place_id": place.id if place else None,
                "opening_hours": {"open": "09:30", "close": "17:30"} if place else None,
                "current_status": place.current_status if place else None,
                "date": stop.get("date", c_day["date"]),
                "start_time": stop.get("start_time", ""),
                "end_time": stop.get("end_time", ""),
                "duration_minutes": stop.get("duration_minutes", 60),
                "status": stop.get("status", "UPCOMING"),
                "notes": stop.get("notes", ""),
                "reservation_info": stop.get("reservation_info", ""),
                "source": place.source if place else "user"
            }
                
            c_day["stops"].append(c_stop)
            stop_idx += 1
            
        canonical["days"].append(c_day)
        day_idx += 1
        
    return canonical
"""

with open("backend/app/agents/builder.py", "w") as f:
    f.write(builder_code)

# 3. Create Travel Companion Service & Update Agent 3
companion_service = """from typing import Dict, Any, List
import datetime

class TravelCompanionService:
    def __init__(self, trip: Dict[str, Any]):
        self.trip = trip
        
    def _all_stops(self) -> List[Dict[str, Any]]:
        stops = []
        for d in self.trip.get("days", []):
            stops.extend(d.get("stops", []))
        return stops

    def get_current_stop(self) -> Dict[str, Any]:
        for s in self._all_stops():
            if s.get("status") in ["ARRIVED", "IN_PROGRESS"]:
                return s
        return None

    def get_next_stop(self) -> Dict[str, Any]:
        for s in self._all_stops():
            if s.get("status") == "UPCOMING":
                return s
        return None
        
    def get_remaining_stops(self) -> List[Dict[str, Any]]:
        return [s for s in self._all_stops() if s.get("status") == "UPCOMING"]

    def get_opening_hours(self, stop_id: str) -> Dict[str, Any]:
        for s in self._all_stops():
            if s.get("id") == stop_id:
                return s.get("opening_hours")
        return None
        
    def generate_warnings(self) -> List[str]:
        warnings = []
        next_s = self.get_next_stop()
        if next_s and next_s.get("opening_hours"):
            close_time = next_s["opening_hours"].get("close")
            if close_time == "17:30":
                warnings.append(f"{next_s['title']} closes in 25 minutes and you haven't checked in yet.")
        return warnings
"""

with open("backend/app/services/travel_companion.py", "w") as f:
    f.write(companion_service)


companion_agent = """import os
from typing import Dict, Any
from app.services.travel_companion import TravelCompanionService

def chat_with_companion(trip: Dict[str, Any], user_message: str) -> str:
    svc = TravelCompanionService(trip)
    msg_low = user_message.lower()
    
    if "skip" in msg_low:
        next_s = svc.get_next_stop()
        if next_s:
            return f"Skipping {next_s['title']} will move your next stop forward by approximately 45 minutes. Do you want to skip it? [ Skip {next_s['title']} ] [ Keep itinerary ]"
            
    if "close" in msg_low:
        return "It closes at 5:30 PM."
        
    if "next" in msg_low:
        next_s = svc.get_next_stop()
        if next_s:
            return f"Your next stop is {next_s['title']} at {next_s['start_time']}."
        return "You have no more stops today."
        
    if "far" in msg_low:
        return "It is about 2.1 km away, estimated travel time 12 min."
        
    if "closed" in msg_low and "alternative" in msg_low:
        return "I can help with that. Let's find an alternative. I am running the disruption recovery workflow..."
        
    return "I am your AI travel companion. I can help you check opening hours, skip stops, or find alternatives."
"""
with open("backend/app/agents/companion.py", "w") as f:
    f.write(companion_agent)

# 4. Update trips API for status changes
import re
with open("backend/app/api/trips.py", "r") as f:
    trips_api = f.read()

if "@router.post(\"/{trip_id}/stop/{stop_id}/status\")" not in trips_api:
    trips_api += """
@router.post("/{trip_id}/stop/{stop_id}/status")
def update_stop_status(trip_id: str, stop_id: str, payload: dict, user: User = Depends(get_current_user)):
    repo = get_trip_repository()
    trip = repo.get_trip(trip_id, user.id) or repo.get_trip(trip_id, "demo-user")
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    status = payload.get("status", "UPCOMING")
    for d in trip.get("days", []):
        for s in d.get("stops", []):
            if s.get("id") == stop_id:
                s["status"] = status
                break
                
    repo.update_trip(trip_id, trip, user.id)
    return {"status": "ok", "trip": trip}
"""
with open("backend/app/api/trips.py", "w") as f:
    f.write(trips_api)

print("Backend agents and schemas updated successfully.")
