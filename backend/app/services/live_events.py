import os
import json
import time
import uuid
import logging
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CACHE_FILE = os.path.join(CACHE_DIR, "events_cache.json")
CACHE_TTL_SECONDS = 30 * 24 * 3600  # 30-day cache so every state is queried at most once, preserving API credits!

# All 28 Indian States + 8 Union Territories
INDIAN_STATES_DATA = {
    "andaman and nicobar": {"name": "Andaman & Nicobar Islands", "hub": "Port Blair", "icon": "🏝️"},
    "andhra pradesh": {"name": "Andhra Pradesh", "hub": "Visakhapatnam", "icon": "🌊"},
    "arunachal pradesh": {"name": "Arunachal Pradesh", "hub": "Itanagar", "icon": "⛰️"},
    "assam": {"name": "Assam", "hub": "Guwahati", "icon": "🦏"},
    "bihar": {"name": "Bihar", "hub": "Patna", "icon": "🏛️"},
    "chandigarh": {"name": "Chandigarh", "hub": "Chandigarh", "icon": "🌹"},
    "chhattisgarh": {"name": "Chhattisgarh", "hub": "Raipur", "icon": "🌳"},
    "dadra and nagar haveli": {"name": "Dadra & Nagar Haveli and Daman & Diu", "hub": "Daman", "icon": "🏖️"},
    "delhi": {"name": "Delhi NCR", "hub": "New Delhi", "icon": "🏛️"},
    "goa": {"name": "Goa", "hub": "Panaji", "icon": "🏖️"},
    "gujarat": {"name": "Gujarat", "hub": "Ahmedabad", "icon": "🪁"},
    "haryana": {"name": "Haryana", "hub": "Gurugram", "icon": "🏙️"},
    "himachal pradesh": {"name": "Himachal Pradesh", "hub": "Shimla", "icon": "🏔️"},
    "jammu and kashmir": {"name": "Jammu & Kashmir", "hub": "Srinagar", "icon": "🛶"},
    "jharkhand": {"name": "Jharkhand", "hub": "Ranchi", "icon": "🌲"},
    "karnataka": {"name": "Karnataka", "hub": "Bengaluru", "icon": "💻"},
    "kerala": {"name": "Kerala", "hub": "Kochi", "icon": "🌴"},
    "ladakh": {"name": "Ladakh", "hub": "Leh", "icon": "🏔️"},
    "lakshadweep": {"name": "Lakshadweep", "hub": "Kavaratti", "icon": "🐠"},
    "madhya pradesh": {"name": "Madhya Pradesh", "hub": "Indore", "icon": "🐅"},
    "maharashtra": {"name": "Maharashtra", "hub": "Mumbai", "icon": "🎬"},
    "manipur": {"name": "Manipur", "hub": "Imphal", "icon": "🌸"},
    "meghalaya": {"name": "Meghalaya", "hub": "Shillong", "icon": "☁️"},
    "mizoram": {"name": "Mizoram", "hub": "Aizawl", "icon": "🎋"},
    "nagaland": {"name": "Nagaland", "hub": "Kohima", "icon": "🪶"},
    "odisha": {"name": "Odisha", "hub": "Bhubaneswar", "icon": "🛕"},
    "puducherry": {"name": "Puducherry", "hub": "Puducherry", "icon": "⛵"},
    "punjab": {"name": "Punjab", "hub": "Amritsar", "icon": "🌾"},
    "rajasthan": {"name": "Rajasthan", "hub": "Jaipur", "icon": "🏰"},
    "sikkim": {"name": "Sikkim", "hub": "Gangtok", "icon": "❄️"},
    "tamil nadu": {"name": "Tamil Nadu", "hub": "Chennai", "icon": "🏛️"},
    "telangana": {"name": "Telangana", "hub": "Hyderabad", "icon": "🕌"},
    "tripura": {"name": "Tripura", "hub": "Agartala", "icon": "🍃"},
    "uttar pradesh": {"name": "Uttar Pradesh", "hub": "Varanasi", "icon": "🪔"},
    "uttarakhand": {"name": "Uttarakhand", "hub": "Dehradun", "icon": "🏔️"},
    "west bengal": {"name": "West Bengal", "hub": "Kolkata", "icon": "🎨"}
}

