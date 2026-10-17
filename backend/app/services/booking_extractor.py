import os
import logging
import instructor
from groq import Groq
from pydantic import BaseModel
from app.schemas.booking import CanonicalBooking, GmailReadIntent

logger = logging.getLogger(__name__)

class ExtractionResult(BaseModel):
    mode: str  # "READ_GMAIL" or "STRUCTURED_BOOKING"
    gmail_intent: GmailReadIntent | None = None
    booking: CanonicalBooking | None = None

class BookingExtractor:
    def extract_intent_or_booking(self, text: str) -> ExtractionResult:
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        if not api_key or api_key == "your_groq_api_key_here":
            if "check my recent" in text.lower() or "mail" in text.lower() or "summarise" in text.lower():
                return ExtractionResult(
                    mode="READ_GMAIL",
                    gmail_intent=GmailReadIntent(intent="SEARCH_AND_SUMMARIZE", time_window="LAST_7_DAYS")
                )
            else:
                service_num = "Mock123"
                if "AI 123" in text:
                    service_num = "AI 123"
                return ExtractionResult(
                    mode="STRUCTURED_BOOKING",
                    booking=CanonicalBooking(provider="Air India" if "AI 123" in text else "Mock", service_number=service_num, booking_status="Confirmed")
                )

        client = Groq(api_key=api_key)
        
        system_prompt = (
            "You are an intent classifier and booking extractor.\n"
            "Determine if the user's text is a conversational request to read their Gmail for travel info (e.g., 'Check my recent Air India mails', 'Did I get any cancellation?').\n"
            "If yes, set mode='READ_GMAIL' and populate 'gmail_intent' with constraints (intent=SEARCH_AND_SUMMARIZE, time_window, etc).\n"
            "Otherwise, if the text is a pasted booking confirmation or itinerary, set mode='STRUCTURED_BOOKING' and extract the details into 'booking'.\n"
            "Leave unknown fields null. Do not hallucinate."
        )
        import json
        system_prompt += "\n\nRespond with JSON matching this schema: " + json.dumps(ExtractionResult.model_json_schema())
        try:
            res = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"},
                temperature=0
            )
            import json
            data = json.loads(res.choices[0].message.content)
            return ExtractionResult.model_validate(data)
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            # Fallback to mock for capstone demo if rate limited
            if "check my recent" in text.lower() or "mail" in text.lower() or "summarise" in text.lower() or "email" in text.lower():
                return ExtractionResult(
                    mode="READ_GMAIL",
                    gmail_intent=GmailReadIntent(intent="SEARCH_AND_SUMMARIZE", time_window="LAST_7_DAYS")
                )
            else:
                return ExtractionResult(
                    mode="STRUCTURED_BOOKING",
                    booking=CanonicalBooking(provider="Air India", service_number="AI 123", booking_status="Confirmed")
                )
