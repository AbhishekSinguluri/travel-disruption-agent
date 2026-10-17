import uuid
import logging
from typing import Dict, Any
from app.services.providers import get_places_provider

logger = logging.getLogger(__name__)

def get_destination_coords(dest: str):
    import requests, time
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": dest, "format": "json", "limit": 1}
        headers = {"User-Agent": "TravelAgentCapstone/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
        time.sleep(1)
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
        
    # Strip time markers to see if it's just generic (e.g. "Lunch at 10:00 PM")
    stripped_time = re.sub(r'\b(at|around|about|time|pm|am|\d{1,2}(:\d{2})?)\b', '', name_lower).strip(" ,-")
    if stripped_time in generic_words:
        return None

    # Clean the search query if it contains a generic prefix like "Lunch at "
    search_query = name
    clean_match = re.search(r'\b(?:lunch|dinner|breakfast|snack|shopping|explore)\s+(?:at|in|near)?\s*(.+)', name_lower)
    if clean_match and clean_match.group(1):
        # We found the actual place name
        # use original case for the place name
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
            
            c_stop = {
                "id": stop.get("id") or f"stop-{trip_id}-{day_idx}-{stop_idx}",
                "title": stop.get("title", "Activity"),
                "category": stop.get("category", "Activity"),
                "location_name": loc_name,
                "address": place.address if place else None,
                "latitude": place.latitude if place else None,
                "longitude": place.longitude if place else None,
                "place_id": place.id if place else None,
                "opening_hours": place.opening_hours if (place and hasattr(place, "opening_hours")) else ({"open": "09:30", "close": "17:30"} if place else None),
                "current_status": place.current_status if place else None,
                "date": stop.get("date", c_day["date"]),
                "start_time": stop.get("start_time", ""),
                "end_time": stop.get("end_time", ""),
                "duration_minutes": stop.get("duration_minutes", 60),
                "status": stop.get("status", "UPCOMING"),
                "notes": stop.get("notes", ""),
                "reservation_info": stop.get("reservation_info", ""),
                "source": place.source if place else "user"
            }
                
            c_day["stops"].append(c_stop)
            stop_idx += 1
            
        canonical["days"].append(c_day)
        day_idx += 1
        
    return canonical
