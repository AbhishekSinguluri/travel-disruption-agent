from typing import List, Dict, Any, Optional
import os
import re
import json
import logging
from pydantic import BaseModel, Field
from app.services.llm import _call_groq_json
from app.services.providers import get_places_provider, get_routes_provider

logger = logging.getLogger(__name__)

class GeneratedAlternative(BaseModel):
    id: str = Field(description="A unique id string like 'alt-1', 'alt-2'")
    name: str = Field(description="The genuine, real-world name of the real place")
    category: str = Field(description="Category of the place, e.g. Indoor Museum, Art Gallery, Palace Interior, Cafe, Scenic Viewpoint, Cultural Center")
    distance_meters: int = Field(description="Estimated distance in meters from current stop (e.g. 800 to 4000 meters)")
    travel_time_mins: int = Field(description="Estimated travel time in minutes (e.g. 5 to 25 mins)")
    why_recommended: str = Field(description="Detailed explanation of why this specific place is an excellent alternative")
    latitude: float = Field(description="Estimated latitude of the place in this destination city")
    longitude: float = Field(description="Estimated longitude of the place in this destination city")

class GeneratedAlternativesList(BaseModel):
    candidates: List[GeneratedAlternative]

# Curated fallback knowledge base per city for offline / zero-network resilience
CURATED_CITY_ALTERNATIVES = {
    "jaipur": {
        "indoor": [
            {
                "name": "Albert Hall Museum",
                "category": "Indoor Museum",
                "why_recommended": "Jaipur's premier Indo-Saracenic museum housing stunning art, carpets, and sculptures, completely sheltered from the rain.",
                "lat": 26.9118, "lng": 75.8195, "dist": 2800, "time": 12
            },
            {
                "name": "City Palace Mubarak Mahal & Armoury Museum",
                "category": "Palace Interior",
                "why_recommended": "Opulent covered royal galleries, historic textile halls, and armoury exhibits perfect for staying dry while exploring heritage.",
                "lat": 26.9258, "lng": 75.8237, "dist": 3200, "time": 15
            },
            {
                "name": "Anokhi Museum of Hand Printing",
                "category": "Heritage Museum",
                "why_recommended": "A beautifully restored indoor haveli museum near Amer showcasing traditional Rajasthani block printing and live artisan demos.",
                "lat": 26.9892, "lng": 75.8504, "dist": 1400, "time": 8
            },
            {
                "name": "Jawahar Kala Kendra (JKK)",
                "category": "Art & Cultural Center",
                "why_recommended": "Multi-arts centre designed by Charles Correa with covered art galleries, theater, and indoor cultural exhibits.",
                "lat": 26.8778, "lng": 75.8078, "dist": 4500, "time": 18
            }
        ],
        "general": [
            {
                "name": "Panna Meena ka Kund",
                "category": "Historic Stepwell",
                "why_recommended": "An iconic 16th-century geometric stepwell just minutes away from Amer, ideal for a quick scenic visit that fits the schedule.",
                "lat": 26.9859, "lng": 75.8485, "dist": 800, "time": 6
            },
            {
                "name": "Jaigarh Fort & Royal Armory",
                "category": "Historic Fort",
                "why_recommended": "Connected by subterranean passages overlooking the valley, offering spectacular views and massive historical cannons.",
                "lat": 26.9850, "lng": 75.8420, "dist": 1200, "time": 10
            },
            {
                "name": "Hawa Mahal Wind Cafe Viewpoint",
                "category": "Scenic Viewpoint & Cafe",
                "why_recommended": "A quick viewpoint and rooftop cafe overlooking the Palace of Winds, perfect for a refreshing stop without travel delays.",
                "lat": 26.9239, "lng": 75.8267, "dist": 2200, "time": 12
            }
        ]
    },
    "hyderabad": {
        "indoor": [
            {
                "name": "B.M. Birla Science Centre & Planetarium",
                "category": "Science Center & Planetarium",
                "why_recommended": "Top-tier indoor science complex with dinosaur exhibits, interactive physics gallery, and dome planetarium safe from weather.",
                "lat": 17.4042, "lng": 78.4716, "dist": 1500, "time": 7
            },
            {
                "name": "Chowmahalla Palace Durbar Hall & Royal Museum",
                "category": "Palace Interior",
                "why_recommended": "Stunning grand indoor chandeliers, vintage royal car museum, and ceremonial throne rooms that keep you sheltered from rain.",
                "lat": 17.3578, "lng": 78.4717, "dist": 3800, "time": 16
            },
            {
                "name": "Salar Jung Museum",
                "category": "Indoor Museum",
                "why_recommended": "One of India's grandest national museums with 38 indoor galleries of world art, clock tower room, and jade artifacts.",
                "lat": 17.3714, "lng": 78.4804, "dist": 3000, "time": 14
            },
            {
                "name": "Nizam's Museum (Purani Haveli)",
                "category": "Heritage Museum",
                "why_recommended": "Fascinating indoor museum displaying the silver jubilee gifts of the 7th Nizam and historical royal memorabilia.",
                "lat": 17.3616, "lng": 78.4747, "dist": 4200, "time": 18
            }
        ],
        "general": [
            {
                "name": "Lumbini Park & Musical Fountain",
                "category": "Scenic Park & Pier",
                "why_recommended": "A vibrant public park right next to Hussain Sagar Lake with quick boat boarding and garden walkways.",
                "lat": 17.4101, "lng": 78.4739, "dist": 700, "time": 5
            },
            {
                "name": "Qutb Shahi Tombs",
                "category": "Historic Monuments",
                "why_recommended": "A majestic architectural enclave of domed royal tombs and landscaped gardens that provides a relaxed, unhurried detour.",
                "lat": 17.3934, "lng": 78.3957, "dist": 2800, "time": 12
            },
            {
                "name": "Famous Ice Cream & Cafe, Mozamjahi Market",
                "category": "Cafe & Historic Food",
                "why_recommended": "A beloved heritage market food stop for quick artisanal fruit ice cream and Hyderabadi chai without derailing your schedule.",
                "lat": 17.3820, "lng": 78.4750, "dist": 1800, "time": 9
            }
        ]
    },
    "delhi": {
        "indoor": [
            {
                "name": "National Museum, Janpath",
                "category": "National Museum",
                "why_recommended": "India's premier cultural repository spanning 5,000 years of history, sculptures, and miniature paintings in a vast air-conditioned building.",
                "lat": 28.6118, "lng": 77.2193, "dist": 2500, "time": 10
            },
            {
                "name": "National Gallery of Modern Art (NGMA)",
                "category": "Art Gallery",
                "why_recommended": "Housed in the historic Jaipur House at India Gate circle, offering peaceful indoor contemporary art exhibitions safe from the rain.",
                "lat": 28.6102, "lng": 77.2345, "dist": 2200, "time": 9
            },
            {
                "name": "National Crafts Museum & Hastkala Academy",
                "category": "Cultural Craft Museum",
                "why_recommended": "Magnificent indoor folk art galleries, textile pavilions, and craft courtyards celebrating Indian artisans.",
                "lat": 28.6145, "lng": 77.2428, "dist": 3100, "time": 14
            }
        ],
        "general": [
            {
                "name": "Agrasen ki Baoli",
                "category": "Historical Stepwell",
                "why_recommended": "An ancient 108-step reservoir tucked near Connaught Place, offering quick sightseeing and striking photographs.",
                "lat": 28.6258, "lng": 77.2250, "dist": 1100, "time": 6
            },
            {
                "name": "Lodhi Garden & Monuments",
                "category": "Heritage Garden",
                "why_recommended": "Sprawling historical park with 15th-century Sayyid and Lodi tombs, ideal for a swift, scenic walk.",
                "lat": 28.5933, "lng": 77.2197, "dist": 2900, "time": 12
            }
        ]
    }
}

