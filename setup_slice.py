import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

backend_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\backend\app"
frontend_dir = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\frontend\src"

# --- BACKEND ---
schemas_trip = """
from pydantic import BaseModel
from typing import List, Optional

class ItineraryStop(BaseModel):
    id: str
    title: str
    category: str
    location_name: str
    latitude: float
    longitude: float
    date: str
    start_time: str
    end_time: str
    duration_minutes: int
    status: str = "PLANNED"
    notes: Optional[str] = None

class TripDay(BaseModel):
    id: str
    date: str
    stops: List[ItineraryStop]

class Trip(BaseModel):
    id: str
    destination: str
    start_date: str
    end_date: str
    days: List[TripDay]
"""
write_file(f"{backend_dir}/schemas/trip.py", schemas_trip)

schemas_disruption = """
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Disruption(BaseModel):
    id: str
    type: str
    affected_stop_id: str
    reason: str
    severity: str

class RecoveryCandidate(BaseModel):
    id: str
    name: str
    category: str
    description: str
    latitude: float
    longitude: float
    distance_km: float
    travel_minutes: int
    opening_time: str
    closing_time: str
    estimated_duration_minutes: int
    budget: str
    rating: float
    weather_suitable: bool
    next_stop_compatible: bool
    why_recommended: str

class UserPreference(BaseModel):
    categories: List[str]
    budget: str

class ReplanResult(BaseModel):
    success: bool
    conflicts: List[str] = []
    updated_stops: List[Dict[str, Any]] = []
"""
write_file(f"{backend_dir}/schemas/disruption.py", schemas_disruption)

services_mock_db = """
from app.schemas.trip import Trip, TripDay, ItineraryStop

demo_trip = Trip(
    id="trip-1",
    destination="Hyderabad",
    start_date="2026-10-01",
    end_date="2026-10-01",
    days=[
        TripDay(
            id="day-1",
            date="2026-10-01",
            stops=[
                ItineraryStop(id="stop-1", title="Hotel", category="Lodging", location_name="Taj Falaknuma Palace", latitude=17.33, longitude=78.46, date="2026-10-01", start_time="09:00", end_time="09:30", duration_minutes=30, status="COMPLETED"),
                ItineraryStop(id="stop-2", title="Charminar", category="Attraction", location_name="Charminar", latitude=17.36, longitude=78.47, date="2026-10-01", start_time="10:00", end_time="11:30", duration_minutes=90, status="COMPLETED"),
                ItineraryStop(id="stop-3", title="Lunch", category="Food", location_name="Shadab Hotel", latitude=17.36, longitude=78.47, date="2026-10-01", start_time="12:00", end_time="13:30", duration_minutes=90, status="COMPLETED"),
                ItineraryStop(id="stop-4", title="Beach", category="Nature", location_name="Fake Beach", latitude=17.42, longitude=78.48, date="2026-10-01", start_time="14:00", end_time="16:00", duration_minutes=120, status="PLANNED"),
                ItineraryStop(id="stop-5", title="Shopping", category="Shopping", location_name="Laad Bazaar", latitude=17.36, longitude=78.47, date="2026-10-01", start_time="17:00", end_time="19:00", duration_minutes=120, status="PLANNED"),
                ItineraryStop(id="stop-6", title="Dinner", category="Food", location_name="Jewel of Nizam", latitude=17.39, longitude=78.47, date="2026-10-01", start_time="20:00", end_time="21:30", duration_minutes=90, status="PLANNED")
            ]
        )
    ]
)

MOCK_DB = {
    "trips": {
        "trip-1": demo_trip.model_dump()
    },
    "disruptions": {},
    "state": {}
}

def get_trip(trip_id: str):
    return MOCK_DB["trips"].get(trip_id)

def update_trip(trip_id: str, data: dict):
    MOCK_DB["trips"][trip_id] = data
    return data
"""
write_file(f"{backend_dir}/services/mock_db.py", services_mock_db)

