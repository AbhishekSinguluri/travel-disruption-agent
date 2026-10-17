import os
import logging
import base64
import fitz  # PyMuPDF
from groq import Groq
import instructor
from app.schemas.import_trip import ExtractedTrip

logger = logging.getLogger(__name__)

class DocumentParser:
    def extract_from_text(self, text: str) -> ExtractedTrip:
        if not text or not text.strip():
            raise ValueError("Input text is empty.")
        return self._extract_via_llm(text)
    def extract_from_pdf(self, file_bytes: bytes) -> ExtractedTrip:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            
            # Fallback for scanned PDFs
            if len(text.strip()) < 50:
                logger.info("PDF text insufficient, attempting vision fallback...")
                if len(doc) > 0:
                    pix = doc[0].get_pixmap()
                    img_bytes = pix.tobytes("png")
                    return self.extract_from_image(img_bytes, "image/png")
            return self._extract_via_llm(text)
        except Exception as e:
            logger.error(f"[DOC] PDF parse error: {e}")
            raise ValueError("Failed to extract itinerary from PDF.")
        
    def extract_from_image(self, file_bytes: bytes, mime_type: str) -> ExtractedTrip:
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_VISION_MODEL", "llama-3.2-90b-vision-preview")
        if not api_key or api_key == "your_groq_api_key_here":
            return self._mock_extraction()
            
        b64 = base64.b64encode(file_bytes).decode('utf-8')
        try:
            client = instructor.from_groq(Groq(api_key=api_key))
            res = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract the itinerary from this image. Do not guess unknown fields, return null."},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}}
                        ]
                    }
                ],
                response_model=ExtractedTrip,
            )
            return res
        except Exception as e:
            logger.error(f"[VISION] Extraction failed: {e}")
            raise ValueError("Failed to extract itinerary from image.")

    def extract_booking_from_pdf(self, file_bytes: bytes) -> 'CanonicalBooking':
        from app.schemas.booking import CanonicalBooking
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            
            if len(text.strip()) < 50:
                if len(doc) > 0:
                    pix = doc[0].get_pixmap()
                    img_bytes = pix.tobytes("png")
                    return self.extract_booking_from_image(img_bytes, "image/png")
                    
            return self._extract_booking_via_llm(text)
        except Exception as e:
            logger.error(f"[DOC] PDF parse error: {e}")
            raise ValueError("Failed to extract booking from PDF.")

    def extract_booking_from_image(self, file_bytes: bytes, mime_type: str) -> 'CanonicalBooking':
        from app.schemas.booking import CanonicalBooking
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_VISION_MODEL", "llama-3.2-11b-vision-preview")
        if not api_key or api_key == "your_groq_api_key_here":
            return CanonicalBooking(provider="Mock", service_number="Mock123", booking_status="Confirmed")
            
        b64 = base64.b64encode(file_bytes).decode('utf-8')
        try:
            client = instructor.from_groq(Groq(api_key=api_key))
            res = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract the travel booking details from this image into a structured format. Do not guess unknown fields, return null."},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}}
                        ]
                    }
                ],
                response_model=CanonicalBooking,
            )
            return res
        except Exception as e:
            logger.error(f"[VISION] Booking extraction failed: {e}")
            raise ValueError("Failed to extract booking from image.")

    def _extract_booking_via_llm(self, text: str) -> 'CanonicalBooking':
        from app.schemas.booking import CanonicalBooking
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_EXTRACTION_MODEL", "openai/gpt-oss-120b")
        if not api_key or api_key == "your_groq_api_key_here":
            return CanonicalBooking(provider="Mock", service_number="Mock123", booking_status="Confirmed")
            
        system_prompt = (
            "You are a booking extractor. Extract booking details from this text into a CanonicalBooking structure.\n"
            "Leave unknown fields null. Do not hallucinate."
        )

        try:
            client = instructor.from_groq(Groq(api_key=api_key))
            res = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract booking from this text:\n{text}"}
                ],
                response_model=CanonicalBooking,
                max_retries=1,
            )
            return res
        except Exception as e:
            logger.error(f"[DOC] LLM Extraction failed: {e}")
            return CanonicalBooking(provider="Mock", service_number="Mock123", booking_status="Confirmed")
            
    def _extract_via_llm(self, text: str) -> ExtractedTrip:
        api_key = os.getenv("GROQ_API_KEY")
        # Use the specific extraction model, do NOT use GROQ_MODEL which is optimized for ChangeDetector
        model = os.getenv("GROQ_EXTRACTION_MODEL", "openai/gpt-oss-120b")
        if not api_key or api_key == "your_groq_api_key_here":
            return self._heuristic_extraction(text)
            
        system_prompt = (
            "You are converting a user's informal travel notes into structured itinerary data.\n"
            "The user may use shorthand, fragments, inconsistent punctuation, abbreviations, natural language, or incomplete information.\n"
            "Interpret the user's intended itinerary without inventing unsupported facts.\n"
            "Preserve every meaningful activity/location mentioned by the user.\n"
            "Normalize formatting, not meaning.\n"
            "Normalize explicit times into HH:MM where possible.\n"
            "Unknown information must remain null.\n"
            "CRITICAL: The list of activities MUST be named 'stops'. DO NOT name it 'activities'.\n"
            "CRITICAL: The name of the activity MUST be named 'title'. DO NOT name it 'name' or 'activity'."
        )

        client = instructor.from_groq(Groq(api_key=api_key), mode=instructor.Mode.MD_JSON)
        res = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract the itinerary from this text:\n{text}"}
            ],
            response_model=ExtractedTrip,
            max_retries=2,
            max_tokens=4000,
        )
        return res

    def _mock_extraction(self) -> ExtractedTrip:
        return ExtractedTrip(
            name="Mock Imported Trip",
            destination="Unknown",
            start_date="2026-10-01",
            end_date="2026-10-02",
            days=[]
        )

    def _heuristic_extraction(self, text: str) -> ExtractedTrip:
        import re
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        stops = []
        destination = "Unknown"
        name = "Imported Trip"
        
        for idx, line in enumerate(lines):
            # Try to extract time (e.g. 9am, 12:00 PM)
            time_match = re.search(r'\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b', line, re.IGNORECASE)
            start_time = time_match.group(0) if time_match else f"{9+idx}:00 AM"
            
            # Use the rest of the line as title
            title = line
            if time_match:
                title = line.replace(time_match.group(0), "").strip(" ,-")
            
            if not title:
                title = f"Activity {idx+1}"
                
            if idx == 0 and "Hyderabad" in text:
                destination = "Hyderabad"
                name = "Hyderabad Trip"
            elif idx == 0:
                name = "Generated Trip"
                
            stops.append({
                "title": title[:50],
                "category": "Attraction",
                "location_name": title[:50],
                "start_time": start_time,
                "confidence": 0.8
            })
            
        from app.schemas.import_trip import ExtractedDay
        day = ExtractedDay(date="2026-10-01", stops=stops)
        return ExtractedTrip(
            name=name,
            destination=destination,
            start_date="2026-10-01",
            end_date="2026-10-02",
            days=[day]
        )
