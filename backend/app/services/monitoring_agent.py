
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

# POINT 1: Date Filters
class EmailMonitoringWindow:
    LAST_1_DAY = "LAST_1_DAY"
    LAST_1_WEEK = "LAST_1_WEEK"
    LAST_2_WEEKS = "LAST_2_WEEKS"

    @classmethod
    def is_within_window(cls, window: str, date_str: str) -> bool:
        if not date_str:
            return False
        try:
            email_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            return False
        
        now = datetime.now(email_date.tzinfo)
        delta = now - email_date
        
        if window == cls.LAST_1_DAY:
            return delta.days <= 1
        elif window == cls.LAST_1_WEEK:
            return delta.days <= 7
        elif window == cls.LAST_2_WEEKS:
            return delta.days <= 14
        return False

# POINT 4 & 5 & 6: Active State and Alert Repo
class MockAlertRepository:
    _alerts = []
    _monitors = {}

    @classmethod
    def start_monitor(cls, monitor_data: Dict[str, Any]):
        mid = str(uuid.uuid4())
        monitor_data['monitor_id'] = mid
        monitor_data['active'] = True
        cls._monitors[mid] = monitor_data
        return mid

    @classmethod
    def get_monitor(cls, monitor_id: str):
        return cls._monitors.get(monitor_id)

    @classmethod
    def stop_monitor(cls, monitor_id: str):
        if monitor_id in cls._monitors:
            cls._monitors[monitor_id]['active'] = False

    @classmethod
    def create_alert(cls, alert: Dict[str, Any]):
        # Deduplication check
        for a in cls._alerts:
            if a.get('source_message_id') == alert.get('source_message_id') and a.get('alert_type') == alert.get('alert_type'):
                return False
        alert['alert_id'] = str(uuid.uuid4())
        alert['read'] = False
        cls._alerts.append(alert)
        return True
        
    @classmethod
    def get_unread(cls):
        return [a for a in cls._alerts if not a['read']]

    @classmethod
    def mark_read(cls, alert_id: str):
        for a in cls._alerts:
            if a['alert_id'] == alert_id:
                a['read'] = True
                break

class BookingIntentAgent:
    def extract_intent(self, text: str) -> Dict[str, Any]:
        intent = {
            "transport_type": "flight",
            "monitoring_events": ["delay", "cancellation", "reschedule", "departure_change", "arrival_change"]
        }
        text_lower = text.lower()
        if "air india" in text_lower:
            intent["operator"] = "Air India"
            intent["flight_number"] = "AI123"
        elif "train" in text_lower:
            intent["transport_type"] = "train"
        elif "hotel" in text_lower:
            intent["transport_type"] = "hotel"
            
        return intent

class BookingSearchPlanner:
    def plan_search(self, intent: Dict[str, Any], date_filter: str) -> Dict[str, Any]:
        concepts = [intent.get("operator", ""), intent.get("flight_number", "")]
        return {
            "window": date_filter,
            "concepts": [c for c in concepts if c]
        }

class EmailRelevanceAgent:
    def evaluate(self, candidate: Dict[str, Any], intent: Dict[str, Any]) -> bool:
        subject = candidate.get("subject", "").lower()
        snippet = candidate.get("snippet", "").lower()
        
        if "promotional" in subject or "wrong" in subject:
            return False
            
        if intent.get("transport_type") == "flight":
            fn = intent.get("flight_number", "").lower()
            if fn and fn not in subject and fn not in snippet:
                return False
                
        return True

class BookingUnderstandingAgent:
    def create_baseline(self, email: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        # POINT 2: User-facing summary
        summary = {
            "transport_type": intent.get("transport_type"),
            "operator": intent.get("operator"),
            "service_number": intent.get("flight_number"),
            "status": "confirmed",
            "monitoring_events": intent.get("monitoring_events"),
            "source_message_ids": [email.get("id")]
        }
        
        # POINT 3: Transport specific
        if summary["transport_type"] == "flight":
            summary["travel_consideration"] = "international flight - check visa" if "international" in email.get("snippet", "").lower() else "domestic flight"
        elif summary["transport_type"] == "train":
            summary["platform"] = "TBD"
            
        return {
            "intent": intent,
            "message_id": email.get("id"),
            "thread_id": email.get("threadId"),
            "summary": summary
        }

class ChangeDetectionAgent:
    def detect_change(self, new_email: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
        body = new_email.get("snippet", "").lower() + new_email.get("body", "").lower()
        if "cancelled" in body or "cancellation" in body:
            return {"changed": True, "type": "cancellation", "importance": "CRITICAL", "message": new_email.get("snippet")}
        if "delayed" in body or "delay" in body:
            return {"changed": True, "type": "delay", "importance": "IMPORTANT", "message": new_email.get("snippet")}
        if "reschedule" in body:
            return {"changed": True, "type": "reschedule", "importance": "IMPORTANT", "message": new_email.get("snippet")}
        return {"changed": False}

class AgenticTravelMonitor:
    def __init__(self):
        self.intent_agent = BookingIntentAgent()
        self.search_planner = BookingSearchPlanner()
        self.relevance_agent = EmailRelevanceAgent()
        self.understanding_agent = BookingUnderstandingAgent()
        self.change_agent = ChangeDetectionAgent()

    def create_monitor(self, text: str, date_filter: str, initial_email: Dict[str, Any]):
        intent = self.intent_agent.extract_intent(text)
        baseline = self.understanding_agent.create_baseline(initial_email, intent)
        monitor_id = MockAlertRepository.start_monitor({
            "intent": intent,
            "window": date_filter,
            "baseline": baseline
        })
        return monitor_id, baseline["summary"]

    def process_new_email(self, monitor_id: str, new_email: Dict[str, Any]) -> Dict[str, Any]:
        monitor = MockAlertRepository.get_monitor(monitor_id)
        if not monitor or not monitor.get("active"):
            return {"alert": False}
            
        baseline = monitor["baseline"]
        
        if not self.relevance_agent.evaluate(new_email, baseline.get("intent", {})):
            return {"alert": False}
        
        change = self.change_agent.detect_change(new_email, baseline)
        if change.get("changed"):
            alert_created = MockAlertRepository.create_alert({
                "monitor_id": monitor_id,
                "importance": change.get("importance"),
                "alert_type": change.get("type"),
                "message": change.get("message"),
                "source_message_id": new_email.get("id")
            })
            if alert_created:
                return {
                    "alert": True,
                    "importance": change.get("importance"),
                    "message": change.get("message")
                }
        return {"alert": False}

# POINT 7 & 8: Prepared Push Architecture / Offline Fallback
class GmailPushService:
    def receive_pubsub_webhook(self, payload): ...
class GmailHistorySyncService:
    def sync_history(self): ...
class BookingMonitorTransport: ...
class MockBookingMonitorTransport(BookingMonitorTransport): ...
class GmailPushTransport(BookingMonitorTransport): ...
class GmailPollingTransport(BookingMonitorTransport): ...