workflows_recovery = """
from app.schemas.disruption import RecoveryCandidate

def run_recovery_workflow(disruption_type: str, affected_stop_id: str, preferences: dict = None):
    # Mock implementation of LangGraph logic
    impact = {
        "affected_stop_id": affected_stop_id,
        "message": "Beach visit is unavailable because of heavy rain. Your 17:00 shopping plan is still feasible."
    }
    
    candidates = []
    if preferences:
        # Generate candidates based on preferences
        candidates = [
            RecoveryCandidate(
                id="cand-1", name="Salar Jung Museum", category="Indoor", description="Famous art museum",
                latitude=17.37, longitude=78.48, distance_km=2.5, travel_minutes=15,
                opening_time="10:00", closing_time="17:00", estimated_duration_minutes=120,
                budget="Low", rating=4.8, weather_suitable=True, next_stop_compatible=True,
                why_recommended="Indoor activity, fits your time window perfectly."
            ),
            RecoveryCandidate(
                id="cand-2", name="Indoor Art Gallery", category="Culture", description="Local contemporary art",
                latitude=17.38, longitude=78.47, distance_km=3.0, travel_minutes=20,
                opening_time="11:00", closing_time="18:00", estimated_duration_minutes=90,
                budget="Medium", rating=4.5, weather_suitable=True, next_stop_compatible=True,
                why_recommended="Close to your next shopping location."
            )
        ]
        
    return {
        "impact": impact,
        "candidates": [c.model_dump() for c in candidates]
    }
    
def run_replanning(trip_id: str, stop_id: str, candidate_id: str, candidates: list):
    from app.services.mock_db import get_trip, update_trip
    trip = get_trip(trip_id)
    cand = next((c for c in candidates if c['id'] == candidate_id), None)
    if not cand: return {"success": False, "conflicts": ["Candidate not found"]}
    
    # Replace stop
    for day in trip['days']:
        for stop in day['stops']:
            if stop['id'] == stop_id:
                stop['title'] = cand['name']
                stop['category'] = cand['category']
                stop['location_name'] = cand['name']
                stop['status'] = "REPLACED"
                stop['notes'] = "Replaced due to weather disruption."
    
    update_trip(trip_id, trip)
    return {"success": True, "conflicts": [], "updated_stops": trip['days'][0]['stops']}
"""
write_file(f"{backend_dir}/workflows/recovery.py", workflows_recovery)

api_trips = """
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
from app.services.mock_db import get_trip, MOCK_DB
from app.workflows.recovery import run_recovery_workflow, run_replanning

router = APIRouter()

@router.get("/demo")
def get_demo_trip():
    return get_trip("trip-1")

class DisruptionReq(BaseModel):
    type: str
    affected_stop_id: str

@router.post("/{trip_id}/simulate-disruption")
def simulate_disruption(trip_id: str, req: DisruptionReq):
    result = run_recovery_workflow(req.type, req.affected_stop_id)
    MOCK_DB["state"][trip_id] = {"impact": result["impact"], "disruption": req.model_dump()}
    return result

class PrefReq(BaseModel):
    categories: List[str]
    budget: str

@router.post("/{trip_id}/recovery/preferences")
def submit_preferences(trip_id: str, req: PrefReq):
    state = MOCK_DB["state"].get(trip_id, {})
    if not state: return {"error": "No disruption active"}
    
    result = run_recovery_workflow(
        state["disruption"]["type"], 
        state["disruption"]["affected_stop_id"], 
        req.model_dump()
    )
    MOCK_DB["state"][trip_id]["candidates"] = result["candidates"]
    return {"candidates": result["candidates"]}

class SelectReq(BaseModel):
    candidate_id: str

@router.post("/{trip_id}/recovery/select")
def select_candidate(trip_id: str, req: SelectReq):
    state = MOCK_DB["state"].get(trip_id, {})
    candidates = state.get("candidates", [])
    stop_id = state["disruption"]["affected_stop_id"]
    
    res = run_replanning(trip_id, stop_id, req.candidate_id, candidates)
    return res
"""
write_file(f"{backend_dir}/api/trips.py", api_trips)

main_py = """
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.trips import router as trips_router

app = FastAPI(title="Travel Disruption Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trips_router, prefix="/api/trips")

@app.get("/api/health")
def health():
    return {"status": "ok"}
"""
write_file(f"{backend_dir}/main.py", main_py)

# --- FRONTEND ---
store_js = """
import { create } from 'zustand';

export const useTripStore = create((set, get) => ({
    trip: null,
    activeDisruption: null,
    impactAnalysis: null,
    recoveryCandidates: [],
    
    loadDemoTrip: async () => {
        const res = await fetch('http://localhost:8000/api/trips/demo');
        const data = await res.json();
        set({ trip: data });
    },
    
    simulateDisruption: async () => {
        const res = await fetch('http://localhost:8000/api/trips/trip-1/simulate-disruption', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ type: 'WEATHER_DISRUPTION', affected_stop_id: 'stop-4' })
        });
        const data = await res.json();
        set({ 
            activeDisruption: { type: 'WEATHER_DISRUPTION', affected_stop_id: 'stop-4' },
            impactAnalysis: data.impact,
            recoveryCandidates: []
        });
    },
    
    submitPreferences: async (prefs) => {
        const res = await fetch('http://localhost:8000/api/trips/trip-1/recovery/preferences', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(prefs)
        });
        const data = await res.json();
        set({ recoveryCandidates: data.candidates });
    },
    
    selectCandidate: async (candidateId) => {
        const res = await fetch('http://localhost:8000/api/trips/trip-1/recovery/select', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ candidate_id: candidateId })
        });
        const data = await res.json();
        if (data.success) {
            const trip = get().trip;
            trip.days[0].stops = data.updated_stops;
            set({ trip: {...trip}, activeDisruption: null, impactAnalysis: null, recoveryCandidates: [] });
        }
    }
}));
"""
write_file(f"{frontend_dir}/store/tripStore.js", store_js)

