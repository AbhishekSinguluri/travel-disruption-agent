import os
import re

app_path = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\frontend\src\App.jsx"
with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add state
if "const [monitoringMode, setMonitoringMode] = useState('TRIP');" not in content:
    content = content.replace(
        "const [activeTab, setActiveTab] = useState('itinerary');",
        "const [activeTab, setActiveTab] = useState('itinerary');\n  const [monitoringMode, setMonitoringMode] = useState('TRIP');"
    )

# Add Alerts State
if "const [alerts, setAlerts] = useState([]);" not in content:
    content = content.replace(
        "const [monitoringMode, setMonitoringMode] = useState('TRIP');",
        "const [monitoringMode, setMonitoringMode] = useState('TRIP');\n  const [alerts, setAlerts] = useState([]);\n  const [bookingSummary, setBookingSummary] = useState(null);\n  const [gmailConnected, setGmailConnected] = useState(false);\n  const [isCheckingEmail, setIsCheckingEmail] = useState(false);\n  const [bookingId, setBookingId] = useState(null);"
    )

# Modify the handleImport function to support booking extraction
import_func_ext = """
  const handleImport = async (type) => {
    setImporting(true);
    setImportError(null);
    try {
      if (monitoringMode === 'BOOKINGS') {
        const res = await fetch('http://localhost:8000/api/bookings/extract', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ type: type, text: "Air India AI 123" }) // Dummy implementation
        });
        const data = await res.json();
        setBookingSummary(data.summary);
        setBookingId(data.booking_id);
      } else {
        const payload = type === 'text' 
          ? { text: "9am Charminar\\n12pm lunch at Laad Bazaar\\n2pm Salar Jung Museum\\n5pm Necklace Road\\n8pm dinner at Jubilee Hills" }
          : { file_type: type, content: "base64..." };
        const res = await fetch(`http://localhost:8000/api/trips/import/${type}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        
        if (!res.ok) throw new Error('Failed to import trip');
        const data = await res.json();
        loadDemoTrip(); // reload
        setShowImportModal(false);
      }
    } catch (err) {
      console.error("Import error:", err);
      setImportError(err.message || 'Failed to process import');
    } finally {
      setImporting(false);
    }
  };
"""
# We will just replace handleImport completely.
content = re.sub(r'const handleImport = async \(type\) => \{.*?\n  \};', import_func_ext, content, flags=re.DOTALL)

# Modify the UI elements
ui_replacement = """
                <div className="flex gap-4 mb-4">
                  <button onClick={() => setMonitoringMode('TRIP')} className={`text-xs font-bold uppercase tracking-widest px-4 py-2 rounded-full transition-all ${monitoringMode === 'TRIP' ? 'bg-slate-200 text-slate-900 shadow-sm' : 'text-slate-500 hover:bg-slate-100'}`}>MONITOR TRIP</button>
                  <button onClick={() => setMonitoringMode('BOOKINGS')} className={`text-xs font-bold uppercase tracking-widest px-4 py-2 rounded-full transition-all ${monitoringMode === 'BOOKINGS' ? 'bg-slate-200 text-slate-900 shadow-sm' : 'text-slate-500 hover:bg-slate-100'}`}>MONITOR BOOKINGS</button>
                </div>
                {monitoringMode === 'TRIP' ? (
                  <p className="text-xl text-slate-600 font-light leading-relaxed mb-8">Your trips, ready for whatever changes along the way.</p>
                ) : (
                  <p className="text-xl text-slate-600 font-light leading-relaxed mb-8">Upload a booking, reservation, or ticket and Roam will keep watch for changes.</p>
                )}
"""

content = content.replace('<p className="text-xl text-slate-600 font-light leading-relaxed mb-8">Your trips, ready for whatever changes along the way.</p>', ui_replacement)

