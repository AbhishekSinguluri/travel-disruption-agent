import uuid
import logging
from typing import Dict, Any
from app.services.providers import get_places_provider

logger = logging.getLogger(__name__)

DESTINATION_CACHE = {
    "hyderabad": (17.3850, 78.4867),
    "alleppey": (9.4981, 76.3388),
    "alappuzha": (9.4981, 76.3388),
    "kerala": (9.9312, 76.2673),
    "kochi": (9.9312, 76.2673),
    "cochin": (9.9312, 76.2673),
    "munnar": (10.0889, 77.0595),
    "wayanad": (11.6854, 76.1320),
    "delhi": (28.6139, 77.2090),
    "new delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "jaipur": (26.9124, 75.7873),
    "goa": (15.2993, 74.1240),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "varanasi": (25.3176, 82.9739),
    "agra": (27.1767, 78.0081),
    "rome": (41.9028, 12.4964),
    "paris": (48.8566, 2.3522),
    "tokyo": (35.6762, 139.6503),
    "london": (51.5074, -0.1278),
    "florence": (43.7696, 11.2558),
    "venice": (45.4408, 12.3155),
    "amsterdam": (52.3676, 4.9041),
}

def get_destination_coords(dest: str):
    if not dest:
        return (17.3850, 78.4867)
    lower = dest.lower().strip()
    for key, coords in DESTINATION_CACHE.items():
        if key in lower:
            return coords

    import requests, time
    try:
        url = "https://nominatim.openstreetmap.org/search"
        q = dest if any(w in lower for w in ["india", "italy", "france", "uk", "usa", "japan"]) else f"{dest}, India"
        params = {"q": q, "format": "json", "limit": 1}
        headers = {"User-Agent": "TravelAgentCapstone/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
        time.sleep(0.5)
    except Exception as e:
        logger.error(f"Geocoding failed for {dest}: {e}")
    return 17.3850, 78.4867

def resolve_location(name: str, category: str, city_context: str):
    import re
    
    # Generic stops that do not contain a concrete location name
    generic_words = {"lunch", "dinner", "breakfast", "snack", "hotel", "shopping", "restaurant", "airport", "cafe", "food", "free time", "transit", "travel", "rest", "explore nearby", "airport transfer", "nearby restaurant"}
    
    if not name:
        return None
        
    name_lower = name.lower()
    
    # Exact match with generic word means it's definitely generic
    if name_lower in generic_words:
        return None

    # Phrases like "lunch around ...", "dinner around ..." where it indicates wandering/generic area
    if re.search(r'\b(lunch|dinner|breakfast|snack|shopping|food)\s+(around|near)\b', name_lower):
        return None
        
    # Strip time markers to see if it's just generic (e.g. "Lunch at 10:00 PM")
    stripped_time = re.sub(r'\b(at|around|about|time|pm|am|\d{1,2}(:\d{2})?)\b', '', name_lower).strip(" ,-")
    if stripped_time in generic_words:
        return None

    # Special handling for Old City in Hyderabad
    if "old city" in name_lower and ("hyderabad" in city_context.lower() or not city_context):
        from app.schemas.places import PlaceCandidate
        return PlaceCandidate(
            id="hyd-old-city",
            name="Old City",
            address="Old City, Hyderabad, Telangana, India",
            latitude=17.3616,
            longitude=78.4746,
            category="Food",
            source="curated"
        )

    # Clean the search query if it contains a generic prefix like "Lunch at "
    search_query = name
    clean_match = re.search(r'\b(?:lunch|dinner|breakfast|snack|shopping|explore)\s+(?:at|in|near)?\s*(.+)', name_lower)
    if clean_match and clean_match.group(1):
        start_idx = name_lower.find(clean_match.group(1))
        search_query = name[start_idx:]

    provider = get_places_provider()
    place = provider.search_place_by_text(search_query, city_context)
    return place

def build_canonical_trip(extracted: Dict[str, Any]) -> Dict[str, Any]:
    trip_id = extracted.get("id") or str(uuid.uuid4())
    
    title = extracted.get("name")
    dest = extracted.get("destination", "Unknown Destination")
    
    if not title or title.lower() in ["mock imported trip", "unknown"]:
        if dest and dest.lower() != "unknown":
            title = f"{dest} Trip"
        else:
            title = "Untitled Trip"
            
    base_lat, base_lng = get_destination_coords(dest)

    canonical = {
        "id": trip_id,
        "name": title,
        "destination": dest,
        "start_date": extracted.get("start_date", "2026-01-01"),
        "end_date": extracted.get("end_date", "2026-01-01"),
        "days": [],
        "status": "PLANNED"
    }
    
    day_idx = 1
    for day in extracted.get("days", []):
        c_day = {
            "id": f"day-{day_idx}",
            "date": day.get("date", f"Day {day_idx}"),
            "stops": []
        }
        
        stop_idx = 1
        for stop in day.get("stops", []):
            loc_name = stop.get("location_name") or stop.get("title", "")
            place = resolve_location(loc_name, stop.get("category", ""), dest)
            
            # Check if place is valid and close to destination
            valid_place = False
            if place and place.latitude and place.longitude:
                import math
                dist = math.hypot(place.latitude - base_lat, place.longitude - base_lng) * 111.0 # approx km
                if dist <= 80:
                    valid_place = True

            if valid_place:
                lat = place.latitude
                lng = place.longitude
            elif place is None:
                lat = None
                lng = None
            else:
                lat = round(base_lat + (stop_idx * 0.005 - 0.012), 6)
                lng = round(base_lng + (stop_idx * 0.004 - 0.010), 6)

            c_stop = {
                "id": stop.get("id") or f"stop-{trip_id}-{day_idx}-{stop_idx}",
                "title": stop.get("title", "Activity"),
                "category": stop.get("category", "Activity"),
                "location_name": loc_name,
                "address": place.address if valid_place else f"{loc_name}, {dest}",
                "latitude": lat,
                "longitude": lng,
                "place_id": place.id if valid_place else None,
                "opening_hours": place.opening_hours if (valid_place and hasattr(place, "opening_hours")) else ({"open": "09:30", "close": "17:30"} if valid_place else None),
                "current_status": place.current_status if valid_place else None,
                "date": stop.get("date", c_day["date"]),
                "start_time": stop.get("start_time", ""),
                "end_time": stop.get("end_time", ""),
                "duration_minutes": stop.get("duration_minutes", 60),
                "status": stop.get("status", "UPCOMING"),
                "notes": stop.get("notes", ""),
                "reservation_info": stop.get("reservation_info", ""),
                "source": place.source if valid_place else "destination_context"
            }
                
            c_day["stops"].append(c_stop)
            stop_idx += 1
            
        canonical["days"].append(c_day)
        day_idx += 1
        
    return canonical
