from pydantic import BaseModel
from typing import Optional, Any, Dict

class UserIntent(BaseModel):
    intent: str
    target_stop_id: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    requested_action: Optional[str] = None
    confidence: float
