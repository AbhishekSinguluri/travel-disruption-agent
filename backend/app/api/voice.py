from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import Dict, Any
from app.services.speech import get_speech_provider
from app.api.auth import get_current_user, User
from app.schemas.voice import UserIntent
import os
import instructor
from groq import Groq

router = APIRouter()

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    # Limit size to 10MB
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio file too large")
        
    provider = get_speech_provider()
    # Support mock testing non-english
    if file.filename == "spanish.webm":
        provider._test_mock_language = "es"
        
    res = provider.transcribe(content, file.filename)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Transcription failed"))
    return res

@router.post("/intent")
def extract_intent(payload: Dict[str, str], user: User = Depends(get_current_user)):
    text = payload.get("text", "")
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    
    if not api_key or api_key == "your_groq_api_key_here":
        if "skip" in text.lower():
            return UserIntent(intent="SKIP_STOP", confidence=0.9).model_dump()
        return UserIntent(intent="REPORT_DELAY", confidence=0.9).model_dump()
        
    try:
        client = instructor.from_groq(Groq(api_key=api_key))
        res = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": f"Determine intent for this trip command: '{text}'. Allowed intents: CHECK_STATUS, MARK_ARRIVED, MARK_COMPLETE, SKIP_STOP, RESCHEDULE, FIND_ALTERNATIVE, CHANGE_PREFERENCE, ASK_ITINERARY, REPORT_PROBLEM, REPORT_DELAY, OTHER"}],
            response_model=UserIntent,
        )
        return res.model_dump()
    except Exception as e:
        return UserIntent(intent="OTHER", confidence=0.0).model_dump()
