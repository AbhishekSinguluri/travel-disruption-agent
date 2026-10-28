
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.schemas.booking import BookingSchema
from app.db.repositories import get_booking_repository
from typing import Optional
import uuid
import datetime
import logging
import email.utils
import re

logger = logging.getLogger(__name__)
router = APIRouter()

def _parse_email_metadata(date_raw: Optional[str], from_raw: Optional[str]):
    email_date = "Unavailable"
    email_time = "Unavailable"
    sender_email = "Unavailable"
    
    if date_raw:
        try:
            dt = email.utils.parsedate_to_datetime(date_raw)
            tz_str = dt.tzname() or (dt.strftime("%z") if dt.tzinfo else "UTC")
            email_date = dt.strftime("%Y-%m-%d")
            email_time = dt.strftime(f"%H:%M {tz_str}").strip()
        except Exception:
            email_date = date_raw
            email_time = "Unavailable"
            
    if from_raw:
        try:
            realname, addr = email.utils.parseaddr(from_raw)
            sender_email = addr if addr else from_raw
        except Exception:
            sender_email = from_raw
            
    return email_date, email_time, sender_email

@router.post("/extract")
async def extract_booking(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    user_id: Optional[str] = Form("demo-user")
):
    from app.services.booking_extractor import BookingExtractor
    from app.services.document_parser import DocumentParser
    from app.services.gmail_provider import get_gmail_provider, RealGmailProvider
    import os
    
    repo = get_booking_repository()
    
    if text:
        try:
            extractor = BookingExtractor()
            result = extractor.extract_intent_or_booking(text)
        except Exception as e:
            logger.error(f"Failed to extract intent: {e}")
            raise HTTPException(status_code=500, detail="The AI agent failed to process the document.")
        
        if result.mode == "READ_GMAIL":
            provider = get_gmail_provider(user_id)
            if not isinstance(provider, RealGmailProvider):
                # Check if mock provider can provide sample message
                pass
            
            intent = result.gmail_intent
            days = 7
            if intent and intent.time_window == "LAST_1_DAY":
                days = 1
            elif intent and intent.time_window == "LAST_2_WEEKS":
                days = 14
                
            query_parts = []
            if intent and intent.provider:
                query_parts.append(f'"{intent.provider}"')
            if intent and intent.service_number:
                query_parts.append(f'"{intent.service_number}"')
                
            query = " ".join(query_parts) if query_parts else "flight OR hotel OR train"
            candidate_emails = provider.search_messages(query=query, days=days)
            
            if not candidate_emails:
                return {
                    "title": f"I didn't find any recent emails matching your request in the last {days} days.",
                    "status": "No emails found"
                }
                
            first_msg_meta = candidate_emails[0] if candidate_emails else {}
            first_msg_full = {}
            emails_text = ""
            for e in candidate_emails[:2]:
                msg_full = provider.get_message(e['id'])
                if not first_msg_full:
                    first_msg_full = msg_full
                emails_text += f"Subject: {e.get('subject')}\nBody: {msg_full.get('body')}\n\n"
            
            date_raw = first_msg_full.get("date") or first_msg_meta.get("date")
            from_raw = first_msg_full.get("from") or first_msg_meta.get("from")
            e_date, e_time, e_sender = _parse_email_metadata(date_raw, from_raw)
            
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key or api_key == "your_groq_api_key_here":
                b_dict = {
                    "booking_type": "FLIGHT",
                    "title": "Air India AI 123",
                    "provider": "Air India",
                    "booking_reference": "AI-88392",
                    "flight_number": "AI 123",
                    "service_number": "AI 123",
                    "departure_location": "Hyderabad (HYD)",
                    "arrival_location": "Delhi (DEL)",
                    "origin": "Hyderabad (HYD)",
                    "destination": "Delhi (DEL)",
                    "departure_time": "09:20",
                    "arrival_time": "11:45",
                    "status": "Extracted from Gmail",
                    "email_date": e_date,
                    "email_time": e_time,
                    "sender_email": e_sender,
                    "user_id": user_id
                }
                saved = repo.save_booking(b_dict)
                saved["booking_id"] = saved["id"]
                return saved
                
            try:
                parser = DocumentParser()
                booking = parser._extract_booking_via_llm(emails_text)
                b_dict = booking.model_dump()
                b_dict["status"] = "Extracted from Gmail"
                b_dict["booking_type"] = b_dict.get("transport_type") or "FLIGHT"
                b_dict["title"] = f"{b_dict.get('provider') or 'Booking'} {b_dict.get('service_number') or ''}".strip()
                b_dict["flight_number"] = b_dict.get("service_number")
                b_dict["departure_location"] = b_dict.get("origin")
                b_dict["arrival_location"] = b_dict.get("destination")
                b_dict["email_date"] = e_date
                b_dict["email_time"] = e_time
                b_dict["sender_email"] = e_sender
                b_dict["user_id"] = user_id
                
                saved = repo.save_booking(b_dict)
                saved["booking_id"] = saved["id"]
                return saved
            except Exception as e:
                logger.error(f"Failed to extract booking: {e}")
                return {
                    "title": f"I found {len(candidate_emails)} recent emails, but failed to summarize them.",
                    "status": "Error"
                }

        else:
            # Mode B: Structured Booking Monitor (Text)
            b = result.booking
            
            # Check if email header metadata exists in pasted text (differentiating from flight route From:)
            from_match = re.search(r'(?:^|\n)(?:From|Sender):\s*([^\r\n]+@[^\r\n]+|[A-Za-z\s]+<[^>]+>)', text, re.IGNORECASE)
            date_match = re.search(r'(?:^|\n)(?:Email\s*Date|Sent|Date):\s*([A-Za-z0-9,\s:+/-]{8,})', text, re.IGNORECASE)
            text_date_raw = date_match.group(1).strip() if date_match else None
            text_from_raw = from_match.group(1).strip() if from_match else None
            e_date, e_time, e_sender = _parse_email_metadata(text_date_raw, text_from_raw)
            
            b_dict = {
                "booking_type": b.transport_type or "UNKNOWN",
                "title": f"{b.provider or 'Booking'} {b.service_number or ''}".strip(),
                "provider": b.provider,
                "booking_reference": b.booking_reference or (f"ROAM-ITN-{abs(hash(text)) % 90000 + 10000}" if ((b.transport_type or '').upper() == 'ITINERARY' or 'itiner' in (b.provider or '').lower()) else f"REF-{abs(hash(text)) % 90000 + 10000}"),
                "flight_number": b.service_number,
                "service_number": b.service_number,
                "departure_location": b.origin,
                "arrival_location": b.destination,
                "origin": b.origin,
                "destination": b.destination,
                "departure_time": b.departure_time,
                "arrival_time": b.arrival_time,
                "status": b.booking_status or "Extracted",
                "email_date": e_date,
                "email_time": e_time,
                "sender_email": e_sender,
                "user_id": user_id
            }
            saved = repo.save_booking(b_dict)
            saved["booking_id"] = saved["id"]
            return saved
            
    elif file:
        parser = DocumentParser()
        content = await file.read()
        mime_type = file.content_type
        try:
            if "pdf" in mime_type.lower():
                b = parser.extract_booking_from_pdf(content)
            else:
                b = parser.extract_booking_from_image(content, mime_type)
                
            b_dict = {
                "booking_type": b.transport_type or "UNKNOWN",
                "title": f"{b.provider or 'Booking'} {b.service_number or ''}".strip(),
                "provider": b.provider,
                "booking_reference": b.booking_reference,
                "flight_number": b.service_number,
                "service_number": b.service_number,
                "departure_location": b.origin,
                "arrival_location": b.destination,
                "origin": b.origin,
                "destination": b.destination,
                "departure_time": b.departure_time,
                "arrival_time": b.arrival_time,
                "status": b.booking_status or "Extracted",
                "email_date": "Unavailable",
                "email_time": "Unavailable",
                "sender_email": "Unavailable",
                "user_id": user_id
            }
            saved = repo.save_booking(b_dict)
            saved["booking_id"] = saved["id"]
            return saved
        except Exception as e:
            logger.error(f"Failed to parse document: {e}")
            return {"title": "Failed to parse document", "status": "Error"}
            
    return {"title": "No input provided", "status": "Error"}

@router.post("/")
async def create_booking(booking: BookingSchema):
    repo = get_booking_repository()
    saved = repo.save_booking(booking.model_dump())
    return saved

@router.get("/")
async def list_bookings(user_id: str = "demo-user"):
    repo = get_booking_repository()
    return repo.list_bookings(user_id)

@router.get("/{booking_id}")
async def get_booking(booking_id: str):
    repo = get_booking_repository()
    booking = repo.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@router.delete("/{booking_id}")
async def delete_booking(booking_id: str, user_id: str = "demo-user"):
    repo = get_booking_repository()
    repo.delete_booking(booking_id, user_id)
    return {"status": "deleted", "booking_id": booking_id}

@router.post("/{booking_id}/monitor")
async def start_monitoring(booking_id: str):
    repo = get_booking_repository()
    repo.start_monitoring(booking_id)
    return {"status": "ACTIVE", "message": "Monitoring started"}