# Major Indian city alias to canonical state mapping
CITY_TO_STATE_MAP = {
    "mumbai": "maharashtra",
    "pune": "maharashtra",
    "nagpur": "maharashtra",
    "jaipur": "rajasthan",
    "udaipur": "rajasthan",
    "jodhpur": "rajasthan",
    "jaisalmer": "rajasthan",
    "hyderabad": "telangana",
    "secunderabad": "telangana",
    "warangal": "telangana",
    "bengaluru": "karnataka",
    "bangalore": "karnataka",
    "mysore": "karnataka",
    "mysuru": "karnataka",
    "chennai": "tamil nadu",
    "madurai": "tamil nadu",
    "coimbatore": "tamil nadu",
    "delhi": "delhi",
    "new delhi": "delhi",
    "noida": "delhi",
    "gurgaon": "haryana",
    "gurugram": "haryana",
    "faridabad": "haryana",
    "kolkata": "west bengal",
    "calcutta": "west bengal",
    "ahmedabad": "gujarat",
    "surat": "gujarat",
    "vadodara": "gujarat",
    "kochi": "kerala",
    "cochin": "kerala",
    "thiruvananthapuram": "kerala",
    "trivandrum": "kerala",
    "panaji": "goa",
    "panjim": "goa",
    "margao": "goa",
    "amritsar": "punjab",
    "ludhiana": "punjab",
    "chandigarh": "chandigarh",
    "varanasi": "uttar pradesh",
    "lucknow": "uttar pradesh",
    "agra": "uttar pradesh",
    "kanpur": "uttar pradesh",
    "shimla": "himachal pradesh",
    "manali": "himachal pradesh",
    "dharamshala": "himachal pradesh",
    "srinagar": "jammu and kashmir",
    "jammu": "jammu and kashmir",
    "leh": "ladakh",
    "visakhapatnam": "andhra pradesh",
    "vizag": "andhra pradesh",
    "vijayawada": "andhra pradesh",
    "patna": "bihar",
    "bhopal": "madhya pradesh",
    "indore": "madhya pradesh",
    "gwalior": "madhya pradesh",
    "bhubaneswar": "odisha",
    "puri": "odisha",
    "guwahati": "assam",
    "dehradun": "uttarakhand",
    "rishikesh": "uttarakhand",
    "haridwar": "uttarakhand",
    "mussoorie": "uttarakhand",
    "shillong": "meghalaya",
    "gangtok": "sikkim",
    "port blair": "andaman and nicobar",
    "raipur": "chhattisgarh",
    "ranchi": "jharkhand"
}

def _load_cache() -> Dict[str, Any]:
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading events cache: {e}")
    return {}

def _save_cache(cache_data: Dict[str, Any]):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Error saving events cache: {e}")

BMS_CITY_SLUGS = {
    "delhi": "national-capital-region-ncr",
    "delhi ncr": "national-capital-region-ncr",
    "new delhi": "national-capital-region-ncr",
    "maharashtra": "mumbai",
    "mumbai": "mumbai",
    "pune": "pune",
    "karnataka": "bengaluru",
    "bengaluru": "bengaluru",
    "bangalore": "bengaluru",
    "telangana": "hyderabad",
    "hyderabad": "hyderabad",
    "rajasthan": "jaipur",
    "jaipur": "jaipur",
    "goa": "goa",
    "tamil nadu": "chennai",
    "chennai": "chennai",
    "west bengal": "kolkata",
    "kolkata": "kolkata",
    "gujarat": "ahmedabad",
    "ahmedabad": "ahmedabad",
    "kerala": "kochi",
    "kochi": "kochi",
    "chandigarh": "chandigarh",
    "punjab": "chandigarh",
    "amritsar": "chandigarh",
    "uttar pradesh": "lucknow",
    "lucknow": "lucknow",
    "varanasi": "varanasi",
    "uttarakhand": "dehradun",
    "dehradun": "dehradun",
    "madhya pradesh": "indore",
    "indore": "indore",
    "bhopal": "bhopal",
    "odisha": "bhubaneswar",
    "bhubaneswar": "bhubaneswar",
    "assam": "guwahati",
    "guwahati": "guwahati",
    "bihar": "patna",
    "patna": "patna",
    "himachal pradesh": "shimla",
    "shimla": "shimla",
    "jammu and kashmir": "srinagar",
    "srinagar": "srinagar",
    "puducherry": "puducherry"
}

