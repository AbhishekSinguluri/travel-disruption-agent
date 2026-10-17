import re

def patch_tripstore():
    with open('frontend/src/store/tripStore.js', 'r', encoding='utf-8') as f:
        content = f.read()

    new_methods = """
    shiftItinerary: async (minutes) => {
        const trip = get().trip;
        if (!trip) return;
        const res = await fetch(`http://localhost:8000/api/trips/${trip.id}/shift`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ minutes })
        });
        if (res.ok) {
            get().loadTrip(trip.id);
        }
    },
    skipToNextStop: async (stopId) => {
        if (!stopId) {
            console.error("No valid stop ID provided for skip.");
            return;
        }
        const trip = get().trip;
        if (!trip) return;
        const res = await fetch(`http://localhost:8000/api/trips/${trip.id}/skip`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ stop_id: stopId })
        });
        if (res.ok) {
            get().loadTrip(trip.id);
        }
    },
    simulateDisruption: async (type='WEATHER_DISRUPTION', stopId=null) => {
        const trip = get().trip;
        if (!trip) return;
        if (!stopId) {
            console.error("No valid active stop ID provided for disruption.");
            return;
        }
        const res = await fetch(`http://localhost:8000/api/trips/${trip.id}/simulate-disruption`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ type: type, affected_stop_id: stopId })
        });
        const data = await res.json();
        
        let cands = [];
        if (data.state && data.state.candidate_alternatives) {
            cands = data.state.candidate_alternatives;
        } else if (data.impact && data.impact.strategy && data.impact.strategy.candidates) {
            cands = data.impact.strategy.candidates;
        } else if (data.candidates) {
            cands = data.candidates;
        }
        
        set({ 
            activeDisruption: { type: type, affected_stop_id: stopId },
            impactAnalysis: data.impact,
            recoveryCandidates: cands
        });
    },
    """
    
    # We replace from shiftItinerary all the way down to simulateDisruption's end
    content = re.sub(r'shiftItinerary: async \(minutes\) => \{.*?simulateDisruption: async \(type=\'WEATHER_DISRUPTION\', stopId=null\) => \{.*?\},', new_methods, content, flags=re.DOTALL)
    
    with open('frontend/src/store/tripStore.js', 'w', encoding='utf-8') as f:
        f.write(content)

def patch_app_jsx():
    with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
        content = f.read()

    # Pass dynamic delay amount instead of 15
    content = content.replace(
        'useTripStore.getState().shiftItinerary(15)',
        'useTripStore.getState().shiftItinerary(delayAlert?.delay_minutes || 15)'
    )
    
    with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
        f.write(content)

def patch_backend_skip():
    with open('backend/app/api/trips.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_skip = """
@router.post("/{trip_id}/skip")
def skip_stop(trip_id: str, payload: dict, user: User = Depends(get_current_user)):
    repo = get_trip_repository()
    trip = repo.get_trip(trip_id, user.id) or repo.get_trip(trip_id, "demo-user")
    if not trip: raise HTTPException(status_code=404)
    stop_id = payload.get("stop_id")
    skipped_found = False
    for day in trip.get("days", []):
        for stop in day.get("stops", []):
            if stop.get("id") == stop_id:
                stop["status"] = "SKIPPED"
                skipped_found = True
            elif skipped_found and stop.get("status") in ["PLANNED", "UPCOMING"]:
                # The next stop becomes active/upcoming (frontend logic handles this based on UPCOMING vs COMPLETED)
                # But we ensure it's not marked anything weird
                stop["status"] = "UPCOMING"
                break
    repo.update_trip(trip_id, trip, user.id)
    return {"status": "skipped"}
"""
    content = re.sub(r'@router\.post\("/\{trip_id\}/skip"\).*?return \{"status": "skipped"\}', new_skip.strip(), content, flags=re.DOTALL)
    
    with open('backend/app/api/trips.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    patch_tripstore()
    patch_app_jsx()
    patch_backend_skip()
    print("Patched files successfully.")
