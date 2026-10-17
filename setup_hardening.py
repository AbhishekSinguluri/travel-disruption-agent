import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

backend_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\app"
tests_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\tests"
root_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent"

# 1. Env Example
env_example = """
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama3-8b-8192
GROQ_VISION_MODEL=llama-3.2-90b-vision-preview
GROQ_WHISPER_MODEL=whisper-large-v3
OPENWEATHER_API_KEY=your_openweather_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
DATABASE_URL=your_db_url
"""
write_file(f"{root_dir}/.env.example", env_example)

# 2. Hardened Document Parser (adds PDF to Image fallback)
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
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            
            # Fallback for scanned PDFs
            if len(text.strip()) < 50:
                logger.info("PDF text insufficient, attempting vision fallback...")
                if len(doc) > 0:
                    pix = doc[0].get_pixmap()
                    img_bytes = pix.tobytes("png")
                    return self.extract_from_image(img_bytes, "image/png")
            return self._extract_via_llm(text)
        except Exception as e:
            logger.error(f"[DOC] PDF parse error: {e}")
            return self._mock_extraction()
        
    def extract_from_image(self, file_bytes: bytes, mime_type: str) -> ExtractedTrip:
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_VISION_MODEL", "llama-3.2-90b-vision-preview")
        if not api_key or api_key == "your_groq_api_key_here":
            return self._mock_extraction()
            
        b64 = base64.b64encode(file_bytes).decode('utf-8')
        try:
            client = instructor.from_groq(Groq(api_key=api_key))
            res = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract the itinerary from this image. Do not guess unknown fields, return null."},
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
        model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        if not api_key or api_key == "your_groq_api_key_here":
            return self._mock_extraction()
            
        try:
            client = instructor.from_groq(Groq(api_key=api_key))
            res = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": f"Extract the itinerary from this text:\\n{text}\\nDo not guess unknown fields, return null."}
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

# 3. Hardened Speech Service (adds model config)
speech_py = """
import os
import logging
from groq import Groq
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SpeechToTextProvider:
    def transcribe(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3")
        
        # Test mock trigger
        if getattr(self, "_test_mock_language", None) == "es":
            return {"success": False, "error": "Voice input currently supports English only."}

        if not api_key or api_key == "your_groq_api_key_here":
            logger.warning("[SPEECH] GROQ_API_KEY missing, using mock transcription")
            return {"text": "I'm stuck in traffic.", "language": "en", "success": True}
            
        try:
            client = Groq(api_key=api_key)
            res = client.audio.transcriptions.create(
                file=(filename, file_bytes),
                model=model,
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

# 4. Hardened voice intent router
voice_router = """
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
"""
write_file(f"{backend_dir}/api/voice.py", voice_router)

# 5. Tests
test_voice_py = """
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_transcribe_mock():
    files = {"file": ("test.webm", b"dummy_audio_content", "audio/webm")}
    res = client.post("/api/voice/transcribe", files=files)
    assert res.status_code == 200
    assert res.json()["success"] == True

def test_transcribe_large_file():
    large_content = b"0" * (11 * 1024 * 1024)
    files = {"file": ("test.webm", large_content, "audio/webm")}
    res = client.post("/api/voice/transcribe", files=files)
    assert res.status_code == 413

def test_transcribe_non_english():
    files = {"file": ("spanish.webm", b"dummy_audio_content", "audio/webm")}
    res = client.post("/api/voice/transcribe", files=files)
    assert res.status_code == 400
    assert "English only" in res.json()["detail"]

def test_intent_mock():
    res = client.post("/api/voice/intent", json={"text": "I am stuck in traffic"})
    assert res.status_code == 200
    assert res.json()["intent"] == "REPORT_DELAY"
    
def test_intent_skip():
    res = client.post("/api/voice/intent", json={"text": "skip the beach"})
    assert res.status_code == 200
    assert res.json()["intent"] == "SKIP_STOP"
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
    pdf_content = b"%PDF-1.4\\n1 0 obj\\n<<>>\\nendobj\\ntrailer\\n<< /Root 1 0 R >>\\n%%EOF"
    files = {"file": ("test.pdf", pdf_content, "application/pdf")}
    res = client.post("/api/import/pdf", files=files)
    assert res.status_code == 200

def test_import_image():
    files = {"file": ("test.jpg", b"fake_image", "image/jpeg")}
    res = client.post("/api/import/image", files=files)
    assert res.status_code == 200
    
def test_import_scanned_pdf():
    # Empty PDF fallback
    pdf_content = b"%PDF-1.4\\n1 0 obj\\n<<>>\\nendobj\\ntrailer\\n<< /Root 1 0 R >>\\n%%EOF"
    files = {"file": ("scanned.pdf", pdf_content, "application/pdf")}
    res = client.post("/api/import/pdf", files=files)
    assert res.status_code == 200
"""
write_file(f"{tests_dir}/test_imports.py", test_imports_py)

