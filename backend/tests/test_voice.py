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
