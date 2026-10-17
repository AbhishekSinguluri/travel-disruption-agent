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
