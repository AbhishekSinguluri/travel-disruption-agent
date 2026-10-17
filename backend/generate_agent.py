import os
import json

def generate_fixtures():
    os.makedirs("tests/fixtures", exist_ok=True)
    fixtures = {
        "air_india_confirmation": {
            "id": "msg-1",
            "threadId": "thread-1",
            "subject": "Booking Confirmation: Air India AI123",
            "snippet": "Your Air India AI123 flight booking from Hyderabad to Delhi on October 4 is confirmed. Departure: 09:20, Arrival: 11:35.",
            "body": "Your Air India AI123 flight booking from Hyderabad to Delhi on October 4 is confirmed. Departure: 09:20, Arrival: 11:35. Booking reference: ABC123. Baggage: 15kg."
        },
        "air_india_delay": {
            "id": "msg-2",
            "threadId": "thread-1",
            "subject": "Flight Delay: Air India AI123",
            "snippet": "Your Air India AI123 flight originally scheduled for 09:20 has been delayed. The new departure time is 11:10.",
            "body": "Your Air India AI123 flight originally scheduled for 09:20 has been delayed. The new departure time is 11:10."
        },
        "air_india_cancellation": {
            "id": "msg-3",
            "threadId": "thread-1",
            "subject": "Flight Cancellation: Air India AI123",
            "snippet": "Your Air India AI123 flight has been cancelled.",
            "body": "Your Air India AI123 flight has been cancelled."
        },
        "air_india_promotional": {
            "id": "msg-4",
            "threadId": "thread-2",
            "subject": "Air India Promotional Offer",
            "snippet": "Fly with Air India and get 20% off on your next booking.",
            "body": "Fly with Air India and get 20% off on your next booking."
        },
        "wrong_air_india_flight": {
            "id": "msg-5",
            "threadId": "thread-3",
            "subject": "Booking Confirmation: Air India AI999",
            "snippet": "Your Air India AI999 flight from Delhi to Mumbai is confirmed.",
            "body": "Your Air India AI999 flight from Delhi to Mumbai is confirmed."
        }
    }
    with open("tests/fixtures/emails.json", "w") as f:
        json.dump(fixtures, f, indent=4)

def generate_monitoring_agent():
    path = "app/services/monitoring_agent.py"
    code = """
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class BookingIntentAgent:
    def extract_intent(self, text: str) -> Dict[str, Any]:
        # Mock LLM extraction
        return {
            "transport_type": "flight",
            "operator": "Air India",
            "flight_number": "AI123",
            "origin": "Hyderabad",
            "destination": "Delhi",
            "travel_date": "2026-10-04",
            "monitoring_events": ["delay", "cancellation", "reschedule", "departure_change", "arrival_change"]
        }

class BookingSearchPlanner:
    def plan_search(self, intent: Dict[str, Any], date_filter: str) -> List[str]:
        # Mock search planning
        return [f"{intent.get('operator')} {intent.get('flight_number')}"]

class EmailRelevanceAgent:
    def evaluate(self, candidate: Dict[str, Any], intent: Dict[str, Any]) -> bool:
        # Mock relevance logic
        subject = candidate.get("subject", "").lower()
        if "promotional" in subject:
            return False
        if intent.get("flight_number", "").lower() not in subject.lower() and intent.get("flight_number", "").lower() not in candidate.get("snippet", "").lower():
            return False
        return True

class BookingUnderstandingAgent:
    def create_baseline(self, email: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "intent": intent,
            "message_id": email.get("id"),
            "thread_id": email.get("threadId"),
            "status": "confirmed",
            "departure": "09:20",
            "arrival": "11:35"
        }

class ChangeDetectionAgent:
    def detect_change(self, new_email: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
        body = new_email.get("snippet", "").lower()
        if "delayed" in body:
            return {"changed": True, "type": "delay", "importance": "IMPORTANT", "message": new_email.get("snippet")}
        if "cancelled" in body:
            return {"changed": True, "type": "cancellation", "importance": "CRITICAL", "message": new_email.get("snippet")}
        return {"changed": False}

class AgenticTravelMonitor:
    def __init__(self):
        self.intent_agent = BookingIntentAgent()
        self.search_planner = BookingSearchPlanner()
        self.relevance_agent = EmailRelevanceAgent()
        self.understanding_agent = BookingUnderstandingAgent()
        self.change_agent = ChangeDetectionAgent()

    def process_new_email(self, new_email: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
        if not self.relevance_agent.evaluate(new_email, baseline.get("intent", {})):
            return {"alert": False}
        
        change = self.change_agent.detect_change(new_email, baseline)
        if change.get("changed"):
            return {
                "alert": True,
                "importance": change.get("importance"),
                "message": change.get("message")
            }
        return {"alert": False}
"""
    with open(path, "w") as f:
        f.write(code)

def generate_tests():
    path = "tests/test_monitoring_agent.py"
    code = """
import pytest
import json
from app.services.monitoring_agent import AgenticTravelMonitor

@pytest.fixture
def emails():
    with open("tests/fixtures/emails.json", "r") as f:
        return json.load(f)

def test_intent_extraction():
    monitor = AgenticTravelMonitor()
    intent = monitor.intent_agent.extract_intent("Monitor my Air India AI123 flight from Hyderabad to Delhi on October 4")
    assert intent["operator"] == "Air India"
    assert intent["flight_number"] == "AI123"

def test_relevance(emails):
    monitor = AgenticTravelMonitor()
    intent = {"flight_number": "AI123"}
    assert monitor.relevance_agent.evaluate(emails["air_india_confirmation"], intent) == True
    assert monitor.relevance_agent.evaluate(emails["air_india_promotional"], intent) == False
    assert monitor.relevance_agent.evaluate(emails["wrong_air_india_flight"], intent) == False

def test_change_detection_delay(emails):
    monitor = AgenticTravelMonitor()
    intent = {"flight_number": "AI123"}
    baseline = monitor.understanding_agent.create_baseline(emails["air_india_confirmation"], intent)
    
    result = monitor.process_new_email(emails["air_india_delay"], baseline)
    assert result["alert"] == True
    assert result["importance"] == "IMPORTANT"

def test_change_detection_cancellation(emails):
    monitor = AgenticTravelMonitor()
    intent = {"flight_number": "AI123"}
    baseline = monitor.understanding_agent.create_baseline(emails["air_india_confirmation"], intent)
    
    result = monitor.process_new_email(emails["air_india_cancellation"], baseline)
    assert result["alert"] == True
    assert result["importance"] == "CRITICAL"
"""
    with open(path, "w") as f:
        f.write(code)

if __name__ == "__main__":
    generate_fixtures()
    generate_monitoring_agent()
    generate_tests()
    print("Agent simulation generated.")