# Add Alerts section and booking summary overlay
alerts_and_summary = """
            {/* Alerts & Booking Review */}
            {alerts.length > 0 && (
              <div className="mt-16 mb-8 max-w-4xl">
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-6">ALERTS</h3>
                <div className="flex flex-col gap-4">
                  {alerts.map((a, i) => (
                    <div key={i} className="bg-red-50 border border-red-100 rounded-xl p-6 flex gap-4 items-start shadow-sm">
                      <div className="w-8 h-8 rounded-full bg-red-100 text-red-600 flex items-center justify-center shrink-0">⚠</div>
                      <div>
                        <h4 className="font-bold text-slate-900">{a.title}</h4>
                        <p className="text-slate-600 mt-1">{a.message}</p>
                        <p className="text-xs text-slate-400 mt-3 font-medium uppercase tracking-wider">Detected {new Date(a.detected_at).toLocaleTimeString()}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {bookingSummary && (
              <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                <div className="bg-white rounded-3xl p-8 max-w-lg w-full shadow-2xl">
                  <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-serif text-slate-900">Booking Summary</h2>
                    <button onClick={() => setBookingSummary(null)} className="text-slate-400 hover:text-slate-900 text-2xl">&times;</button>
                  </div>
                  
                  <div className="space-y-4 mb-8">
                    <p className="text-sm font-bold uppercase tracking-widest text-blue-600">{bookingSummary.booking_type}</p>
                    <h3 className="text-xl font-medium text-slate-900">{bookingSummary.title}</h3>
                    <div className="flex items-center gap-2 text-slate-600">
                      <span>{bookingSummary.departure_location}</span>
                      <span>→</span>
                      <span>{bookingSummary.arrival_location}</span>
                    </div>
                    <div className="text-slate-500 mt-4 text-sm">
                      <p>Booking ref: <span className="font-medium text-slate-800">{bookingSummary.booking_reference}</span></p>
                      <p>Status: <span className="font-medium text-slate-800">{bookingSummary.status}</span></p>
                      {bookingSummary.baggage && (
                         <div className="mt-2 p-3 bg-slate-50 rounded-lg">
                           <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Baggage</p>
                           <p className="text-slate-700">{bookingSummary.baggage}</p>
                         </div>
                      )}
                    </div>
                  </div>
                  
                  {!gmailConnected ? (
                    <div className="bg-blue-50 p-6 rounded-2xl border border-blue-100">
                      <h4 className="font-bold text-slate-900 mb-2">Connect Gmail</h4>
                      <p className="text-sm text-slate-600 mb-4">Roam will monitor your booking emails for changes.</p>
                      <button 
                        onClick={async () => {
                          const res = await fetch(`http://localhost:8000/api/bookings/${bookingId}/gmail/connect`, {
                            method: 'POST', headers:{'Content-Type': 'application/json'}, body: JSON.stringify({auth_code:'mock'})
                          });
                          if(res.ok) setGmailConnected(true);
                        }}
                        className="w-full bg-blue-600 text-white rounded-full py-3 text-sm font-bold hover:bg-blue-700 transition-colors shadow-sm"
                      >
                        Connect Gmail
                      </button>
                    </div>
                  ) : (
                    <div className="bg-green-50 p-6 rounded-2xl border border-green-100">
                      <h4 className="font-bold text-green-900 mb-1">Monitoring Active</h4>
                      <p className="text-xs text-green-700 mb-4 uppercase tracking-wider">Last checked: Just now</p>
                      <button 
                        onClick={async () => {
                          setIsCheckingEmail(true);
                          const res = await fetch(`http://localhost:8000/api/bookings/${bookingId}/check`, { method: 'POST' });
                          const data = await res.json();
                          if(data.status === 'alert_created') {
                             setAlerts(prev => [data.alert, ...prev]);
                             setBookingSummary(null); // Close modal on alert
                          }
                          setIsCheckingEmail(false);
                        }}
                        disabled={isCheckingEmail}
                        className="w-full bg-white border border-green-200 text-green-800 rounded-full py-3 text-sm font-bold hover:bg-green-50 transition-colors shadow-sm disabled:opacity-50"
                      >
                        {isCheckingEmail ? 'Checking...' : 'Check now'}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
"""
content = content.replace('            {/* Grid for Past Trips (Placeholder) */}', alerts_and_summary + '\n            {/* Grid for Past Trips (Placeholder) */}')

with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Frontend Booking code generated.")
