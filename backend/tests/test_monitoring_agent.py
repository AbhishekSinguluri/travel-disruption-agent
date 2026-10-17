
import pytest
import json
from datetime import datetime, timedelta
from app.services.monitoring_agent import (
    AgenticTravelMonitor, EmailMonitoringWindow, MockAlertRepository
)

@pytest.fixture(autouse=True)
def reset_repo():
    MockAlertRepository._alerts = []
    MockAlertRepository._monitors = {}

@pytest.fixture
def emails():
    return {
        "air_india_confirmation": {
            "id": "msg-1", "threadId": "t-1", "subject": "Booking Confirmation AI123",
            "snippet": "Flight AI123 confirmed.", "body": "Flight AI123 confirmed."
        },
        "air_india_delay": {
            "id": "msg-2", "threadId": "t-1", "subject": "Delay AI123",
            "snippet": "Flight delayed.", "body": "Flight delayed."
        },
        "air_india_cancellation": {
            "id": "msg-3", "threadId": "t-1", "subject": "Cancellation AI123",
            "snippet": "Flight cancelled.", "body": "Flight cancelled."
        },
        "air_india_reschedule": {
            "id": "msg-4", "threadId": "t-1", "subject": "Reschedule AI123",
            "snippet": "Flight reschedule.", "body": "Flight reschedule."
        },
        "air_india_promotion": {
            "id": "msg-5", "threadId": "t-2", "subject": "Promotional offer",
            "snippet": "20% off", "body": "20% off"
        },
        "wrong_flight": {
            "id": "msg-6", "threadId": "t-3", "subject": "Booking AI999",
            "snippet": "Flight AI999", "body": "Flight AI999"
        },
        "duplicate_cancellation": {
            "id": "msg-3", "threadId": "t-1", "subject": "Cancellation AI123",
            "snippet": "Flight cancelled.", "body": "Flight cancelled."
        },
        "train_booking": {
            "id": "msg-7", "threadId": "t-4", "subject": "Train booking",
            "snippet": "Train booking", "body": "Train booking"
        },
        "hotel_booking": {
            "id": "msg-8", "threadId": "t-5", "subject": "Hotel booking",
            "snippet": "Hotel booking", "body": "Hotel booking"
        }
    }

def test_date_filters():
    now = datetime.now()
    d_3_days_ago = (now - timedelta(days=3)).isoformat() + "Z"
    d_10_days_ago = (now - timedelta(days=10)).isoformat() + "Z"
    d_20_days_ago = (now - timedelta(days=20)).isoformat() + "Z"

    assert not EmailMonitoringWindow.is_within_window(EmailMonitoringWindow.LAST_1_DAY, d_3_days_ago)
    assert EmailMonitoringWindow.is_within_window(EmailMonitoringWindow.LAST_1_WEEK, d_3_days_ago)
    assert EmailMonitoringWindow.is_within_window(EmailMonitoringWindow.LAST_2_WEEKS, d_10_days_ago)
    assert not EmailMonitoringWindow.is_within_window(EmailMonitoringWindow.LAST_2_WEEKS, d_20_days_ago)

def test_e2e_offline_flow(emails):
    monitor = AgenticTravelMonitor()
    
    # Create baseline
    mid, summary = monitor.create_monitor(
        "Monitor my Air India AI123 flight", 
        EmailMonitoringWindow.LAST_1_WEEK, 
        emails["air_india_confirmation"]
    )
    
    assert summary["transport_type"] == "flight"
    assert summary["operator"] == "Air India"
    
    # Process delay
    res = monitor.process_new_email(mid, emails["air_india_delay"])
    assert res["alert"] == True
    assert res["importance"] == "IMPORTANT"
    
    # Process cancellation
    res = monitor.process_new_email(mid, emails["air_india_cancellation"])
    assert res["alert"] == True
    assert res["importance"] == "CRITICAL"
    
    # Duplicate cancellation (deduplication)
    res = monitor.process_new_email(mid, emails["duplicate_cancellation"])
    assert res["alert"] == False
    
    # Irrelevant
    res = monitor.process_new_email(mid, emails["air_india_promotion"])
    assert res["alert"] == False
    
    res = monitor.process_new_email(mid, emails["wrong_flight"])
    assert res["alert"] == False

def test_transport_reasoning(emails):
    monitor = AgenticTravelMonitor()
    mid, summary = monitor.create_monitor("Monitor my train", "LAST_1_WEEK", emails["train_booking"])
    assert summary["transport_type"] == "train"
    
    mid2, summary2 = monitor.create_monitor("Monitor my hotel", "LAST_1_WEEK", emails["hotel_booking"])
    assert summary2["transport_type"] == "hotel"

def test_stop_monitor(emails):
    monitor = AgenticTravelMonitor()
    mid, _ = monitor.create_monitor("Monitor AI123", "LAST_1_WEEK", emails["air_india_confirmation"])
    MockAlertRepository.stop_monitor(mid)
    res = monitor.process_new_email(mid, emails["air_india_delay"])
    assert res["alert"] == False
