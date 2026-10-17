import re
import json

def patch_app_jsx():
    with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the I'm okay button and add an onClick handler
    content = content.replace(
        '<button className="flex-1 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600">I\'m okay</button>',
        '<button onClick={() => { useTripStore.getState().shiftItinerary(15); setDelayAlert(null); }} className="flex-1 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600">I\'m okay</button>'
    )
    content = content.replace(
        '<button className="flex-1 py-2 bg-slate-100 text-slate-700 rounded-full text-xs font-bold uppercase tracking-wider hover:bg-slate-200 transition-colors">I\'m okay</button>',
        '<button onClick={() => { useTripStore.getState().shiftItinerary(15); setDelayAlert(null); }} className="flex-1 py-2 bg-slate-100 text-slate-700 rounded-full text-xs font-bold uppercase tracking-wider hover:bg-slate-200 transition-colors">I\'m okay</button>'
    )

    # I'm stuck button
    content = content.replace(
        '<button className="flex-1 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600">I\'m stuck</button>',
        '<button onClick={() => setDelayAlert(prev => ({...prev, showOptions: true}))} className="flex-1 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600">I\'m stuck</button>'
    )
    content = content.replace(
        '<button className="flex-1 py-2 bg-slate-800 text-white rounded-full text-xs font-bold uppercase tracking-wider hover:bg-slate-700 transition-colors">I\'m stuck</button>',
        '<button onClick={() => setDelayAlert(prev => ({...prev, showOptions: true}))} className="flex-1 py-2 bg-slate-800 text-white rounded-full text-xs font-bold uppercase tracking-wider hover:bg-slate-700 transition-colors">I\'m stuck</button>'
    )
    
    # We need to render the options if showOptions is true
    options_ui = """
                 {delayAlert.showOptions ? (
                    <div className="flex flex-col gap-2 w-full mt-2">
                        <button onClick={() => { useTripStore.getState().simulateDisruption('DELAY_DISRUPTION', activeStop?.id); setDelayAlert(null); }} className="w-full py-2 bg-blue-500 text-white rounded text-sm hover:bg-blue-600">FIND NEARBY ALTERNATIVE</button>
                        <button onClick={() => { useTripStore.getState().skipToNextStop(activeStop?.id); setDelayAlert(null); }} className="w-full py-2 bg-slate-500 text-white rounded text-sm hover:bg-slate-600">SKIP TO NEXT STOP</button>
                    </div>
                 ) : (
                    <div className="flex gap-2 w-full mt-2">
                        <button onClick={() => { useTripStore.getState().shiftItinerary(15); setDelayAlert(null); }} className="flex-1 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600">I'm okay</button>
                        <button onClick={() => setDelayAlert(prev => ({...prev, showOptions: true}))} className="flex-1 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600">I'm stuck</button>
                    </div>
                 )}
    """
    
    pattern = re.compile(r'<div className="flex gap-2 w-full mt-2">.*?I\'m okay.*?</button>.*?I\'m stuck.*?</button>\s*</div>', re.DOTALL)
    content = re.sub(pattern, options_ui, content)

    content = content.replace(
        '<button onClick={() => useTripStore.getState().simulateDisruption()} className="px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-medium hover:bg-blue-200">Weather Disruption</button>',
        '<button onClick={() => useTripStore.getState().simulateDisruption(\'WEATHER_DISRUPTION\', activeStop?.id)} className="px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-medium hover:bg-blue-200">Weather Disruption</button>'
    )
    
    # Deduplicate AI companion messages
    old_msg_setter = """setCompanionMessages(prev => [...prev, { sender: 'bot', text: `You're about ${data.delay_minutes} minutes behind schedule. I've updated your remaining stops.` }]);"""
    new_msg_setter = """setCompanionMessages(prev => { const txt = `You're about ${data.delay_minutes} minutes behind schedule. I've updated your remaining stops.`; if(prev.some(m => m.text === txt)) return prev; return [...prev, { sender: 'bot', text: txt }]; });"""
    content = content.replace(old_msg_setter, new_msg_setter)

    with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
        f.write(content)


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
        const res = await fetch(`http://localhost:8000/api/trips/${trip.id}/simulate-disruption`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ type: type, affected_stop_id: stopId || 'stop-4' })
        });
        const data = await res.json();
        set({ 
            activeDisruption: { type: type, affected_stop_id: stopId || 'stop-4' },
            impactAnalysis: data.impact,
            recoveryCandidates: []
        });
    },
    """
    
    content = re.sub(r'simulateDisruption:\s*async\s*\(\)\s*=>\s*\{.*?\},', new_methods, content, flags=re.DOTALL)
    
    with open('frontend/src/store/tripStore.js', 'w', encoding='utf-8') as f:
        f.write(content)

def patch_trips_py():
    with open('backend/app/api/trips.py', 'r', encoding='utf-8') as f:
        content = f.read()

    new_endpoints = """
@router.post("/{trip_id}/shift")
def shift_itinerary(trip_id: str, payload: dict, user: User = Depends(get_current_user)):
    repo = get_trip_repository()
    trip = repo.get_trip(trip_id, user.id) or repo.get_trip(trip_id, "demo-user")
    if not trip: raise HTTPException(status_code=404)
    minutes = payload.get("minutes", 15)
    
    from datetime import datetime, timedelta
    shifted = False
    for day in trip.get("days", []):
        for stop in day.get("stops", []):
            if stop.get("status") in ["UPCOMING", "PLANNED"]:
                try:
                    start = datetime.strptime(stop.get("start_time", "00:00"), "%H:%M")
                    end = datetime.strptime(stop.get("end_time", "00:00"), "%H:%M")
                    stop["start_time"] = (start + timedelta(minutes=minutes)).strftime("%H:%M")
                    stop["end_time"] = (end + timedelta(minutes=minutes)).strftime("%H:%M")
                except:
                    pass
    repo.update_trip(trip_id, trip, user.id)
    return {"status": "shifted", "trip": trip}

@router.post("/{trip_id}/skip")
def skip_stop(trip_id: str, payload: dict, user: User = Depends(get_current_user)):
    repo = get_trip_repository()
    trip = repo.get_trip(trip_id, user.id) or repo.get_trip(trip_id, "demo-user")
    if not trip: raise HTTPException(status_code=404)
    stop_id = payload.get("stop_id")
    for day in trip.get("days", []):
        for stop in day.get("stops", []):
            if stop.get("id") == stop_id:
                stop["status"] = "SKIPPED"
    repo.update_trip(trip_id, trip, user.id)
    return {"status": "skipped"}
    """
    
    if "@router.post(\"/{trip_id}/shift\")" not in content:
        content += new_endpoints
    
    with open('backend/app/api/trips.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    patch_app_jsx()
    patch_tripstore()
    patch_trips_py()
    print("Patched files successfully.")
