from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.services.gmail_provider import get_gmail_provider, RealGmailProvider
from app.services.monitoring_agent import AgenticTravelMonitor, MockAlertRepository
from app.api.auth import get_current_user, User
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class MonitorTestRequest(BaseModel):
    operator: str
    service_number: str
    origin: str
    destination: str
    travel_date: str
    monitoring_window: str

@router.post("/test-start")
async def start_booking_monitor_test(req: MonitorTestRequest, user: User = Depends(get_current_user)):
    try:
        # Step 1 & 4: Retrieve Candidate Emails with RealGmailProvider
        provider = get_gmail_provider(user.id)
        if not isinstance(provider, RealGmailProvider):
            raise HTTPException(status_code=400, detail="RealGmailProvider not available. Connect Gmail first.")
            
        profile = provider.connect()
        gmail_address = profile.get("email", "unknown")
        
        # Determine days from window
        days = 1
        if req.monitoring_window == "LAST_1_WEEK":
            days = 7
        elif req.monitoring_window == "LAST_2_WEEKS":
            days = 14
            
        # Step 3: Build a focused search
        query = f'"{req.operator}" OR "{req.service_number}"'
        candidate_emails = provider.search_messages(query=query, days=days)
        
        # Step 5 & 6 & 7: Agent 4 pipeline
        monitor = AgenticTravelMonitor()
        intent = {
            "transport_type": "flight", # defaulting for test
            "operator": req.operator,
            "flight_number": req.service_number,
            "monitoring_events": ["DELAY", "CANCELLATION", "RESCHEDULE"]
        }
        
        relevant_email = None
        for email in candidate_emails:
            if monitor.relevance_agent.evaluate(email, intent):
                relevant_email = email
                break
                
        if not relevant_email:
            return {
                "found": False,
                "reason": "No relevant booking email found within the selected time window.",
                "account": gmail_address,
                "candidates_checked": len(candidate_emails)
            }
            
        # Create baseline
        baseline = monitor.understanding_agent.create_baseline(relevant_email, intent)
        
        # Step 9: Store baseline
        monitor_id = MockAlertRepository.start_monitor({
            "user_id": user.id,
            "gmail_account": gmail_address,
            "intent": intent,
            "window": req.monitoring_window,
            "baseline": baseline,
            "source_message_id": relevant_email.get("id")
        })
        
        # User-facing summary
        summary = f"{req.operator} {req.service_number}\\n{req.origin} -> {req.destination}\\n{req.travel_date}\\nStatus: Confirmed\\n\\nMonitoring is active for delays, cancellations and schedule changes."
        
        return {
            "found": True,
            "account": gmail_address,
            "query": f"{query} newer_than:{days}d",
            "candidates_checked": len(candidate_emails),
            "booking": baseline.get("summary", {}),
            "summary": summary,
            "monitoring": {
                "active": True,
                "events": intent["monitoring_events"]
            },
            "message": "Booking found and monitoring baseline created."
        }

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
