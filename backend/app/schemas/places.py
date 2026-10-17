from pydantic import BaseModel
from typing import Optional, List, Dict

class PlaceCandidate(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    category: str
    rating: Optional[float] = None
    review_count: Optional[int] = None
    opening_hours: Optional[Dict[str, str]] = None
    current_status: Optional[str] = None
    price_level: Optional[int] = None
    photo_reference: Optional[str] = None
    source: str
