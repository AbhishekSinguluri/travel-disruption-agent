from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class BookingExtractionRequest(BaseModel):
    text: Optional[str] = None
    type: str # "pasted_text", "pdf", "image"

class BookingSummary(BaseModel):
    booking_type: str
    title: str
    provider: Optional[str]
    booking_reference: Optional[str]
    flight_number: Optional[str]
    departure_location: Optional[str]
    arrival_location: Optional[str]
    departure_time: Optional[str]
    arrival_time: Optional[str]
    status: Optional[str]
    baggage: Optional[str]
    
class GmailConnectionReq(BaseModel):
    auth_code: str
