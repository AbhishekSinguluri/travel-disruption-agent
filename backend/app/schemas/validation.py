from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ValidationIssue(BaseModel):
    id: str
    severity: str
    type: str
    stop_id: Optional[str] = None
    message: str
    details: str
    suggested_action: Optional[str] = None

class ValidationResult(BaseModel):
    valid: bool
    issues: List[ValidationIssue]
    validated_stops: List[Dict[str, Any]]
    summary: Dict[str, Any]
