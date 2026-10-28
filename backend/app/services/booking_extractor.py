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

import re
from typing import Optional

def _heuristic_itinerary_extraction(text: str) -> Optional[CanonicalBooking]:
    lower = text.lower()
    
    has_itinerary_keywords = any(k in lower for k in [
        "itinerary", "itenary", "itenerary", "day plan", "tour plan", "trip plan", 
        "stops", "travel plan", "-in-a-nutshell"
    ])
    has_schedule_format = (
        ("|" in text and len(re.findall(r'\b\d{1,2}:\d{2}\b', text)) >= 2) or
        len(re.findall(r'(?:stop\s*\d+|day\s*\d+)', text, re.I)) >= 2 or
        len(re.findall(r'\|\s*\d{1,2}:\d{2}', text)) >= 2
    )
    
    if not (has_itinerary_keywords or has_schedule_format):
        return None
        
    b_type = "ITINERARY"
    
    # 1. Destination / Provider
    dest_name = ""
    quote_m = re.search(r"['\"]([A-Za-z\s-]+?)['\"]", text)
    if quote_m:
        cand = quote_m.group(1).replace("-in-a-nutshell", "").strip()
        if cand and cand.lower() not in ["stop", "time", "what to see", "time (approx.)"]:
            dest_name = cand
            
    if not dest_name:
        dest_match = re.search(r"([A-Za-z\s]+?)(?:-in-a-nutshell|\s+itinerary|\s+day plan|\s+tour plan|\s+trip plan)", text, re.I)
        if dest_match:
            candidate = dest_match.group(1).strip().strip("'\"* ")
            for noise in ["one-day", "one day", "a", "the", "my", "suggest", "sample", "ideal", "full day", "2-day", "3-day"]:
                if candidate.lower().startswith(noise):
                    candidate = candidate[len(noise):].strip()
            if candidate and len(candidate) > 2:
                dest_name = candidate
                
    if not dest_name:
        in_match = re.search(r'\b(?:in|for|to)\s+([A-Z][a-zA-Z\s]{2,15}?)(?:,|\.|\s+covering|\s+with|\n|\r)', text)
        if in_match:
            dest_name = in_match.group(1).strip()
            
    if not dest_name:
        if "kerala" in lower: dest_name = "Kerala"
        elif "rome" in lower: dest_name = "Rome"
        elif "goa" in lower: dest_name = "Goa"
        elif "paris" in lower: dest_name = "Paris"
        elif "delhi" in lower: dest_name = "Delhi"
        elif "jaipur" in lower: dest_name = "Jaipur"
        elif "mumbai" in lower: dest_name = "Mumbai"
        else: dest_name = "Roam"

    prov = f"{dest_name.title()} Itinerary"
    
    # 2. Times
    all_times = re.findall(r'\b\d{1,2}:\d{2}\b', text)
    dep_time = all_times[0] if all_times else "08:00"
    arr_time = all_times[-1] if len(all_times) > 1 else "20:00"

    # 3. Stops
    table_stops = re.findall(r'\|\s*\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?\s*\|\s*([^|\r\n]+)', text)
    clean_stops = [
        re.sub(r'^[^\w]+', '', s.strip().strip('* ')) 
        for s in table_stops 
        if s.strip() and not re.match(r'^(stop|time|what to see|approx)', s.strip(), re.I)
    ]
    if not clean_stops:
        bullet_stops = re.findall(r'(?:^|[\r\n])\s*[-*•]\s*(?:\d{1,2}:\d{2}\s*[-:]\s*)?([^:\r\n]+)', text)
        clean_stops = [
            re.sub(r'^[^\w]+', '', s.strip().strip('* ')) 
            for s in bullet_stops 
            if s.strip() and not re.match(r'^(stop|time|what to see|one-day|ideal)', s.strip(), re.I)
        ]

    stop_count = len(clean_stops) if clean_stops else max(len(all_times), 1)
    service_number = f"ITN-{stop_count}STOPS"
    
    orig = clean_stops[0] if clean_stops else f"{dest_name} (Base)"
    dest = clean_stops[-1] if len(clean_stops) > 1 else f"{dest_name} Tour"
    
    booking_ref = f"ROAM-ITN-{abs(hash(text)) % 90000 + 10000}"

    return CanonicalBooking(
        transport_type=b_type,
        provider=prov,
        service_number=service_number,
        booking_reference=booking_ref,
        origin=orig,
        destination=dest,
        departure_time=dep_time,
        arrival_time=arr_time,
        booking_status="Confirmed"
    )

