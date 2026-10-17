import os
from typing import Protocol, List, Dict
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

        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {"q": f"{query}, {city_context}", "format": "json", "limit": 3}
            headers = {"User-Agent": "TravelAgentCapstone/1.0"}
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    place = data[0]
                    return PlaceCandidate(
                        id=str(place.get("place_id", place.get("osm_id", "mock-1"))),
                        name=query,
                        address=place.get("display_name"),
                        latitude=float(place.get("lat")),
                        longitude=float(place.get("lon")),
                        category="Activity",
                        source="nominatim"
                    )
            time.sleep(1)
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
