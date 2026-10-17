from pydantic import BaseModel
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
