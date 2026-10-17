
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class Baggage(BaseModel):
    checked: Optional[str] = None
    cabin: Optional[str] = None

class CanonicalBooking(BaseModel):
    id: Optional[str] = None
    provider: Optional[str] = None
    booking_reference: Optional[str] = None
    service_number: Optional[str] = None
    transport_type: Optional[str] = None
    origin: Optional[str] = None
    origin_code: Optional[str] = None
    destination: Optional[str] = None
    destination_code: Optional[str] = None
    travel_date: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    terminal: Optional[str] = None
    passenger_name: Optional[str] = None
    seat: Optional[str] = None
    class_name: Optional[str] = None # 'class' is reserved
    fare_type: Optional[str] = None
    booking_status: Optional[str] = None
    source: Optional[str] = None
    source_message_id: Optional[str] = None
    confidence: Optional[str] = None
    extracted_at: Optional[datetime] = None
    raw_source_reference: Optional[str] = None
    baggage: Optional[Baggage] = None

class GmailReadIntent(BaseModel):
    intent: str
    provider: Optional[str] = None
    transport_type: Optional[str] = None
    service_number: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    travel_date: Optional[str] = None
    time_window: Optional[str] = None
    status_filter: Optional[str] = None
    requested_summary_type: Optional[str] = None

class BookingSchema(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    booking_type: str # FLIGHT, HOTEL, TRAIN, RESTAURANT
    title: str
    provider: Optional[str] = None
    booking_reference: Optional[str] = None
    flight_number: Optional[str] = None
    departure_location: Optional[str] = None
    arrival_location: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    status: str
    domestic_international: Optional[str] = None
    baggage: Optional[Baggage] = None
    raw_extraction_metadata: Optional[Dict[str, Any]] = None

class BookingEvent(BaseModel):
    id: Optional[str] = None
    booking_id: str
    event_type: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    source_message_id: str
    source_thread_id: Optional[str] = None
    detected_at: Optional[datetime] = None
    confidence: str

class BookingAlert(BaseModel):
    id: Optional[str] = None
    user_id: str
    booking_id: str
    event_id: str
    title: str
    message: str
    severity: str # LOW, MEDIUM, HIGH
    read: bool = False
    created_at: Optional[datetime] = None

class GmailConnection(BaseModel):
    id: Optional[str] = None
    user_id: str
    email: str
    provider: str = "gmail"
    encrypted_token_reference: str
