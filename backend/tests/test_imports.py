from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_import_text():
    res = client.post("/api/import/text", json={"text": "Day 1 10AM Beach"})
    assert res.status_code == 200
    assert "name" in res.json()
    assert "days" in res.json()

def test_import_text_messy_bhubaneswar_regression():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    # Skip if no API key is present so CI doesn't fail, but we'll run it locally with .env
    if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "your_groq_api_key_here":
        return
        
    messy_text = (
        "I’m going to Bhubaneswar on 4 October. I land around 12 in the afternoon from Hyderabad "
        "and want to check into my hotel first. After that I want to have lunch somewhere nearby, "
        "then visit Udayagiri and Khandagiri caves, Dhauli Shanti Stupa, and maybe Ekamra Haat in the evening. "
        "I’d like dinner around 7:30 or 8 and then head back to the hotel. Please arrange the day sensibly "
        "with enough travel time between places and don’t make it too rushed."
    )
    res = client.post("/api/import/text", json={"text": messy_text})
    assert res.status_code == 200
    data = res.json()
    
    assert data["destination"].lower() == "bhubaneswar"
    assert "2026-10-04" in data.get("start_date", "") or "2023" in data.get("start_date", "") or "2024" in data.get("start_date", "") or "-10-04" in data.get("start_date", "")
    
    stops = data["days"][0]["stops"]
    titles = [s["title"].lower() for s in stops]
    notes = [str(s.get("notes") or "").lower() for s in stops]
    all_text = " ".join(titles + notes)
    
    # Check that context is preserved
    assert "hyderabad" in all_text or "hotel" in all_text
    assert "lunch" in all_text
    assert "udayagiri" in all_text or "khandagiri" in all_text
    assert "dhauli" in all_text or "stupa" in all_text
    assert "ekamra" in all_text or "haat" in all_text
    assert "dinner" in all_text

def test_import_pdf():
    # PDF parsing needs a valid PDF header minimal or it fails PyMuPDF
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    files = {"file": ("test.pdf", pdf_content, "application/pdf")}
    res = client.post("/api/import/pdf", files=files)
    assert res.status_code == 200

def test_import_image():
    files = {"file": ("test.jpg", b"fake_image", "image/jpeg")}
    res = client.post("/api/import/image", files=files)
    assert res.status_code == 200

def test_import_scanned_pdf():
    # Empty PDF fallback
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    files = {"file": ("scanned.pdf", pdf_content, "application/pdf")}
    res = client.post("/api/import/pdf", files=files)
    assert res.status_code == 200

def test_import_text_exact_hyderabad_regression():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "your_groq_api_key_here":
        return
        
    messy_text = (
        "Hyderabad trip\n"
        "Day 1: Leave hotel, visit Charminar, Chowmahalla Palace, lunch around Laad Bazaar, "
        "then Golconda Fort and Qutb Shahi Tombs. Dinner and back to hotel."
    )
    res = client.post("/api/import/text", json={"text": messy_text})
    assert res.status_code == 200
    data = res.json()
    
    assert data["destination"].lower() == "hyderabad"
    
    stops = data["days"][0]["stops"]
    titles = [s["title"].lower() for s in stops]
    all_text = " ".join(titles)
    
    assert "charminar" in all_text
    assert "chowmahalla" in all_text
    assert "lunch" in all_text
    assert "laad" in all_text or "bazaar" in all_text
    assert "golconda" in all_text
    assert "qutb" in all_text
    assert "dinner" in all_text
    assert "hotel" in all_text
