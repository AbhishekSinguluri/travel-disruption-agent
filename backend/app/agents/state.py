from typing import TypedDict, List, Optional, Dict, Any

class TripState(TypedDict):
    trip_id: str
    trip_data: Optional[Dict[str, Any]]
    disruption_input: Optional[Dict[str, Any]]
    active_disruption: Optional[Dict[str, Any]]
    impact_analysis: Optional[Dict[str, Any]]
    user_preferences: Optional[Dict[str, Any]]
    candidate_alternatives: List[Dict[str, Any]]
    selected_candidate_id: Optional[str]
    revised_itinerary: Optional[List[Dict[str, Any]]]
    validation_errors: List[str]
