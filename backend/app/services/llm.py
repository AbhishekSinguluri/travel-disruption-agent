import os
import json
import logging
from time import time
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.schemas.llm import DisruptionClassification, UserRecoveryPreference, RecoveryStrategy

logger = logging.getLogger(__name__)

# Initialize Groq client conditionally
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
raw_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
# Auto-fix deprecated models like llama-3.1-8b-instant
GROQ_MODEL = "llama-3.3-70b-versatile" if "llama-3.1" in raw_model else raw_model

try:
    if GROQ_API_KEY:
        from groq import Groq
        groq_client = Groq(api_key=GROQ_API_KEY)
    else:
        groq_client = None
except Exception:
    groq_client = None

def _call_groq_json(system_prompt: str, user_prompt: str, schema: BaseModel) -> Optional[BaseModel]:
    if not groq_client:
        return None
    start = time()
    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt + "\n\nOutput JSON matching this schema: " + json.dumps(schema.model_json_schema())},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        latency = time() - start
        logger.info(f"[LLM] SUCCESS - model: {GROQ_MODEL}, latency: {latency:.2f}s")
        return schema.model_validate_json(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"[LLM] Groq reasoning failed: {str(e)}")
        return None

def classify_disruption_text(disruption_text: str, trip_context: str) -> DisruptionClassification:
    logger.info("[LLM] CLASSIFY_DISRUPTION")
    system_prompt = "You are a travel itinerary recovery reasoning component. You do not browse the internet. Reason only from facts provided. Classify the disruption."
    user_prompt = f"Trip Context: {trip_context}\nDisruption: {disruption_text}"
    
    result = _call_groq_json(system_prompt, user_prompt, DisruptionClassification)
    if result:
        return result
    
    logger.warning("[LLM] Groq reasoning failed — using deterministic fallback for classification")
    
    req_type = "WEATHER_DISRUPTION"
    stop_id = "stop-4"
    try:
        import json
        parsed = json.loads(disruption_text)
        req_type = parsed.get("type", "WEATHER_DISRUPTION")
        stop_id = parsed.get("stop_id", parsed.get("affected_stop_id", "stop-4"))
    except Exception:
        pass
        
    return DisruptionClassification(
        type=req_type,
        severity="HIGH",
        affected_stop_id=stop_id,
        reason="Fallback deterministic classification",
        confidence=1.0
    )

def parse_user_preferences(user_text: str) -> UserRecoveryPreference:
    logger.info("[LLM] PARSE_USER_PREFERENCES")
    system_prompt = "You are a travel itinerary recovery reasoning component. Parse user text into structured preferences."
    
    result = _call_groq_json(system_prompt, user_text, UserRecoveryPreference)
    if result:
        return result
        
    logger.warning("[LLM] Groq reasoning failed — using deterministic fallback for preferences")
    return UserRecoveryPreference(
        categories=["Indoor", "Culture"],
        indoor=True,
        budget="Low",
        duration_preference=None
    )

def determine_recovery_strategy(facts: str) -> RecoveryStrategy:
    logger.info("[LLM] DETERMINE_RECOVERY_STRATEGY")
    system_prompt = "You are a travel itinerary recovery reasoning component. You do not know current real-world information. Never invent places or times. Choose a recovery strategy."
    
    result = _call_groq_json(system_prompt, facts, RecoveryStrategy)
    if result:
        return result
        
    logger.warning("[LLM] Groq reasoning failed — using deterministic fallback for strategy")
    return RecoveryStrategy(
        strategy="ASK_USER",
        explanation="Deterministic fallback: asking user for preferences."
    )
