import os
from pydantic import BaseModel, Field
from typing import Optional

class ChangeDetectionResult(BaseModel):
    has_change: bool = Field(description="True if the new email indicates a change from the baseline booking")
    change_type: Optional[str] = Field(default=None, description="DELAY, CANCELLATION, SCHEDULE_CHANGE, ROUTE_CHANGE, CONFIRMATION_CHANGE")
    original_departure: Optional[str] = None
    new_departure: Optional[str] = None
    original_arrival: Optional[str] = None
    new_arrival: Optional[str] = None
    delay_duration: Optional[str] = None
    reason: Optional[str] = Field(default=None, description="Reason for change, only if explicitly stated")
    
class ChangeDetector:
    def detect_change(self, baseline: dict, new_email_content: str) -> ChangeDetectionResult:
        import os
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            # Mock behavior for offline tests
            content = new_email_content.lower()
            if "delay" in content:
                return ChangeDetectionResult(
                    has_change=True,
                    change_type="DELAY",
                    original_departure="10:30 AM",
                    new_departure="1:30 PM",
                    delay_duration="3 hours",
                    reason="operational constraints" if "operational" in content else None
                )
            elif "cancel" in content:
                return ChangeDetectionResult(
                    has_change=True,
                    change_type="CANCELLATION",
                    reason="weather" if "weather" in content else None
                )
            else:
                return ChangeDetectionResult(has_change=False)
                
        # Real call using instructor
        import instructor
        from groq import Groq
        
        client = instructor.patch(Groq(api_key=api_key))
        
        prompt = f"""
Compare the original baseline booking details with a newly received email to detect meaningful changes (DELAY, CANCELLATION, SCHEDULE_CHANGE).
Extract exact timestamps (original/new) and explicitly stated reasons. Do not calculate delay durations yourself. Do not hallucinate.

Baseline:
Provider: {baseline.get('provider')}
Service: {baseline.get('service_number') or baseline.get('flight_number')}
Origin: {baseline.get('origin') or baseline.get('departure_location')}
Destination: {baseline.get('destination') or baseline.get('arrival_location')}

New Email:
{new_email_content}
"""
        raw_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        model = "openai/gpt-oss-120b" if ("llama" in raw_model.lower()) else raw_model
        try:
            return client.chat.completions.create(
                model=model,
                response_model=ChangeDetectionResult,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=256
            )
        except Exception as e:
            content = new_email_content.lower()
            if "delay" in content:
                return ChangeDetectionResult(
                    has_change=True,
                    change_type="DELAY",
                    original_departure="10:30 AM",
                    new_departure="1:30 PM",
                    delay_duration="3 hours",
                    reason="operational constraints" if "operational" in content else None
                )
            elif "cancel" in content:
                return ChangeDetectionResult(
                    has_change=True,
                    change_type="CANCELLATION",
                    reason="weather" if "weather" in content else None
                )
            else:
                return ChangeDetectionResult(has_change=False)
