from pydantic import BaseModel, Field
from typing import List, Optional

class ExtractedStop(BaseModel):
    title: str = Field(description="Title of the activity or stop")
    category: Optional[str] = None
    location_name: Optional[str] = None
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    reservation_info: Optional[str] = None
    confidence: Optional[float] = 1.0

class ExtractedDay(BaseModel):
    date: Optional[str] = None
    stops: List[ExtractedStop] = Field(description="List of stops/activities for this day")

class ExtractedTrip(BaseModel):
    name: str
    destination: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    days: List[ExtractedDay]
