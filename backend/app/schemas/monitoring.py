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
