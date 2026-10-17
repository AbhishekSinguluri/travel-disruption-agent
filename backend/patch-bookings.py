import re
with open('app/api/bookings.py', 'r') as f:
    content = f.read()

# Replace extract_booking signature and body
old_extract = """@router.post("/extract")
async def extract_booking(text: str = None):
    # Mock extraction for Agent 4 MVP
    return {
        "booking_type": "FLIGHT",
        "title": "Air India AI 123",
        "provider": "Air India",
        "booking_reference": "ABC123",
        "flight_number": "AI 123",
        "departure_location": "Hyderabad",
        "arrival_location": "Delhi",
        "departure_time": "09:20",
        "arrival_time": "11:35",
        "status": "Confirmed",
        "domestic_international": "Domestic",
        "baggage": {"checked": "20 kg", "cabin": "7 kg"}
    }"""

new_extract = """from fastapi import UploadFile, File, Form
from typing import Optional

@router.post("/extract")
async def extract_booking(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    # Mock extraction for Agent 4 MVP
    return {
        "booking_type": "FLIGHT",
        "title": "Air India AI 123",
        "provider": "Air India",
        "booking_reference": "ABC123",
        "flight_number": "AI 123",
        "departure_location": "Hyderabad",
        "arrival_location": "Delhi",
        "departure_time": "09:20",
        "arrival_time": "11:35",
        "status": "Confirmed",
        "domestic_international": "Domestic",
        "baggage": {"checked": "20 kg", "cabin": "7 kg"}
    }"""

if old_extract in content:
    content = content.replace(old_extract, new_extract)
else:
    print("Could not find extract_booking!")

with open('app/api/bookings.py', 'w') as f:
    f.write(content)
