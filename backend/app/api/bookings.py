
from fastapi import APIRouter
from app.schemas.booking import BookingSchema
from app.db.repositories import get_booking_repository
import uuid
import datetime

router = APIRouter()

from fastapi import UploadFile, File, Form
from typing import Optional

@router.post("/extract")
async def extract_booking(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    user_id: str = "demo-user"
):
    from app.services.booking_extractor import BookingExtractor
    from app.services.document_parser import DocumentParser
    from app.services.gmail_provider import get_gmail_provider, RealGmailProvider
    import os
    import instructor
    from groq import Groq
    from datetime import datetime, timedelta
    
    if text:
        try:
            extractor = BookingExtractor()
            result = extractor.extract_intent_or_booking(text)
        except Exception as e:
            logger.error(f"Failed to extract intent: {e}")
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail="The AI agent failed to process the document.")
        
        if result.mode == "READ_GMAIL":
            # Mode A: Conversational Gmail Reader
            provider = get_gmail_provider(user_id)
            if not isinstance(provider, RealGmailProvider):
                # Fallback to mock behavior if no real provider
                return {
                    "title": "Please connect your Gmail account to search for recent travel emails.",
                    "status": "Gmail Not Connected"
                }
            
            # Use intent to build query
            intent = result.gmail_intent
            days = 7 # default 7 days
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
                
            # Summarize the emails using LLM
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key or api_key == "your_groq_api_key_here":
                return {
                    "title": f"I found {len(candidate_emails)} recent emails matching your request. (Mock summary)",
                    "status": "Summary Ready"
                }
                
            try:
                emails_text = ""
                for e in candidate_emails[:2]:
                    msg_full = provider.get_message(e['id'])
                    emails_text += f"Subject: {e.get('subject')}\nBody: {msg_full.get('body')}\n\n"
                
                from app.services.document_parser import DocumentParser
                parser = DocumentParser()
                booking = parser._extract_booking_via_llm(emails_text)
                
                b_dict = booking.model_dump()
                b_dict["status"] = "Extracted from Gmail"
                return b_dict
                
            except Exception as e:
                logger.error(f"Failed to extract booking: {e}")
                return {
                    "title": f"I found {len(candidate_emails)} recent emails, but failed to summarize them.",
                    "status": "Error"
                }

        else:
            # Mode B: Structured Booking Monitor (Text)
            b = result.booking
            return {
                "booking_type": b.transport_type or "UNKNOWN",
                "title": f"{b.provider or 'Booking'} {b.service_number or ''}".strip(),
                "provider": b.provider,
                "booking_reference": b.booking_reference,
                "flight_number": b.service_number,
                "departure_location": b.origin,
                "arrival_location": b.destination,
                "departure_time": b.departure_time,
                "arrival_time": b.arrival_time,
                "status": b.booking_status or "Extracted"
            }
            
    elif file:
        # Mode B: Structured Booking Monitor (Image/PDF)
        parser = DocumentParser()
        content = await file.read()
        mime_type = file.content_type
        try:
            if "pdf" in mime_type.lower():
                b = parser.extract_booking_from_pdf(content)
            else:
                b = parser.extract_booking_from_image(content, mime_type)
                
            return {
                "booking_type": b.transport_type or "UNKNOWN",
                "title": f"{b.provider or 'Booking'} {b.service_number or ''}".strip(),
                "provider": b.provider,
                "booking_reference": b.booking_reference,
                "flight_number": b.service_number,
                "departure_location": b.origin,
                "arrival_location": b.destination,
                "departure_time": b.departure_time,
                "arrival_time": b.arrival_time,
                "status": b.booking_status or "Extracted"
            }
        except Exception as e:
            return {"title": "Failed to parse document", "status": "Error"}
            
    return {"title": "No input provided", "status": "Error"}

@router.post("/")
async def create_booking(booking: BookingSchema):
    repo = get_booking_repository()
    booking.id = str(uuid.uuid4())
    repo.save_booking(booking.model_dump())
    return booking

@router.get("/")
async def list_bookings(user_id: str = "demo-user"):
    repo = get_booking_repository()
    return repo.list_bookings(user_id)

@router.post("/{booking_id}/monitor")
async def start_monitoring(booking_id: str):
    repo = get_booking_repository()
    repo.start_monitoring(booking_id)
    return {"status": "ACTIVE", "message": "Monitoring started"}
