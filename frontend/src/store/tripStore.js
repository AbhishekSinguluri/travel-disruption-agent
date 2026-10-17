import { create } from 'zustand';

export const useTripStore = create((set, get) => ({
    trip: null,
    trips: [],
    activeDisruption: null,
    impactAnalysis: null,
    recoveryCandidates: [],
    alerts: [],
    addAlert: (alert) => set((state) => {
        // Prevent duplicates based on source_message_id
        if (state.alerts.some(a => a.source_message_id === alert.source_message_id && a.change.type === alert.change.type)) {
            return state;
        }
        return { alerts: [{...alert, is_read: false}, ...state.alerts] };
    }),
    markAlertRead: (alertId) => set((state) => ({
        alerts: state.alerts.map(a => a.id === alertId ? { ...a, is_read: true } : a)
    })),
    
    fetchTrips: async () => {
        const res = await fetch('http://localhost:8000/api/trips');
        const data = await res.json();
        set({ trips: Array.isArray(data) ? data : [] });
    },

    saveTrip: async (tripData) => {
        const res = await fetch('http://localhost:8000/api/trips', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(tripData)
        });
        if (res.ok) { get().fetchTrips(); }
    },

    updateTrip: async (tripId, tripData) => {
        const res = await fetch(`http://localhost:8000/api/trips/${tripId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(tripData)
        });
        if (res.ok) {
            get().fetchTrips();
            if (get().trip?.id === tripId) {
                set({ trip: tripData });
            }
        }
    },

    deleteTrip: async (tripId) => {
        const res = await fetch(`http://localhost:8000/api/trips/${tripId}`, { method: 'DELETE' });
        if (res.ok) {
            get().fetchTrips();
            if (get().trip?.id === tripId) {
                set({ trip: null });
            }
        }
    },

    toggleStopCheck: async (tripId, dayId, stopId) => {
        const trip = get().trip;
        if (!trip || trip.id !== tripId) return;
        
        const updatedTrip = JSON.parse(JSON.stringify(trip));
        const day = updatedTrip.days.find(d => d.id === dayId);
        if (day) {
            const stop = day.stops.find(s => s.id === stopId);
            if (stop) {
                stop.completed = !stop.completed;
                stop.status = stop.completed ? 'COMPLETED' : 'PLANNED';
                
                await fetch(`http://localhost:8000/api/trips/${tripId}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(updatedTrip)
                });
                
                set({ trip: updatedTrip });
            }
        }
    },

    sendCompanionMessage: async (tripId, message) => {
        const res = await fetch(`http://localhost:8000/api/trips/${tripId}/chat`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message })
        });
        if (res.ok) {
            const data = await res.json();
            return data.reply;
        }
        return "Sorry, I couldn't process that request.";
    },

    loadTrip: async (tripId) => {
        const res = await fetch(`http://localhost:8000/api/trips/${tripId}`);
        const data = await res.json();
        set({ trip: data });
    },

    loadDemoTrip: async () => {
        const res = await fetch('http://localhost:8000/api/trips/demo');
        const data = await res.json();
        set({ trip: data });
    },
    
    
    
    shiftItinerary: async (stopId, minutes) => {
        const trip = get().trip;
        if (!trip) return;
        const res = await fetch(`http://localhost:8000/api/trips/${trip.id}/shift`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ stop_id: stopId, minutes: minutes })
        });
        if (res.ok) {
            const data = await res.json();
            if (data.trip) set({ trip: data.trip });
        }
    },
    clearDisruption: () => set({ activeDisruption: null, recoveryCandidates: [] }),
    setDisruptionStuck: () => set(state => ({ activeDisruption: { ...state.activeDisruption, showRecovery: true } })),
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
            const data = await res.json();
            if (data.trip) set({ trip: data.trip });
        }
    },
    simulateDisruption: async (type='WEATHER_DISRUPTION', stopId=null, delay_minutes=15) => {
        const trip = get().trip;
        if (!trip) return;
        if (!stopId) {
            console.error("No valid active stop ID provided for disruption.");
            return;
        }
        const res = await fetch(`http://localhost:8000/api/trips/${trip.id}/simulate-disruption`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ type: type, affected_stop_id: stopId, delay_minutes: delay_minutes })
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
            activeDisruption: { type: type, affected_stop_id: stopId, delay_minutes: delay_minutes, showRecovery: false },
            impactAnalysis: data.impact || { message: "Disruption" },
            recoveryCandidates: cands
        });
    },
    

    submitPreferences: async (prefs) => {
        const trip = get().trip;
        if (!trip) return;
        const res = await fetch(`http://localhost:8000/api/trips/${trip.id}/recovery/preferences`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(prefs)
        });
        const data = await res.json();
        set({ recoveryCandidates: data.candidates });
    },
    
    selectCandidate: async (candidateId) => {
        const trip = get().trip;
        if (!trip) return;
        
        // Optimistic local update
        const activeDisruption = get().activeDisruption;
        const candidates = get().recoveryCandidates;
        const candidate = candidates?.find(c => c.id === candidateId);
        
        let newTrip = JSON.parse(JSON.stringify(trip));
        if (candidate && activeDisruption && activeDisruption.affected_stop_id) {
            for (let day of newTrip.days) {
                let stopIndex = day.stops.findIndex(s => s.id === activeDisruption.affected_stop_id);
                if (stopIndex !== -1) {
                    day.stops[stopIndex] = {
                        ...day.stops[stopIndex],
                        id: candidate.id || `alt-${Date.now()}`,
                        title: candidate.name,
                        location_name: candidate.name,
                        category: candidate.category || 'Alternative',
                        status: 'REPLACED',
                        duration_minutes: candidate.travel_time_mins || 90,
                        notes: candidate.why_recommended
                    };
                }
            }
        }
        
        set({ trip: newTrip, activeDisruption: null, impactAnalysis: null, recoveryCandidates: [] });

        const res = await fetch(`http://localhost:8000/api/trips/${trip.id}/recovery/select`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ candidate_id: candidateId })
        });
        const data = await res.json();
        // Removed backend overwrite to preserve optimistic UI update
    }
}));