def _clean_destination_name(dest: str, lat: float = None, lng: float = None) -> str:
    if dest:
        # Check if known city name is contained in the string
        dest_lower = dest.lower()
        for city in ["jaipur", "hyderabad", "delhi", "mumbai", "bengaluru", "bangalore", "goa", "chennai", "kolkata", "rome", "paris", "london"]:
            if city in dest_lower:
                return "Bengaluru" if city == "bangalore" else city.title()
        # Clean extra words
        cleaned = re.sub(r'\b(itinerary|trip|tour|day-trip|heritage|stops?|day|plan)\b', '', dest, flags=re.IGNORECASE)
        cleaned = re.sub(r'[\d\-\u2011\u2013\(\),]+', ' ', cleaned).strip()
        if cleaned:
            return cleaned

    # Fallback by coordinates
    if lat is not None and lng is not None:
        if 26.5 <= lat <= 27.5 and 75.0 <= lng <= 76.5:
            return "Jaipur"
        if 28.0 <= lat <= 29.0 and 76.5 <= lng <= 77.8:
            return "Delhi"
        if 17.0 <= lat <= 17.8 and 78.0 <= lng <= 79.0:
            return "Hyderabad"

    return dest.strip() if dest else "Hyderabad"

def _is_place_excluded(place_name: str, excluded_places: List[str]) -> bool:
    if not excluded_places or not place_name:
        return False
    name_clean = re.sub(r'[^\w\s]', '', place_name.lower()).strip()
    for excl in excluded_places:
        if not excl:
            continue
        excl_clean = re.sub(r'[^\w\s]', '', excl.lower()).strip()
        if excl_clean and (excl_clean in name_clean or name_clean in excl_clean):
            return True
    return False

