# ROAM — Local Business AI Automator & Disruption Concierge

> **Capstone Project:** The Local Business AI Automator  
> **Target Business Domain:** Local City Tourism & Heritage Experience Operator  
> **Platform:** ROAM Autonomous Concierge & Disruption Recovery Agent

---

## 🎯 Business Problem & Value Proposition
Local experience providers, city tour operators, and tourism businesses lose thousands of dollars each month due to unexpected disruptions:
- Unpredictable weather (e.g. monsoon rains shuttering outdoor monuments)
- Sudden venue closures and VIP blockades
- Overwhelmed support desks during peak tourist seasons

**ROAM** operates as a 24/7 autonomous customer support and operations agent tailored for local tourism and experience operators. When disruptions occur, ROAM grounds itself in real local business and city data, autonomously reschedules affected itinerary stops with vetted alternatives, books live local events, and keeps customer itineraries in sync in real time.

---

## 🏗️ 3-Tier Core Architecture

### 1. The Knowledge Layer (RAG & Grounding)
- **Local Business Grounding:** Ingests curated local attraction schedules, ticket pricing structures, category metadata, and operational constraints for destinations (e.g. Jaipur, Rome).
- **Live Local Events & Festivals:** Tracks local city happenings (cultural nights, heritage workshops, festival dates, and ticket prices) to offer authentic real-time alternatives.
- **Zero-Hallucination Policy:** Agent strictly grounds its alternatives within real opening hours, geographic feasibility, and weather constraints.

### 2. The Action Layer (Autonomous Tools & State Graph)
- **LangGraph Multi-Agent Workflows:**
  - `classify_disruption`: Evaluates severity and affected stops.
  - `assess_impact`: Computes time and schedule ripple effects.
  - `determine_recovery`: Chooses optimal recovery strategy (e.g. indoor substitution, time shift).
  - `search_alternatives`: Autonomous tool querying nearby curated attractions and live local events.
- **Data Persistence:** Writes real-time booking payloads, schedule changes, and status logs to Supabase / SQLite databases.

### 3. The Interface Layer
- **Voice-to-Text (Whisper):** Spoken input handling powered by Groq Whisper (`whisper-large-v3`) with speech transcription.
- **Interactive Live Dashboard:** Modern React + Tailwind interface featuring interactive maps, live disruption recovery cards, and Rome Buddy AI chat drawer with real-time state mirroring.

---

## 🚀 Key Features
- **Live Disruption Detection:** Monitors GPS location, weather conditions, and transport delays.
- **1-Click / Autonomous Recovery:** Suggests smart nearby substitutes with distance and travel time.
- **Local Events & Experiences Hub:** Live discovery of city events, entry fees, and booking integration.
- **Multi-Modal Interaction:** Voice transcription and interactive conversational agent.

---

## 🛠️ Setup Instructions

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate   # On Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Edge Case Handling
- **Closed Venues / Weather Hazards:** Automatically routes travelers from outdoor venues to sheltered indoor heritage sites.
- **Off-Topic & Out-of-Bounds Queries:** Gracefully redirects off-topic questions back to local business services and trip itineraries.
- **Language / Audio Validation:** Validates audio transcriptions and handles edge cases without crashes.
