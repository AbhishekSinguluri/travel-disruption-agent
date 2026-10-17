from typing import List, Dict, Any
from app.services.providers import get_places_provider, get_routes_provider
from app.schemas.places import PlaceCandidate
from app.services.llm import _call_groq_json
from pydantic import BaseModel, Field
import json
import logging

logger = logging.getLogger(__name__)

class GeneratedAlternative(BaseModel):
    id: str = Field(description="A unique id string like 'alt-1'")
    name: str = Field(description="The genuine name of the real place")
    category: str = Field(description="Category of the place")
    distance_meters: int = Field(description="Estimated distance in meters")
    travel_time_mins: int = Field(description="Estimated travel time in minutes")
    why_recommended: str = Field(description="Why this is recommended")
    latitude: float = Field(description="Estimated latitude of the place")
    longitude: float = Field(description="Estimated longitude of the place")

class GeneratedAlternativesList(BaseModel):
    candidates: List[GeneratedAlternative]

def search_recovery_candidates(lat: float, lng: float, prefs: Dict[str, Any], disruption_type: str = "NORMAL_DELAY") -> List[Dict[str, Any]]:
    logger.info("[AGENT] SEARCHING CANDIDATES VIA LLM")
    categories = prefs.get("categories", ["Indoor" if disruption_type == "WEATHER_DISRUPTION" else "Nearby"])
    
    system_prompt = "You are a travel assistant for Hyderabad, India. The user needs alternative places due to a disruption."
    user_prompt = f"Disruption: {disruption_type}. We are currently near lat: {lat}, lng: {lng}. We need 2 genuine, real-world places in Hyderabad that match these categories: {categories}. Generate realistic estimated distances and travel times."
    
    result = _call_groq_json(system_prompt, user_prompt, GeneratedAlternativesList)
    if result and result.candidates:
        candidates = [c.model_dump() for c in result.candidates]
        logger.info(f"[AGENT] Final candidates from LLM: {candidates}")
        return candidates
    
    # Fallback if LLM fails
    return [{
        "id": "alt-fallback-1",
        "name": "Salar Jung Museum (Indoor)",
        "category": "Indoor Attraction",
        "distance_meters": 3000,
        "travel_time_mins": 15,
        "why_recommended": "Since it's raining, this indoor museum is a much better option to stay dry.",
        "latitude": 17.37,
        "longitude": 78.48
    }]