def _generate_fallback_candidates(
    destination: str,
    disruption_type: str,
    lat: float,
    lng: float,
    excluded_places: List[str]
) -> List[Dict[str, Any]]:
    city_key = destination.lower()
    is_weather = disruption_type == "WEATHER_DISRUPTION"
    pool_type = "indoor" if is_weather else "general"

    # Match curated city or pick generic
    matched_city = None
    for k in CURATED_CITY_ALTERNATIVES:
        if k in city_key or city_key in k:
            matched_city = k
            break

    candidates = []
    if matched_city:
        curated_pool = CURATED_CITY_ALTERNATIVES[matched_city].get(pool_type, [])
        # Also try other pool if general was selected
        if not is_weather:
            curated_pool = curated_pool + CURATED_CITY_ALTERNATIVES[matched_city].get("indoor", [])

        routes_provider = get_routes_provider()
        for item in curated_pool:
            if not _is_place_excluded(item["name"], excluded_places):
                travel_mins = item.get("time", 15)
                if routes_provider and hasattr(routes_provider, "calculate_travel_time"):
                    try:
                        c_time = routes_provider.calculate_travel_time((lat, lng), (item.get("lat", lat), item.get("lng", lng)))
                        if c_time:
                            travel_mins = c_time
                    except Exception:
                        pass
                candidates.append({
                    "id": f"alt-{len(candidates) + 1}",
                    "name": item["name"],
                    "category": item["category"],
                    "distance_meters": item.get("dist", 2500),
                    "travel_time_mins": travel_mins,
                    "travel_minutes": travel_mins,
                    "why_recommended": item["why_recommended"],
                    "latitude": item.get("lat", lat or 17.38),
                    "longitude": item.get("lng", lng or 78.48)
                })
            if len(candidates) >= 2:
                break

    # If still not enough candidates, generate generic for the exact destination
    if len(candidates) < 2:
        if is_weather:
            generic_items = [
                {
                    "name": f"{destination} Heritage Museum & Art Gallery",
                    "category": "Indoor Museum",
                    "why_recommended": f"A prime indoor cultural museum in {destination} featuring historic galleries and covered exhibitions to stay completely dry during rain."
                },
                {
                    "name": f"{destination} Royal Palace Indoor Exhibition Hall",
                    "category": "Palace Interior",
                    "why_recommended": f"Magnificent sheltered palace corridors and royal halls in {destination}, offering a cultural escape sheltered from bad weather."
                }
            ]
        else:
            generic_items = [
                {
                    "name": f"{destination} Historic Gate & Viewpoint",
                    "category": "Scenic Viewpoint",
                    "why_recommended": f"A historic architectural landmark in {destination} right nearby, ideal for a memorable photo-stop that fits the schedule."
                },
                {
                    "name": f"{destination} Heritage Promenade & Cafe",
                    "category": "Heritage Cafe & Walk",
                    "why_recommended": f"A quick scenic spot and artisan cafe in {destination} that minimizes travel delay while keeping your itinerary lively."
                }
            ]

        for gen in generic_items:
            if not _is_place_excluded(gen["name"], excluded_places):
                candidates.append({
                    "id": f"alt-{len(candidates) + 1}",
                    "name": gen["name"],
                    "category": gen["category"],
                    "distance_meters": 2000 + len(candidates) * 500,
                    "travel_time_mins": 15,
                    "travel_minutes": 15,
                    "why_recommended": gen["why_recommended"],
                    "latitude": (lat or 17.38) + 0.008 * (len(candidates) + 1),
                    "longitude": (lng or 78.48) + 0.008 * (len(candidates) + 1)
                })
            if len(candidates) >= 2:
                break

    return candidates

