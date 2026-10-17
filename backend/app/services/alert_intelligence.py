import logging
from typing import Optional, Dict, List, Any
from pydantic import BaseModel
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class AgenticAlertSummary(BaseModel):
    id: str
    headline: str
    transport_mode: str
    operator: str
    service_number: str
    route: Dict[str, str]
    journey_context: Dict[str, Any]
    change: Dict[str, Any]
    impact: Dict[str, Any]
    summary: str
    recommendations: List[Dict[str, Any]]
    actions: List[str]
    created_at: str
    delay_minutes: int = 0

def parse_time(time_str: str) -> Optional[datetime]:
    if not time_str:
        return None
    try:
        if "T" in time_str:
            return datetime.fromisoformat(time_str)
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def determine_journey_context(trip: dict, service_number: str) -> dict:
    context = {
        "segment_type": "unknown",
        "overall_journey_type": "domestic",
        "has_connection": False,
        "connection_summary": ""
    }
    if not trip:
        return context

    all_stops = []
    for day in trip.get("days", []):
        all_stops.extend(day.get("stops", []))

    has_intl = False
    is_segment_intl = False

    for i, stop in enumerate(all_stops):
        title = stop.get("title", "").lower()
        if "international" in title or "london" in title or "new york" in title or "dubai" in title or "tokyo" in title:
            has_intl = True
        
        if service_number.lower() in title:
            if "international" in title or "london" in title or "new york" in title or "dubai" in title or "tokyo" in title:
                is_segment_intl = True
            
            if i < len(all_stops) - 1:
                context["has_connection"] = True
                next_stop = all_stops[i+1]
                context["connection_summary"] = f"Connecting to {next_stop.get('title')}"

    context["overall_journey_type"] = "international" if has_intl else "domestic"
    context["segment_type"] = "international" if is_segment_intl else "domestic"

    return context

def process_alert(alert_data: dict, active_trip: Optional[dict] = None) -> AgenticAlertSummary:
    """
    Transform raw booking change into structured intelligence.
    Calculates exact delay from timestamps if available.
    """
    operator = alert_data.get("provider", "")
    service_number = alert_data.get("service_number", "")
    
    # 1. Deterministic Delay Calculation
    delay_minutes = 0
    original_dep = alert_data.get("original_departure")
    updated_dep = alert_data.get("new_departure")
    alert_type = alert_data.get("alert_type", "DELAY")
    reason = alert_data.get("reason")
    
    if original_dep and updated_dep:
        t1 = parse_time(original_dep)
        t2 = parse_time(updated_dep)
        if t1 and t2:
            diff = (t2 - t1).total_seconds() / 60.0
            if diff > 0:
                delay_minutes = int(diff)
    
    if delay_minutes == 0 and alert_data.get("delay_duration"):
        dur_str = str(alert_data.get("delay_duration")).lower()
        if "hour" in dur_str:
            import re
            m = re.search(r"(\d+(?:\.\d+)?)\s*hour", dur_str)
            if m: delay_minutes = int(float(m.group(1)) * 60)
        elif "min" in dur_str:
            import re
            m = re.search(r"(\d+)\s*min", dur_str)
            if m: delay_minutes = int(m.group(1))

    # 2. Journey Context
    journey_context = determine_journey_context(active_trip, service_number)

    # 3. Recommendations & Impact
    if alert_type == "CANCELLATION":
        summary = f"Your service {service_number} has been cancelled."
        if reason: summary += f" Reason: {reason}."
        impact_level = "high"
        recommendations = [
            {"type": "REBOOK", "title": "Check alternative flights", "reason": "Immediate rebooking is required.", "verified": True}
        ]
        headline = f"{operator.upper()} CANCELLATION"
    else:
        if delay_minutes > 0:
            hrs = delay_minutes // 60
            mins = delay_minutes % 60
            delay_str = ""
            if hrs > 0:
                delay_str += f"{hrs} hour{'s' if hrs > 1 else ''}"
            if mins > 0:
                delay_str += f" {mins} min{'s' if mins > 1 else ''}"
            summary = f"Your service {service_number} is delayed by {delay_str.strip()}."
        elif delay_minutes == 0 and not updated_dep:
            summary = f"Your service {service_number} is delayed."
        else:
            summary = f"Your service {service_number} schedule changed."
            
        if reason: summary += f" Reason: {reason}."
        impact_level = "low"
        recommendations = []
        headline = f"{operator.upper()} {alert_type}"

        if delay_minutes > 120:
            summary += f" You have approximately {delay_minutes} minutes of additional free time."
            recommendations.append({
                "type": "REST",
                "title": "Rest at airport/station",
                "reason": "You have enough time to visit a lounge or rest area safely before departure.",
                "verified": True
            })

    if journey_context["has_connection"]:
        impact_level = "high" if delay_minutes > 60 or alert_type == "CANCELLATION" else "medium"
        summary += f" {journey_context['connection_summary']}."
    
    # Format Route
    route = {"origin": alert_data.get("origin") or "Unknown", "destination": alert_data.get("destination") or "Unknown"}

    return AgenticAlertSummary(
        id=f"alert-{datetime.now().timestamp()}",
        headline=headline,
        transport_mode="flight" if "flight" in str(alert_data).lower() else "unknown",
        operator=operator,
        service_number=service_number,
        route=route,
        journey_context=journey_context,
        change={
            "type": alert_type,
            "delay_minutes": delay_minutes if delay_minutes > 0 else None,
            "original_departure": original_dep,
            "updated_departure": updated_dep,
            "original_arrival": alert_data.get("original_arrival"),
            "updated_arrival": alert_data.get("new_arrival"),
            "reason": reason
        },
        impact={"level": impact_level, "affected_stops": [], "connection_risk": journey_context["has_connection"]},
        summary=summary,
        recommendations=recommendations,
        actions=["CHECK_TRIP_IMPACT", "FIND_NEARBY_OPTIONS", "VIEW_BOOKING"],
        created_at=datetime.now().isoformat(),
        delay_minutes=delay_minutes
    )
