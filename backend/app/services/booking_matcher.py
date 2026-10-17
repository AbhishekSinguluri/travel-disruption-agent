import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

def match_booking_to_trip(monitor_state: dict, trips: List[dict]) -> Optional[dict]:
    """
    Attempts to deterministically match a booking/monitor to a canonical trip.
    
    Matching rules in order of precedence:
    1. Explicit trip_id in monitor_state
    2. PNR / Booking reference match in any of the trip's stops
    3. Operator/airline + service/flight number + travel date match
    4. Origin/destination + date (fallback)
    
    Returns the matched trip dictionary if exactly one reliable match is found.
    Returns None if no match is found, or if multiple ambiguous matches exist.
    """
    if not trips:
        logger.info("No trips available for matching.")
        return None
        
    # 1. Explicit trip_id match
    explicit_trip_id = monitor_state.get("trip_id")
    if explicit_trip_id:
        matched = [t for t in trips if t.get("id") == explicit_trip_id]
        if len(matched) == 1:
            return matched[0]
            
    # Prepare booking details
    booking_ref = monitor_state.get("booking_reference", "")
    booking_ref = booking_ref.strip().lower() if booking_ref else ""
    
    operator = monitor_state.get("provider", "")
    operator = operator.strip().lower() if operator else ""
    
    service_number = monitor_state.get("service_number", "")
    service_number = service_number.strip().lower() if service_number else ""
    
    travel_date = monitor_state.get("travel_date", "")
    travel_date = travel_date.strip() if travel_date else ""
    
    if travel_date and "T" in travel_date:
        travel_date_prefix = travel_date.split("T")[0]
    else:
        travel_date_prefix = travel_date

    def normalize(val: str) -> str:
        return val.strip().lower() if isinstance(val, str) else ""
        
    candidates = []
    
    for trip in trips:
        matched_this_trip = False
        
        # We need to search through the trip's stops
        days = trip.get("days", [])
        for day in days:
            for stop in day.get("stops", []):
                # 2. PNR / Booking Reference Match
                stop_ref = normalize(stop.get("booking_reference", ""))
                if booking_ref and stop_ref and booking_ref == stop_ref:
                    matched_this_trip = True
                    break
                    
                # 3. Operator + Service Number Match
                stop_title = normalize(stop.get("title", ""))
                # If operator and service number are found in the title (e.g., "Air India AI 123")
                if operator and service_number:
                    if operator in stop_title and service_number in stop_title:
                        matched_this_trip = True
                        break
                elif service_number and service_number in stop_title:
                    matched_this_trip = True
                    break
                    
            if matched_this_trip:
                break
                
        # 4. Global fallback: check if trip title contains origin/destination
        if not matched_this_trip:
            trip_title = normalize(trip.get("destination", trip.get("name", "")))
            dest = normalize(monitor_state.get("destination", ""))
            if dest and dest in trip_title:
                start_date = normalize(trip.get("start_date", ""))
                if travel_date_prefix and start_date:
                    if travel_date_prefix == start_date:
                        matched_this_trip = True
                else:
                    matched_this_trip = True
                    
        if matched_this_trip:
            candidates.append(trip)
            
    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) > 1:
        logger.warning(f"Ambiguous matching: found {len(candidates)} trips for monitor {monitor_state.get('monitor_id')}")
        return None
    else:
        logger.info(f"No matching trip found for monitor {monitor_state.get('monitor_id')}")
        return None