def search_recovery_candidates(
    lat: float, 
    lng: float, 
    prefs: Dict[str, Any] = None, 
    disruption_type: str = "NORMAL_DELAY",
    destination: str = "",
    current_stop_name: str = "",
    excluded_places: List[str] = None
) -> List[Dict[str, Any]]:
    prefs = prefs or {}
    excluded_places = [p for p in (excluded_places or []) if p]

    # Resolve destination
    raw_dest = destination or prefs.get("destination") or ""
    clean_dest = _clean_destination_name(raw_dest, lat, lng)
    
    # Resolve current stop name
    stop_name = current_stop_name or prefs.get("current_stop_name") or prefs.get("affected_stop_name") or "Current Location"
    if stop_name and stop_name not in excluded_places:
        excluded_places.append(stop_name)

    is_weather = (disruption_type == "WEATHER_DISRUPTION")

    logger.info(f"[AGENT] SEARCHING CANDIDATES: dest='{clean_dest}', stop='{stop_name}', type='{disruption_type}', excluded={excluded_places}")

    # Build prompt instructions based on disruption type
    if is_weather:
        rule_desc = (
            f"CRITICAL REQUIREMENT - WEATHER DISRUPTION (RAINING/BAD WEATHER):\n"
            f"It is heavily raining in {clean_dest}. The traveler's planned activity at '{stop_name}' is disrupted.\n"
            "You MUST suggest EXCLUSIVELY INDOOR places (e.g. covered museums, indoor art galleries, palace interior halls, indoor science centres, covered cultural halls, indoor tea houses/cafes).\n"
            "DO NOT suggest outdoor lakes, open parks, gardens, outdoor forts, or open walking tracks.\n"
            "Each suggestion's 'why_recommended' MUST clearly explain why it is a fantastic indoor escape from the rain while exploring local culture."
        )
    else:
        rule_desc = (
            f"NORMAL DELAY DISRUPTION (+15 min delay / time-slip):\n"
            f"The traveler is running behind schedule near '{stop_name}' in {clean_dest}. It is NOT raining.\n"
            "You can freely recommend BOTH outdoor and indoor places (e.g. nearby scenic viewpoints, historic stepwells, gates, gardens, street bazaars, cafes) that are close by and quick to visit without blowing the schedule.\n"
            "Each suggestion's 'why_recommended' MUST explain why it fits the remaining schedule and minimizes delay."
        )

    system_prompt = (
        f"You are ROAM's autonomous agentic travel guide specializing in {clean_dest}. "
        f"You provide genuine, real-world, famous alternative attractions that actually exist in {clean_dest}. "
        f"Never suggest places from other cities or states (for example, if the trip is in Jaipur, all places MUST be in Jaipur, Rajasthan!). "
        "Ensure realistic coordinates, distance (meters), and travel time (minutes) from the current stop."
    )

    user_prompt = (
        f"City / Destination: {clean_dest}\n"
        f"Current Disrupted Stop: '{stop_name}' (approx lat: {lat}, lng: {lng})\n"
        f"Disruption Type: {disruption_type}\n"
        f"{rule_desc}\n\n"
        f"EXCLUSION LIST: Do NOT suggest any of these places, as they are already planned or already visited in this trip: {', '.join(excluded_places) if excluded_places else 'None'}.\n\n"
        f"Generate 2 to 3 unique, genuine real-world alternatives in {clean_dest} that are NOT in the exclusion list. "
        "Give realistic distances (meters) and travel times (mins) from the disrupted stop."
    )

    result = _call_groq_json(system_prompt, user_prompt, GeneratedAlternativesList)
    if result and result.candidates:
        valid_candidates = []
        for i, c in enumerate(result.candidates):
            c_dict = c.model_dump()
            # Verify candidate is not in exclusion list
            if _is_place_excluded(c_dict["name"], excluded_places):
                continue
            # Ensure travel_minutes compatibility
            c_dict["id"] = f"alt-{len(valid_candidates) + 1}"
            c_dict["travel_minutes"] = c_dict.get("travel_time_mins", 15)
            valid_candidates.append(c_dict)

        if len(valid_candidates) >= 2:
            logger.info(f"[AGENT] Successfully generated {len(valid_candidates)} candidates via LLM for {clean_dest}")
            return valid_candidates

    logger.warning(f"[AGENT] Using dynamic fallback for {clean_dest} ({disruption_type})")
    fallback = _generate_fallback_candidates(clean_dest, disruption_type, lat, lng, excluded_places)
    return fallback

