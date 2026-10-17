from app.schemas.disruption import RecoveryCandidate

def run_recovery_workflow(disruption_type: str, affected_stop_id: str, preferences: dict = None):
    # Mock implementation of LangGraph logic
    impact = {
        "affected_stop_id": affected_stop_id,
        "message": "Salar Jung Museum visit may be affected by heavy rain. Your 17:00 shopping plan is still feasible."
    }
    
    candidates = []
    if preferences:
        # Generate candidates based on preferences
        candidates = [
            RecoveryCandidate(
                id="cand-1", name="Salar Jung Museum", category="Indoor", description="Famous art museum",
                latitude=17.37, longitude=78.48, distance_km=2.5, travel_minutes=15,
                opening_time="10:00", closing_time="17:00", estimated_duration_minutes=120,
                budget="Low", rating=4.8, weather_suitable=True, next_stop_compatible=True,
                why_recommended="Indoor activity, fits your time window perfectly."
            ),
            RecoveryCandidate(
                id="cand-2", name="Indoor Art Gallery", category="Culture", description="Local contemporary art",
                latitude=17.38, longitude=78.47, distance_km=3.0, travel_minutes=20,
                opening_time="11:00", closing_time="18:00", estimated_duration_minutes=90,
                budget="Medium", rating=4.5, weather_suitable=True, next_stop_compatible=True,
                why_recommended="Close to your next shopping location."
            )
        ]
        
    return {
        "impact": impact,
        "candidates": [c.model_dump() for c in candidates]
    }
    
def run_replanning(trip_id: str, stop_id: str, candidate_id: str, candidates: list):
    from app.db.repositories import get_trip_repository
    repo = get_trip_repository()
    trip = repo.get_trip(trip_id, 'demo-user')
    cand = next((c for c in candidates if c['id'] == candidate_id), None)
    if not cand: return {"success": False, "conflicts": ["Candidate not found"]}
    
    # Replace stop
    for day in trip['days']:
        for stop in day['stops']:
            if stop['id'] == stop_id:
                stop['title'] = cand['name']
                stop['category'] = cand['category']
                stop['location_name'] = cand['name']
                stop['status'] = "REPLACED"
                stop['notes'] = "Replaced due to weather disruption."
    
    update_trip(trip_id, trip)
    return {"success": True, "conflicts": [], "updated_stops": trip['days'][0]['stops']}
