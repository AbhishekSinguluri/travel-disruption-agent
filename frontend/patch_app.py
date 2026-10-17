import re

with open("src/App.jsx", "r", encoding="utf-8") as f:
    content = f.read()

# Make activeDisruption and recoveryCandidates reactive
# Find the line:
# const { trip, trips, loadDemoTrip, fetchTrips, saveTrip, loadTrip, updateTrip, deleteTrip, toggleStopCheck, sendCompanionMessage, simulateDisruption, activeDisruption: disruption, impactAnalysis: impact, submitPreferences, recoveryCandidates: candidates, selectCandidate, alerts, addAlert, markAlertRead } = useTripStore();
# The user wants:
# const activeDisruption = useTripStore(state => state.activeDisruption)
# const recoveryCandidates = useTripStore(state => state.recoveryCandidates)

content = content.replace(
    "const { trip, trips, loadDemoTrip, fetchTrips, saveTrip, loadTrip, updateTrip, deleteTrip, toggleStopCheck, sendCompanionMessage, simulateDisruption, activeDisruption: disruption, impactAnalysis: impact, submitPreferences, recoveryCandidates: candidates, selectCandidate, alerts, addAlert, markAlertRead } = useTripStore();",
    "const { trip, trips, loadDemoTrip, fetchTrips, saveTrip, loadTrip, updateTrip, deleteTrip, toggleStopCheck, sendCompanionMessage, simulateDisruption, impactAnalysis: impact, submitPreferences, selectCandidate, alerts, addAlert, markAlertRead, setDelayAlert, delayAlert } = useTripStore();\n  const activeDisruption = useTripStore(state => state.activeDisruption);\n  const recoveryCandidates = useTripStore(state => state.recoveryCandidates);"
)

# Wait, `delayAlert` is also state? We don't have delayAlert in tripStore.
# Let's just create a local state for 'showRecoveryChoices' in App instead of 'I'M STUCK'
# Actually, I'll update the card HTML inside App.jsx that I inserted.

card_ui_old = """      {useTripStore.getState().activeDisruption && (
        <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 z-[1000] bg-white rounded-2xl shadow-2xl p-6 border border-slate-200 w-[400px]">
          {!useTripStore.getState().recoveryCandidates?.length ? (
            <>
              <h3 className="font-bold text-red-600 mb-2 uppercase tracking-wide text-sm">Action Required</h3>
              <p className="text-slate-700 mb-4 font-serif">You're behind schedule. Would you like to recover or shift the itinerary?</p>
              <div className="flex gap-3">
                <button onClick={() => { useTripStore.getState().shiftItinerary(15); }} className="flex-1 py-2 bg-slate-100 text-slate-700 rounded-lg font-bold text-sm hover:bg-slate-200 transition-colors">I'M OKAY</button>
                <button onClick={() => { useTripStore.getState().simulateDisruption('WEATHER_DISRUPTION', activeStopId); }} className="flex-1 py-2 bg-slate-900 text-white rounded-lg font-bold text-sm hover:bg-slate-800 transition-colors">I'M STUCK</button>
              </div>
            </>
          ) : (
             <>
              <h3 className="font-bold text-red-600 mb-2 uppercase tracking-wide text-sm">Recovery Options</h3>
              <div className="flex flex-col gap-2">
                <button onClick={() => { useTripStore.getState().submitPreferences({}); }} className="w-full py-2 bg-slate-900 text-white rounded-lg font-bold text-sm hover:bg-slate-800 transition-colors">FIND ALTERNATIVE</button>
                <button onClick={() => { useTripStore.getState().skipToNextStop(activeStopId); }} className="w-full py-2 bg-slate-100 text-slate-700 rounded-lg font-bold text-sm hover:bg-slate-200 transition-colors">SKIP STOP</button>
              </div>
             </>
          )}
        </div>
      )}"""

# First, I need to add state for 'showRecovery' if I'm stuck.
# And `delayAlert` has delay_minutes. I need to make `delayAlert` part of the store or just use activeDisruption.delay_minutes.
card_ui_new = """      {activeDisruption && (
        <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 z-[1000] bg-white rounded-2xl shadow-2xl p-6 border border-slate-200 w-[400px]">
          {!recoveryCandidates?.length && !activeDisruption.showRecovery ? (
            <>
              <h3 className="font-bold text-red-600 mb-2 uppercase tracking-wide text-sm">Action Required</h3>
              <p className="text-slate-700 mb-4 font-serif">You're {activeDisruption.delay_minutes || 15} min behind schedule. Would you like to recover or shift the itinerary?</p>
              <div className="flex gap-3">
                <button onClick={() => { useTripStore.getState().shiftItinerary(activeDisruption.delay_minutes || 15); useTripStore.getState().clearDisruption(); }} className="flex-1 py-2 bg-slate-100 text-slate-700 rounded-lg font-bold text-sm hover:bg-slate-200 transition-colors">I'M OKAY</button>
                <button onClick={() => { useTripStore.getState().setDisruptionStuck(); }} className="flex-1 py-2 bg-slate-900 text-white rounded-lg font-bold text-sm hover:bg-slate-800 transition-colors">I'M STUCK</button>
              </div>
            </>
          ) : (
             <>
              <h3 className="font-bold text-red-600 mb-2 uppercase tracking-wide text-sm">Recovery Options</h3>
              <div className="flex flex-col gap-2">
                {!recoveryCandidates?.length && <button onClick={() => { simulateDisruption('WEATHER_DISRUPTION', activeStopId); }} className="w-full py-2 bg-slate-900 text-white rounded-lg font-bold text-sm hover:bg-slate-800 transition-colors">FIND ALTERNATIVE</button>}
                {recoveryCandidates?.map(cand => (
                  <button key={cand.id} onClick={() => { selectCandidate(cand.id); }} className="w-full py-2 bg-slate-50 text-slate-700 rounded-lg text-sm text-left px-4 hover:bg-slate-100">{cand.name}</button>
                ))}
                <button onClick={() => { useTripStore.getState().skipToNextStop(activeStopId); useTripStore.getState().clearDisruption(); }} className="w-full py-2 bg-slate-100 text-slate-700 rounded-lg font-bold text-sm hover:bg-slate-200 transition-colors">SKIP STOP</button>
              </div>
             </>
          )}
        </div>
      )}"""

content = content.replace(card_ui_old, card_ui_new)

# Update tripStore.js to add `clearDisruption` and `setDisruptionStuck`
store_path = "src/store/tripStore.js"
with open(store_path, "r", encoding="utf-8") as fs:
    store_content = fs.read()

if "clearDisruption: () => set" not in store_content:
    store_content = store_content.replace(
        "skipToNextStop: async",
        "clearDisruption: () => set({ activeDisruption: null, recoveryCandidates: [] }),\n    setDisruptionStuck: () => set(state => ({ activeDisruption: { ...state.activeDisruption, showRecovery: true } })),\n    skipToNextStop: async"
    )

with open(store_path, "w", encoding="utf-8") as fs:
    fs.write(store_content)

with open("src/App.jsx", "w", encoding="utf-8") as f:
    f.write(content)
print("Patched App.jsx and tripStore.js")