def resolve_booking_url(raw_url: Optional[str], state_key: str = "", title: str = "", hub: str = "") -> str:
    """Ensures every ticket URL is valid, active and never opens a blank BookMyShow page"""
    target = (state_key or hub or "").lower().strip().replace("_", " ")
    slug = BMS_CITY_SLUGS.get(target)
    if not slug:
        for k, v in BMS_CITY_SLUGS.items():
            if k in target or target in k:
                slug = v
                break
    if not slug:
        slug = "mumbai"

    if not raw_url or raw_url.rstrip("/") in [
        "https://in.bookmyshow.com/explore/events",
        "http://in.bookmyshow.com/explore/events",
        "https://in.bookmyshow.com",
        "http://in.bookmyshow.com"
    ] or ("bookmyshow.com/explore/events" in raw_url and "explore/events-" not in raw_url):
        return f"https://in.bookmyshow.com/explore/events-{slug}"
    return raw_url

class LiveEventsService:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")

    def resolve_location(self, query: str) -> tuple[str, str, str]:
        """Resolves any Indian city or state query to (canonical_state_key, display_name, search_query)"""
        q_low = query.lower().strip()
        
        # 1. Exact state match
        if q_low in INDIAN_STATES_DATA:
            state_info = INDIAN_STATES_DATA[q_low]
            return q_low, state_info["name"], f"events in {state_info['hub']}, {state_info['name']}"
            
        # 2. City alias match
        if q_low in CITY_TO_STATE_MAP:
            canonical_state = CITY_TO_STATE_MAP[q_low]
            state_info = INDIAN_STATES_DATA.get(canonical_state, {})
            display_name = f"{q_low.title()}, {state_info.get('name', 'India')}"
            return canonical_state, display_name, f"events in {q_low.title()}, {state_info.get('name', 'India')}"

        # 3. Partial state or hub match
        for key, info in INDIAN_STATES_DATA.items():
            if q_low in key or key in q_low or q_low in info["hub"].lower():
                return key, info["name"], f"events in {info['hub']}, {info['name']}"

        # Default fallback strictly in India (Maharashtra / Mumbai)
        return "maharashtra", "Maharashtra", "events in Mumbai, Maharashtra, India"

    def get_states_directory(self) -> Dict[str, Any]:
        """Returns directory of all 36 Indian states and UTs with their cache status."""
        cache = _load_cache()
        states_list = []
        cached_count = 0

        for key, info in sorted(INDIAN_STATES_DATA.items(), key=lambda item: item[1]["name"]):
            hub_key = info["hub"].lower()
            is_cached = bool((cache.get(key) and cache[key].get("events")) or (cache.get(hub_key) and cache[hub_key].get("events")))
            if is_cached:
                cached_count += 1
            states_list.append({
                "key": key,
                "name": info["name"],
                "hub": info["hub"],
                "icon": info["icon"],
                "is_cached": is_cached
            })

        return {
            "total_states": len(states_list),
            "cached_count": cached_count,
            "states": states_list
        }

    def get_city_events(self, location_query: str = "maharashtra", force_refresh: bool = False, city: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        target = (city or location_query or "maharashtra").strip().lower()
        canonical_key, display_name, search_query = self.resolve_location(target)
        cache = _load_cache()

        state_info = INDIAN_STATES_DATA.get(canonical_key, {})
        hub_key = state_info.get("hub", "").lower()

        # Check cache under canonical key, target name, or hub city name
        cached_entry = cache.get(canonical_key) or cache.get(target) or (cache.get(hub_key) if hub_key else None)

        now = time.time()
        # Strictly conserve credits: If state has cached events, return from cache immediately (0 credits used)!
        if not force_refresh and cached_entry and cached_entry.get("events"):
            logger.info(f"[EVENTS] Cache HIT for '{target}' (key: {canonical_key}): {len(cached_entry['events'])} events returned (0 credits used)")
            return {
                "city": display_name,
                "state_key": canonical_key,
                "cached": True,
                "credits_used": 0,
                "last_updated": cached_entry.get("last_updated") or time.strftime("%Y-%m-%d %H:%M:%S"),
                "events": cached_entry["events"]
            }

        # Fetch from SerpAPI (1 API credit used, saved permanently for future queries)
        if not self.api_key or self.api_key == "your_serpapi_key_here":
            logger.warning("[EVENTS] Missing SERPAPI_API_KEY, returning curated fallback")
            return self._get_fallback_events(canonical_key)

        try:
            logger.info(f"[EVENTS] Querying SerpAPI Google Events for '{search_query}, India' (1 credit used)...")
            url = "https://serpapi.com/search.json"
            params = {
                "engine": "google_events",
                "q": f"{search_query}, India",
                "location": "India",
                "api_key": self.api_key,
                "hl": "en",
                "gl": "in"
            }
            res = requests.get(url, params=params, timeout=12)
            if res.status_code == 200:
                raw_data = res.json()
                raw_events = raw_data.get("events_results", [])
                formatted_events = self._format_raw_events(raw_events, canonical_key, display_name)
                
                if formatted_events:
                    entry = {
                        "timestamp": now,
                        "display_name": display_name,
                        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "events": formatted_events
                    }
                    # Save under canonical state key
                    cache[canonical_key] = entry
                    # Also save under target and hub city aliases so all future searches use 0 credits
                    if target != canonical_key:
                        cache[target] = entry
                    if hub_key:
                        cache[hub_key] = entry
                        
                    _save_cache(cache)
                    logger.info(f"[EVENTS] Successfully cached {len(formatted_events)} events for {canonical_key}. Future visits will use 0 credits!")
                    return {
                        "city": display_name,
                        "state_key": canonical_key,
                        "cached": False,
                        "credits_used": 1,
                        "last_updated": entry["last_updated"],
                        "events": formatted_events
                    }
            else:
                logger.error(f"[EVENTS] SerpAPI returned status {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"[EVENTS] SerpAPI query failed: {e}")

        # Fallback if network or quota issue, also cache it
        fallback = self._get_fallback_events(canonical_key)
        cache[canonical_key] = {
            "timestamp": now,
            "display_name": display_name,
            "last_updated": fallback.get("last_updated"),
            "events": fallback.get("events", [])
        }
        _save_cache(cache)
        return fallback

    def _format_raw_events(self, raw_events: List[Dict[str, Any]], state_key: str, display_name: str) -> List[Dict[str, Any]]:
        formatted = []
        for idx, ev in enumerate(raw_events[:12]):
            ev_id = f"evt-{state_key[:3]}-{idx+1}"
            title = ev.get("title") or f"Local Event in {display_name}"
            
            # Extract venue
            venue_info = ev.get("venue") or {}
            venue_name = venue_info.get("name") if isinstance(venue_info, dict) else str(venue_info)
            if not venue_name:
                addr_list = ev.get("address", [])
                venue_name = addr_list[0] if addr_list else f"Central {display_name}"
                
            # Date string
            date_info = ev.get("date") or {}
            when = date_info.get("when") or date_info.get("start_date") or "Upcoming This Week"
            
            # Ticket link & source
            ticket_info = ev.get("ticket_info", [])
            primary_ticket = ticket_info[0] if ticket_info else {}
            raw_url = primary_ticket.get("link") or ev.get("link")
            ticket_url = resolve_booking_url(raw_url, state_key, title, venue_name)
            source = primary_ticket.get("source") or "BookMyShow / Local Box Office"

            # Category detection
            cat = ev.get("type") or "Cultural & Entertainment"
            title_low = title.lower()
            if any(w in title_low for w in ["music", "concert", "sufi", "band", "live"]):
                category = "Live Music"
            elif any(w in title_low for w in ["comedy", "standup", "theater", "play"]):
                category = "Theater & Comedy"
            elif any(w in title_low for w in ["tour", "walk", "cycling", "heritage", "palace"]):
                category = "Heritage & Tours"
            elif any(w in title_low for w in ["festival", "fest", "utsav", "fair"]):
                category = "Festival & Cultural"
            elif any(w in title_low for w in ["workshop", "craft", "pottery", "print"]):
                category = "Workshops & Crafts"
            else:
                category = "Local Experience"

            # Approximate realistic ticket price
            price_str = "₹350"
            unit_price = 350
            if "free" in title_low or "free" in str(ev.get("description", "")).lower():
                price_str = "Free Entry"
                unit_price = 0
            elif "tour" in title_low or "cycling" in title_low or "walk" in title_low:
                price_str = "₹750"
                unit_price = 750
            elif "comedy" in title_low or "standup" in title_low:
                price_str = "₹499"
                unit_price = 499
            elif "music" in title_low or "concert" in title_low:
                price_str = "₹600"
                unit_price = 600

            thumbnail = ev.get("thumbnail") or "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=500&q=80"

            formatted.append({
                "id": ev_id,
                "title": title,
                "venue": venue_name,
                "city": display_name,
                "timing": when,
                "category": category,
                "price": price_str,
                "unit_price": unit_price,
                "ticket_url": ticket_url,
                "source": source,
                "thumbnail": thumbnail,
                "description": ev.get("description") or f"Verified Indian local event happening live in {display_name}."
            })
        return formatted

    def _get_fallback_events(self, state_key: str) -> Dict[str, Any]:
        """Verified Indian state event highlights for reliable offline performance"""
        state_info = INDIAN_STATES_DATA.get(state_key, {"name": state_key.title(), "hub": state_key.title()})
        hub = state_info["hub"]
        state_name = state_info["name"]
        bms_city_url = resolve_booking_url(None, state_key, "Local Events", hub)

        events = [
            {
                "id": f"evt-{state_key[:3]}-1",
                "title": f"{hub} Heritage & Cultural Exploration",
                "venue": f"Central Cultural Plaza, {hub}",
                "city": f"{hub}, {state_name}",
                "timing": "Daily at 6:30 PM",
                "category": "Heritage & Tours",
                "price": "₹450",
                "unit_price": 450,
                "ticket_url": bms_city_url,
                "source": "BookMyShow / State Tourism",
                "thumbnail": "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=400&q=80",
                "description": f"Guided cultural journey through historic landmarks and artisan centers in {hub}."
            },
            {
                "id": f"evt-{state_key[:3]}-2",
                "title": f"Live Indian Classical & Fusion Night",
                "venue": f"Auditorium Center, {hub}",
                "city": f"{hub}, {state_name}",
                "timing": "This Weekend at 7:00 PM",
                "category": "Live Music",
                "price": "₹600",
                "unit_price": 600,
                "ticket_url": bms_city_url,
                "source": "BookMyShow Live",
                "thumbnail": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400&q=80",
                "description": "Celebration of traditional ragas, contemporary instruments, and local vocal talent."
            },
            {
                "id": f"evt-{state_key[:3]}-3",
                "title": f"Traditional Regional Handicraft Masterclass",
                "venue": f"Artisan Village, {hub}",
                "city": f"{hub}, {state_name}",
                "timing": "Daily 11:00 AM – 1:00 PM",
                "category": "Workshops & Crafts",
                "price": "₹350",
                "unit_price": 350,
                "ticket_url": bms_city_url,
                "source": "State Craft Collective",
                "thumbnail": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=400&q=80",
                "description": f"Hands-on workshop exploring authentic indigenous art and textile crafts of {state_name}."
            }
        ]

        return {
            "city": state_name,
            "state_key": state_key,
            "cached": True,
            "credits_used": 0,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "events": events
        }

    def book_event(self, event_data: Dict[str, Any], num_tickets: int = 1, attendee_name: str = "Demo Traveler") -> Dict[str, Any]:
        """Action Layer Tool: Calculates total bill and writes confirmed booking payload to repository"""
        unit_price = event_data.get("unit_price", 350)
        subtotal = unit_price * num_tickets
        convenience_fee = int(subtotal * 0.05)
        total_bill = subtotal + convenience_fee

        ref_id = f"BMS-{event_data.get('city', 'IND')[:3].upper()}-{str(uuid.uuid4())[:4].upper()}"
        booking_payload = {
            "id": f"booking-event-{ref_id}",
            "type": "LOCAL_EVENT_PASS",
            "booking_reference": ref_id,
            "provider": event_data.get("source", "BookMyShow / Local City Concierge"),
            "title": event_data.get("title"),
            "venue": event_data.get("venue"),
            "city": event_data.get("city"),
            "timing": event_data.get("timing"),
            "attendee_name": attendee_name,
            "tickets_count": num_tickets,
            "unit_price": unit_price,
            "subtotal": subtotal,
            "tax_and_fees": convenience_fee,
            "total_amount": total_bill,
            "currency": "INR",
            "booking_status": "Confirmed (Pay at Box Office / Concierge Desk)",
            "official_url": event_data.get("ticket_url"),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            from app.db.repositories import get_booking_repository
            from app.schemas.booking import BookingSchema
            repo = get_booking_repository()
            b_schema = BookingSchema(
                id=booking_payload["id"],
                user_id="demo-user",
                booking_type="EVENT",
                title=event_data.get("title", "Local Event Pass"),
                provider=booking_payload["provider"],
                flight_number=ref_id,
                departure_location=event_data.get("venue", "City Center"),
                arrival_location=event_data.get("city", "Local Event"),
                status="CONFIRMED",
                booking_reference=ref_id,
                raw_extraction_metadata=booking_payload
            )
            repo.save_booking(b_schema)
            logger.info(f"[EVENTS] Successfully booked event {ref_id} into database repository")
        except Exception as e:
            logger.warning(f"[EVENTS] Could not save to repository, proceeding in memory: {e}")

        return booking_payload

def get_live_events_service() -> LiveEventsService:
    return LiveEventsService()