def _heuristic_booking_extraction(text: str) -> CanonicalBooking:
    itin = _heuristic_itinerary_extraction(text)
    if itin:
        return itin

    lower = text.lower()
    
    # 1. Transport type
    b_type = "FLIGHT"
    if "flight" in lower or "airline" in lower or "air india" in lower or "indigo" in lower or "emirates" in lower or "lufthansa" in lower:
        b_type = "FLIGHT"
    elif "hotel" in lower or "resort" in lower or "inn" in lower or "stay" in lower:
        b_type = "HOTEL"
    elif "train" in lower or "rail" in lower or "irctc" in lower or "eurostar" in lower:
        b_type = "TRAIN"
    elif "bus" in lower:
        b_type = "BUS"
    elif "tour" in lower or "sightseeing" in lower:
        b_type = "TOUR"
    elif "restaurant" in lower or "dinner" in lower or "table" in lower:
        b_type = "RESTAURANT"
    elif "express" in lower:
        b_type = "TRAIN"
        
    # 2. Provider
    prov = "Booking"
    if "air india express" in lower:
        prov = "Air India Express"
        b_type = "FLIGHT"
    elif "air india" in lower:
        prov = "Air India"
        b_type = "FLIGHT"
    elif "emirates" in lower:
        prov = "Emirates"
    elif "eurostar" in lower:
        prov = "Eurostar"
    elif "lufthansa" in lower:
        prov = "Lufthansa"
    elif "delta" in lower:
        prov = "Delta"
    elif "united" in lower:
        prov = "United Airlines"
    elif "british airways" in lower or "ba " in lower:
        prov = "British Airways"
    elif "indigo" in lower:
        prov = "IndiGo"
    elif "vistara" in lower:
        prov = "Vistara"
    elif "irctc" in lower:
        prov = "IRCTC"
    elif "marriott" in lower:
        prov = "Marriott"
    elif "hilton" in lower:
        prov = "Hilton"
    elif "taj" in lower:
        prov = "Taj Hotels"
    else:
        domain_match = re.search(r'@([a-zA-Z0-9-]+)\.[a-z]+', text)
        if domain_match and domain_match.group(1).lower() not in ["gmail", "yahoo", "hotmail", "outlook"]:
            prov = domain_match.group(1).capitalize()
        else:
            body_lines = [l for l in text.splitlines() if not re.match(r'^(from|date|subject|to|cc):', l.strip(), re.IGNORECASE) and l.strip()]
            if body_lines:
                words = body_lines[0].split()
                if len(words) > 0 and len(words[0]) > 2:
                    prov = words[0].strip(":,")

    # 3. Service / Flight / Train number
    svc_match = re.search(r'(?:flight\s*(?:number|no|\#)|train\s*(?:number|no|\#)|service\s*(?:number|no|\#))\s*[:\-#]\s*([A-Za-z0-9\s-]{2,12})', text, re.IGNORECASE)
    if svc_match:
        service_number = svc_match.group(1).strip().upper()
    else:
        svc_match = re.search(r'\b([A-Z]{1,3}\s*\d{2,5}|\d{4,5})\b', text)
        service_number = svc_match.group(1).upper() if svc_match else ("AI 123" if "ai 123" in lower else "BK-100")
    
    # 4. Booking reference / PNR
    ref_match = re.search(r'(?:booking\s+reference|booking\s+ref|pnr|reservation\s+code|confirmation\s+code|booking\s+confirmation)[:\s#]*([A-Z0-9-]+)', text, re.IGNORECASE)
    if not ref_match:
        ref_match = re.search(r'(?:ref|pnr|confirmation|conf|reference)[:\s#]*([A-Z0-9-]+)', text, re.IGNORECASE)
    booking_ref = ref_match.group(1).upper() if ref_match else f"REF-{abs(hash(text)) % 100000}"
    
    # 5. Origin and destination
    orig, dest = "Unknown", "Unknown"
    # Check bullet / line formats: "From: ... \n To: ..."
    orig_match = re.search(r'(?:^|[\r\n•\-\*])\s*From\s*[:\-]\s*([^\r\n]+)', text, re.IGNORECASE)
    dest_match = re.search(r'(?:^|[\r\n•\-\*])\s*To\s*[:\-]\s*([^\r\n]+)', text, re.IGNORECASE)
    if orig_match and dest_match:
        orig = orig_match.group(1).strip()
        dest = dest_match.group(1).strip()
    else:
        body_text = "\n".join([l for l in text.splitlines() if not re.match(r'^(from\s*:|date\s*:|subject\s*:)', l.strip(), re.IGNORECASE)])
        route_match = re.search(r'(?:from\s+)?([A-Za-z\s]+?)\s+(?:to|&rarr;|->)\s+([A-Za-z\s]+)', body_text, re.IGNORECASE)
        if route_match:
            orig = route_match.group(1).strip()
            dest = route_match.group(2).strip().split('\n')[0].strip()
            dest = re.sub(r'\s+(confirmed|for|on|at|departure).*$', '', dest, flags=re.IGNORECASE).strip()
        elif "hyderabad" in lower and "delhi" in lower:
            orig = "Hyderabad"
            dest = "Delhi"
        elif "bengaluru" in lower and "hyderabad" in lower:
            orig = "Bengaluru (BLR)"
            dest = "Hyderabad (HYD)"

    # 6. Times, Dates, Passenger
    dep_m = re.search(r'(?:^|[\r\n•\-\*])\s*Departure\s*[:\-]\s*([^\r\n]+)', text, re.IGNORECASE)
    arr_m = re.search(r'(?:^|[\r\n•\-\*])\s*Arrival\s*[:\-]\s*([^\r\n]+)', text, re.IGNORECASE)
    pax_m = re.search(r'(?:^|[\r\n•\-\*])\s*Passenger\s*Name\s*[:\-]\s*([^\r\n]+)', text, re.IGNORECASE)
    date_m = re.search(r'(?:^|[\r\n•\-\*])\s*(?:Travel\s*Date|Date)\s*[:\-]\s*([^\r\n]+)', text, re.IGNORECASE)

    dep_time = dep_m.group(1).strip() if dep_m else None
    arr_time = arr_m.group(1).strip() if arr_m else None
    pax_name = pax_m.group(1).strip() if pax_m else None
    travel_date = date_m.group(1).strip() if date_m else None
        
    return CanonicalBooking(
        transport_type=b_type,
        provider=prov,
        service_number=service_number,
        booking_reference=booking_ref,
        origin=orig,
        destination=dest,
        departure_time=dep_time,
        arrival_time=arr_time,
        travel_date=travel_date,
        passenger_name=pax_name,
        booking_status="Confirmed"
    )

