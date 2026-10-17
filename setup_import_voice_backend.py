import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

backend_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\app"
tests_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\tests"

# --- SCHEMAS ---
voice_schema = """
from pydantic import BaseModel
from typing import Optional, Any, Dict

class UserIntent(BaseModel):
    intent: str
    target_stop_id: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    requested_action: Optional[str] = None
    confidence: float
"""
write_file(f"{backend_dir}/schemas/voice.py", voice_schema)

import_schema = """
from pydantic import BaseModel
from typing import List, Optional

class ExtractedStop(BaseModel):
    title: str
    category: Optional[str] = None
    location_name: Optional[str] = None
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    reservation_info: Optional[str] = None
    confidence: float

class ExtractedDay(BaseModel):
    date: str
    stops: List[ExtractedStop]

class ExtractedTrip(BaseModel):
    name: str
    destination: str
    start_date: str
    end_date: str
    days: List[ExtractedDay]
"""
write_file(f"{backend_dir}/schemas/import_trip.py", import_schema)

# --- SERVICES ---
speech_py = """
import os
import logging
from groq import Groq
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SpeechToTextProvider:
    def transcribe(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            logger.warning("[SPEECH] GROQ_API_KEY missing, using mock transcription")
            return {"text": "I'm stuck in traffic.", "language": "en", "success": True}
            
        try:
            client = Groq(api_key=api_key)
            # groq supports whisper-large-v3
            res = client.audio.transcriptions.create(
                file=(filename, file_bytes),
                model="whisper-large-v3",
                response_format="verbose_json"
            )
            lang = res.language
            if not lang.startswith("en"):
                return {"success": False, "error": "Voice input currently supports English only."}
                
            return {"text": res.text, "language": "en", "success": True}
        except Exception as e:
            logger.error(f"[SPEECH] Transcription failed: {e}")
            return {"success": False, "error": str(e)}

def get_speech_provider() -> SpeechToTextProvider:
    return SpeechToTextProvider()
"""
write_file(f"{backend_dir}/services/speech.py", speech_py)

doc_parser_py = """
import os
import logging
import base64
import fitz  # PyMuPDF
from groq import Groq
import instructor
from app.schemas.import_trip import ExtractedTrip

logger = logging.getLogger(__name__)

class DocumentParser:
    def extract_from_text(self, text: str) -> ExtractedTrip:
        return self._extract_via_llm(text)
        
    def extract_from_pdf(self, file_bytes: bytes) -> ExtractedTrip:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return self._extract_via_llm(text)
        
    def extract_from_image(self, file_bytes: bytes, mime_type: str) -> ExtractedTrip:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            return self._mock_extraction()
            
        b64 = base64.b64encode(file_bytes).decode('utf-8')
        client = instructor.from_groq(Groq(api_key=api_key))
        try:
            res = client.chat.completions.create(
                model="llama-3.2-90b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract the itinerary from this image."},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}}
                        ]
                    }
                ],
                response_model=ExtractedTrip,
            )
            return res
        except Exception as e:
            logger.error(f"[VISION] Extraction failed: {e}")
            return self._mock_extraction()
            
    def _extract_via_llm(self, text: str) -> ExtractedTrip:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            return self._mock_extraction()
            
        client = instructor.from_groq(Groq(api_key=api_key))
        try:
            res = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "user", "content": f"Extract the itinerary from this text:\n{text}"}
                ],
                response_model=ExtractedTrip,
            )
            return res
        except Exception as e:
            logger.error(f"[DOC] Extraction failed: {e}")
            return self._mock_extraction()

    def _mock_extraction(self) -> ExtractedTrip:
        return ExtractedTrip(
            name="Mock Imported Trip",
            destination="Unknown",
            start_date="2026-10-01",
            end_date="2026-10-02",
            days=[]
        )
"""
write_file(f"{backend_dir}/services/document_parser.py", doc_parser_py)

