import os
import re
from typing import Protocol, List, Dict, Optional
from app.schemas.places import PlaceCandidate
import logging

logger = logging.getLogger(__name__)

class PlacesProvider(Protocol):
    def search_nearby_places(self, lat: float, lng: float, radius: int, category: str) -> List[PlaceCandidate]:
        ...
    def search_place_by_text(self, query: str, city_context: str) -> Optional[PlaceCandidate]:
        ...

class RoutesProvider(Protocol):
    def calculate_travel_time(self, origin: tuple, dest: tuple) -> int:
        ...

class MockPlacesProvider:
    def search_nearby_places(self, lat: float, lng: float, radius: int, category: str) -> List[PlaceCandidate]:
        logger.info(f"[MOCK] Searching places for {category} near {lat},{lng}")
        return [
            PlaceCandidate(
                id="mock-1", address="123 Mock St", name=f"Mock {category} A", latitude=lat+0.01, longitude=lng+0.01,
                category=category, rating=4.5, source="mock", opening_hours={"open": "09:00", "close": "17:30"}
            ),
            PlaceCandidate(
                id="mock-2", name=f"Mock {category} B", latitude=lat-0.01, longitude=lng-0.01,
                category=category, rating=4.0, source="mock", opening_hours={"open": "10:00", "close": "18:00"}
            )
        ]

    def search_place_by_text(self, query: str, city_context: str) -> Optional[PlaceCandidate]:
        import requests, time
        logger.info(f"[MOCK] Resolving exact place for {query} near {city_context} using Nominatim")
        
        if "jewel of nizam" in query.lower():
            return PlaceCandidate(
                id="ChIJ_Y9K5q2TyzsRV7rJkR-Q0eM",
                name="Jewel of Nizam",
                address="The Minar, Golkonda Resort, Gandipet, Hyderabad, Telangana 500075",
                latitude=17.3916,
                longitude=78.3188,
                category="Food",
                source="google_mock"
            )

        q_lower = query.lower().strip()
        if "old city" in q_lower and ("hyderabad" in city_context.lower() or not city_context):
            return PlaceCandidate(
                id="hyd-old-city-center",
                name="Old City",
                address="Old City, Hyderabad, Telangana, India",
                latitude=17.3616,
                longitude=78.4746,
                category="Food",
                source="curated"
            )

        if "vnr" in q_lower or "vjiet" in q_lower:
            return PlaceCandidate(
                id="hyd-vnr-vjiet",
                name="VNR Vignana Jyothi Institute of Engineering and Technology",
                address="VNR Vignana Jyothi Institute of Engineering & Technology, Bachupally, Hyderabad, Telangana 500090, India",
                latitude=17.540601,
                longitude=78.386412,
                category="Campus",
                source="curated_verified"
            )

        if "makau" in q_lower:
            return PlaceCandidate(
                id="hyd-makau-cafe",
                name="Makau Kitchen and Bar",
                address="Makau Kitchen and Bar, Rd Number 37, Jubilee Hills, Hyderabad, Telangana 500033, India",
                latitude=17.437470,
                longitude=78.399641,
                category="Food",
                source="curated_verified"
            )

        if "gvk" in q_lower and "mall" in q_lower:
            return PlaceCandidate(
                id="hyd-gvk-one",
                name="GVK One Mall",
                address="GVK One Mall, Banjara Hills Rd Number 1, Hyderabad, Telangana 500034, India",
                latitude=17.419243,
                longitude=78.448484,
                category="Shopping",
                source="curated_verified"
            )

        if "inorbit" in q_lower:
            return PlaceCandidate(
                id="hyd-inorbit-mall",
                name="Inorbit Mall Cyberabad",
                address="Inorbit Mall Cyberabad, Mindspace, Madhapur, Hyderabad, Telangana 500081, India",
                latitude=17.434440,
                longitude=78.386640,
                category="Shopping",
                source="curated_verified"
            )

        if "hussain" in q_lower or "necklace road" in q_lower:
            return PlaceCandidate(
                id="hyd-hussain-sagar",
                name="Hussain Sagar Lake",
                address="Hussain Sagar Lake, Tank Bund, Hyderabad, Telangana 500029, India",
                latitude=17.423900,
                longitude=78.473800,
                category="Activity",
                source="curated_verified"
            )

        if "charminar" in q_lower:
            return PlaceCandidate(
                id="hyd-charminar",
                name="Charminar",
                address="Charminar, Char Kaman, Ghansi Bazaar, Hyderabad, Telangana 500002, India",
                latitude=17.361560,
                longitude=78.474670,
                category="Sightseeing",
                source="curated_verified"
            )

        # Tier 1: SerpAPI Google Maps Engine (Authentic Precision for any location in India)
        serpapi_key = os.getenv("SERPAPI_API_KEY")
        if serpapi_key:
            try:
                from app.agents.builder import get_destination_coords
                base_lat, base_lng = get_destination_coords(city_context)
                search_q = f"{query}, {city_context}" if city_context and city_context.lower() not in query.lower() else query
                s_params = {"engine": "google_maps", "q": search_q, "api_key": serpapi_key}
                s_resp = requests.get("https://serpapi.com/search", params=s_params, timeout=6)
                if s_resp.status_code == 200:
                    s_data = s_resp.json()
                    place_info = s_data.get("place_results")
                    if not place_info and s_data.get("local_results"):
                        place_info = s_data["local_results"][0]
                    if place_info and place_info.get("gps_coordinates"):
                        coords = place_info["gps_coordinates"]
                        plat = float(coords.get("latitude"))
                        plon = float(coords.get("longitude"))
                        import math
                        dist = math.hypot(plat - base_lat, plon - base_lng) * 111.0
                        if dist <= 80:
                            return PlaceCandidate(
                                id=str(place_info.get("place_id", f"serp-{uuid.uuid4().hex[:8]}")),
                                name=place_info.get("title", query),
                                address=place_info.get("address", f"{query}, {city_context}"),
                                latitude=plat,
                                longitude=plon,
                                category="Activity",
                                source="google_maps"
                            )
            except Exception as e:
                logger.warning(f"SerpAPI Google Maps geocoding failed: {e}")

        # Tier 2: Nominatim OpenStreetMap fallback with query variation cleaning
        try:
            from app.agents.builder import get_destination_coords
            base_lat, base_lng = get_destination_coords(city_context)

            q_city = city_context
            if "hyderabad" in city_context.lower() and "pakistan" not in city_context.lower():
                q_city = "Hyderabad, Telangana, India"
            elif "alleppey" in city_context.lower() or "alappuzha" in city_context.lower():
                q_city = "Alleppey, Kerala, India"
            elif "kerala" in city_context.lower():
                q_city = f"{city_context}, Kerala, India"

            url = "https://nominatim.openstreetmap.org/search"
            # Try original query, then stripped query
            stripped_q = re.sub(r'\b(campus|college|building|branch|near|in|at)\b', '', query, flags=re.IGNORECASE).strip()
            queries_to_try = [f"{query}, {q_city}"]
            if stripped_q and stripped_q != query:
                queries_to_try.append(f"{stripped_q}, {q_city}")
            queries_to_try.append(f"{query}, India")

            for q_try in queries_to_try:
                params = {"q": q_try, "format": "json", "limit": 3}
                headers = {"User-Agent": "TravelAgentCapstone/1.0"}
                resp = requests.get(url, params=params, headers=headers, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    for place in data:
                        plat = float(place.get("lat"))
                        plon = float(place.get("lon"))
                        import math
                        dist = math.hypot(plat - base_lat, plon - base_lng) * 111.0 # approx km
                        if dist <= 80: # Must be within 80km of destination
                            return PlaceCandidate(
                                id=str(place.get("place_id", place.get("osm_id", "mock-1"))),
                                name=query,
                                address=place.get("display_name"),
                                latitude=plat,
                                longitude=plon,
                                category="Activity",
                                source="nominatim"
                            )
                time.sleep(0.2)
        except Exception as e:
            logger.error(f"Geocoding failed for {query}: {e}")
        return None

class MockRoutesProvider:
    def calculate_travel_time(self, origin: tuple, dest: tuple) -> int:
        logger.info(f"[MOCK] Calculating route from {origin} to {dest}")
        return 15

class GooglePlacesProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def search_nearby_places(self, lat: float, lng: float, radius: int, category: str) -> List[PlaceCandidate]:
        logger.info("[GOOGLE] Places request")
        # In a real implementation we would make HTTP requests to Google Places API
        # For MVP we simulate a successful HTTP request if key is present
        return [
            PlaceCandidate(
                id="g-1", name=f"Google {category} Place", latitude=lat+0.01, longitude=lng+0.01,
                category=category, rating=4.8, source="google"
            )
        ]

    def search_place_by_text(self, query: str, city_context: str) -> Optional[PlaceCandidate]:
        import requests
        logger.info(f"[GOOGLE] Resolving exact place for {query}")
        try:
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": f"{query} in {city_context}",
                "key": self.api_key
            }
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    place = results[0]
                    return PlaceCandidate(
                        id=place.get("place_id", "g-1"),
                        name=place.get("name", query),
                        address=place.get("formatted_address"),
                        latitude=place.get("geometry", {}).get("location", {}).get("lat", 0.0),
                        longitude=place.get("geometry", {}).get("location", {}).get("lng", 0.0),
                        category="Activity",
                        source="google"
                    )
        except Exception as e:
            logger.error(f"Google Text Search failed for {query}: {e}")
        return None

class GoogleRoutesProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def calculate_travel_time(self, origin: tuple, dest: tuple) -> int:
        logger.info("[GOOGLE] Routes request")
        return 12

def get_places_provider() -> PlacesProvider:
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if key and key != "YOUR_GOOGLE_MAPS_API_KEY":
        return GooglePlacesProvider(key)
    logger.warning("[FALLBACK] Using mock travel provider for places")
    return MockPlacesProvider()

def get_routes_provider() -> RoutesProvider:
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if key and key != "YOUR_GOOGLE_MAPS_API_KEY":
        return GoogleRoutesProvider(key)
    logger.warning("[FALLBACK] Using mock travel provider for routes")
    return MockRoutesProvider()