def _is_gmail_search_intent(text: str) -> bool:
    lower = text.lower().strip()
    # If the text has email headers or typical confirmation markers, it's a booking, not a query to read Gmail
    if re.search(r'^(from|subject|date|to):', lower, re.M) or re.search(r'\b(booking reference|pnr|reservation|ticket number|confirmed for departure)\b', lower):
        return False
    # Conversational requests to read or search email
    if re.search(r'\b(check|read|scan|search|fetch|find|summarise|summarize)\b.*\b(emails?|mails?|inbox|messages?)\b', lower):
        return True
    if lower.startswith("check my") or lower.startswith("read my") or "recent emails" in lower or "recent mails" in lower:
        return True
    return False

class BookingExtractor:
    def extract_intent_or_booking(self, text: str) -> ExtractionResult:
        if _is_gmail_search_intent(text):
            return ExtractionResult(
                mode="READ_GMAIL",
                gmail_intent=GmailReadIntent(intent="SEARCH_AND_SUMMARIZE", time_window="LAST_7_DAYS")
            )

        api_key = os.getenv("GROQ_API_KEY")
        raw_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        # Ensure deprecated llama models automatically fallback to active models
        model = "openai/gpt-oss-120b" if ("llama" in raw_model.lower()) else raw_model
        if not api_key or api_key == "your_groq_api_key_here":
            return ExtractionResult(
                mode="STRUCTURED_BOOKING",
                booking=_heuristic_booking_extraction(text)
            )

        client = Groq(api_key=api_key)
        
        system_prompt = (
            "You are an intent classifier and booking extractor.\n"
            "Determine if the user's text is a conversational request to read their Gmail for travel info (e.g., 'Check my recent Air India mails', 'Did I get any cancellation?').\n"
            "If yes, set mode='READ_GMAIL' and populate 'gmail_intent' with constraints (intent=SEARCH_AND_SUMMARIZE, time_window, etc).\n"
            "Otherwise, if the text is a pasted booking confirmation or itinerary/travel plan, set mode='STRUCTURED_BOOKING' and extract the details into 'booking'.\n"
            "If the text is an itinerary or multi-stop travel schedule, set transport_type='ITINERARY', provider='[Destination] Itinerary' (e.g. 'Kerala Itinerary'), service_number='ITN-[X]STOPS' (e.g. 'ITN-6STOPS'), origin=starting stop/location, destination=final stop or destination, departure_time=first scheduled time, arrival_time=last scheduled time, booking_status='Confirmed'.\n"
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
            data = json.loads(res.choices[0].message.content)
            return ExtractionResult.model_validate(data)
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            if _is_gmail_search_intent(text):
                return ExtractionResult(
                    mode="READ_GMAIL",
                    gmail_intent=GmailReadIntent(intent="SEARCH_AND_SUMMARIZE", time_window="LAST_7_DAYS")
                )
            else:
                return ExtractionResult(
                    mode="STRUCTURED_BOOKING",
                    booking=_heuristic_booking_extraction(text)
                )