# --- ROUTERS ---
voice_router = """
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import Dict, Any
from app.services.speech import get_speech_provider
from app.api.auth import get_current_user, User
from app.schemas.voice import UserIntent
import os
import json
import instructor
from groq import Groq

router = APIRouter()

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    content = await file.read()
    provider = get_speech_provider()
    res = provider.transcribe(content, file.filename)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Transcription failed"))
    return res

@router.post("/intent")
def extract_intent(payload: Dict[str, str], user: User = Depends(get_current_user)):
    text = payload.get("text", "")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        return UserIntent(intent="REPORT_DELAY", confidence=0.9).model_dump()
        
    try:
        client = instructor.from_groq(Groq(api_key=api_key))
        res = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": f"Determine intent for this trip command: '{text}'"}],
            response_model=UserIntent,
        )
        return res.model_dump()
    except Exception as e:
        return UserIntent(intent="OTHER", confidence=0.0).model_dump()
"""
write_file(f"{backend_dir}/api/voice.py", voice_router)

imports_router = """
from fastapi import APIRouter, UploadFile, File, Form, Depends
from app.services.document_parser import DocumentParser
from app.api.auth import get_current_user, User

router = APIRouter()
parser = DocumentParser()

@router.post("/text")
def import_text(payload: dict, user: User = Depends(get_current_user)):
    text = payload.get("text", "")
    res = parser.extract_from_text(text)
    return res.model_dump()

@router.post("/pdf")
async def import_pdf(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    content = await file.read()
    res = parser.extract_from_pdf(content)
    return res.model_dump()

@router.post("/image")
async def import_image(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    content = await file.read()
    res = parser.extract_from_image(content, file.content_type)
    return res.model_dump()
"""
write_file(f"{backend_dir}/api/imports.py", imports_router)

# Mount them in main
main_patch = """
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.trips import router as trips_router
from app.api.monitoring import router as mon_router
from app.api.voice import router as voice_router
from app.api.imports import router as imports_router

app = FastAPI(title="Travel Disruption Recovery Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

app.include_router(trips_router, prefix="/api/trips", tags=["trips"])
app.include_router(mon_router, prefix="/api/monitor", tags=["monitoring"])
app.include_router(voice_router, prefix="/api/voice", tags=["voice"])
app.include_router(imports_router, prefix="/api/import", tags=["import"])
"""
write_file(f"{backend_dir}/main.py", main_patch)

# --- TESTS ---
test_voice_py = """
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_transcribe_mock():
    # Provide a dummy webm file
    files = {"file": ("test.webm", b"dummy_audio_content", "audio/webm")}
    res = client.post("/api/voice/transcribe", files=files)
    assert res.status_code == 200
    assert res.json()["success"] == True

def test_intent_mock():
    res = client.post("/api/voice/intent", json={"text": "I am stuck in traffic"})
    assert res.status_code == 200
    assert "intent" in res.json()
"""
write_file(f"{tests_dir}/test_voice.py", test_voice_py)

test_imports_py = """
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_import_text():
    res = client.post("/api/import/text", json={"text": "Day 1 10AM Beach"})
    assert res.status_code == 200
    assert "name" in res.json()
    assert "days" in res.json()

def test_import_pdf():
    # PDF parsing needs a valid PDF header minimal or it fails PyMuPDF
    pdf_content = b"%PDF-1.4\\n1 0 obj\\n<<>>\\nendobj\\ntrailer\\n<< /Root 1 0 R >>\\n%%EOF"
    files = {"file": ("test.pdf", pdf_content, "application/pdf")}
    res = client.post("/api/import/pdf", files=files)
    assert res.status_code == 200

def test_import_image():
    files = {"file": ("test.jpg", b"fake_image", "image/jpeg")}
    res = client.post("/api/import/image", files=files)
    assert res.status_code == 200
"""
write_file(f"{tests_dir}/test_imports.py", test_imports_py)