app_jsx = """
import { useEffect, useState } from 'react';
import { useTripStore } from './store/tripStore';

function App() {
    const { trip, loadDemoTrip, simulateDisruption, activeDisruption, impactAnalysis, recoveryCandidates, submitPreferences, selectCandidate } = useTripStore();
    const [prefs, setPrefs] = useState({ categories: [], budget: 'Low' });

    useEffect(() => {
        loadDemoTrip();
    }, []);

    if (!trip) return <div className="p-10">Loading...</div>;

    const stops = trip.days[0].stops;

    return (
        <div className="flex h-screen bg-slate-50 text-slate-800 font-sans">
            <div className="w-1/3 p-6 border-r bg-white overflow-y-auto">
                <h1 className="text-2xl font-bold mb-4">{trip.destination} Itinerary</h1>
                <button onClick={simulateDisruption} className="mb-6 bg-red-500 text-white px-4 py-2 rounded">Simulate Disruption: Beach Closed</button>
                
                <div className="space-y-4">
                    {stops.map(stop => (
                        <div key={stop.id} className={`p-4 border rounded ${stop.status === 'REPLACED' ? 'bg-green-50 border-green-200' : stop.id === activeDisruption?.affected_stop_id ? 'bg-red-50 border-red-200' : 'bg-gray-50'}`}>
                            <div className="font-bold">{stop.start_time} - {stop.end_time}</div>
                            <div className="text-lg">{stop.title}</div>
                            <div className="text-sm text-gray-600">{stop.status}</div>
                        </div>
                    ))}
                </div>
            </div>
            
            <div className="w-1/3 p-6 bg-slate-200 flex items-center justify-center border-r">
                <div className="text-center text-slate-500">
                    <p>Map Placeholder</p>
                    <p>(Google Maps integration comes later)</p>
                </div>
            </div>
            
            <div className="w-1/3 p-6 bg-white overflow-y-auto">
                <h2 className="text-xl font-bold mb-4">AI Companion</h2>
                
                {!activeDisruption && (
                    <div className="p-4 bg-blue-50 text-blue-800 rounded">
                        Monitoring your trip. Everything is on schedule.
                    </div>
                )}
                
                {activeDisruption && impactAnalysis && recoveryCandidates.length === 0 && (
                    <div className="space-y-4">
                        <div className="p-4 bg-red-50 text-red-800 rounded border border-red-200">
                            <strong>⚠ Trip Disruption</strong>
                            <p>{impactAnalysis.message}</p>
                        </div>
                        
                        <div className="p-4 border rounded">
                            <h3 className="font-bold mb-2">What would you like instead?</h3>
                            <div className="flex gap-2 mb-4">
                                {['Indoor', 'Culture', 'Food'].map(cat => (
                                    <label key={cat} className="flex items-center gap-1">
                                        <input type="checkbox" onChange={(e) => {
                                            const cats = e.target.checked ? [...prefs.categories, cat] : prefs.categories.filter(c => c !== cat);
                                            setPrefs({...prefs, categories: cats});
                                        }} /> {cat}
                                    </label>
                                ))}
                            </div>
                            <button onClick={() => submitPreferences(prefs)} className="bg-blue-500 text-white px-4 py-2 rounded">Find Alternatives</button>
                        </div>
                    </div>
                )}
                
                {recoveryCandidates.length > 0 && (
                    <div className="space-y-4">
                        <h3 className="font-bold text-lg">Alternative Options</h3>
                        {recoveryCandidates.map(cand => (
                            <div key={cand.id} className="p-4 border rounded hover:border-blue-300">
                                <h4 className="font-bold">{cand.name}</h4>
                                <p className="text-sm text-gray-600">{cand.category} • {cand.distance_km}km • {cand.budget}</p>
                                <p className="text-sm my-2">{cand.why_recommended}</p>
                                <button onClick={() => selectCandidate(cand.id)} className="bg-green-500 text-white px-3 py-1 rounded text-sm">Choose this</button>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default App;
"""
write_file(f"{frontend_dir}/App.jsx", app_jsx)
