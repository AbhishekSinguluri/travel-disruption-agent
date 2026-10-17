from typing import Dict, Any, List
import datetime

class TravelCompanionService:
    def __init__(self, trip: Dict[str, Any]):
        self.trip = trip
        
    def _all_stops(self) -> List[Dict[str, Any]]:
        stops = []
        for d in self.trip.get("days", []):
            stops.extend(d.get("stops", []))
        return stops

    def get_current_stop(self) -> Dict[str, Any]:
        for s in self._all_stops():
            if s.get("status") in ["ARRIVED", "IN_PROGRESS"]:
                return s
        return None

    def get_next_stop(self) -> Dict[str, Any]:
        for s in self._all_stops():
            if s.get("status") == "UPCOMING":
                return s
        return None
        
    def get_remaining_stops(self) -> List[Dict[str, Any]]:
        return [s for s in self._all_stops() if s.get("status") == "UPCOMING"]

    def get_opening_hours(self, stop_id: str) -> Dict[str, Any]:
        for s in self._all_stops():
            if s.get("id") == stop_id:
                return s.get("opening_hours")
        return None
        
    def generate_warnings(self) -> List[str]:
        warnings = []
        next_s = self.get_next_stop()
        if next_s and next_s.get("opening_hours"):
            close_time = next_s["opening_hours"].get("close")
            if close_time == "17:30":
                warnings.append(f"{next_s['title']} closes in 25 minutes and you haven't checked in yet.")
        return warnings
