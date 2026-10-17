import re

with open("src/App.jsx", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Remove duplicate disruption cards
content = re.sub(r'\{liveStatus\.includes\(\'behind\'\)\s*&&\s*\([\s\S]*?I\'m stuck</button>\s*</div>\s*\)\}', '', content)
content = re.sub(r'\{delayAlert\s*&&\s*\([\s\S]*?I\'m stuck</button>\s*</div>\s*\)\}', '', content)

# 2. Inject global card right before the closing div of the main layout
card_ui = """
      {useTripStore.getState().activeDisruption && (
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
      )}
"""

content = content.replace("    </div>\n  );\n}\n\nexport default App;", f"{card_ui}\n    </div>\n  );\n}}\n\nexport default App;")

with open("src/App.jsx", "w", encoding="utf-8") as f:
    f.write(content)
print("Patched frontend")
