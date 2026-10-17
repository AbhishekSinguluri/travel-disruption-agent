from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class DisruptionClassification(BaseModel):
    type: str
    severity: str
    affected_stop_id: str
    reason: str
    confidence: float

class UserRecoveryPreference(BaseModel):
    categories: List[str]
    indoor: Optional[bool] = None
    budget: str
    duration_preference: Optional[int] = None

class RecoveryStrategyType(str, Enum):
    KEEP = "KEEP"
    SHIFT = "SHIFT"
    SHORTEN = "SHORTEN"
    SKIP = "SKIP"
    REPLACE = "REPLACE"
    ASK_USER = "ASK_USER"

class RecoveryStrategy(BaseModel):
    strategy: RecoveryStrategyType
    explanation: str
