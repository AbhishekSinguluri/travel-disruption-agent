from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Disruption(BaseModel):
    id: str
    type: str
    affected_stop_id: str
    reason: str
    severity: str

class RecoveryCandidate(BaseModel):
    id: str
    name: str
    category: str
    description: str
    latitude: float
    longitude: float
    distance_km: float
    travel_minutes: int
    opening_time: str
    closing_time: str
    estimated_duration_minutes: int
    budget: str
    rating: float
    weather_suitable: bool
    next_stop_compatible: bool
    why_recommended: str

class UserPreference(BaseModel):
    categories: List[str]
    budget: str

class ReplanResult(BaseModel):
    success: bool
    conflicts: List[str] = []
    updated_stops: List[Dict[str, Any]] = []
