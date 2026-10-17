import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

frontend_src = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\frontend\src"

# Read existing App.jsx to find where to patch
app_jsx_path = f"{frontend_src}/App.jsx"
with open(app_jsx_path, 'r', encoding='utf-8') as f:
    app_jsx = f.read()

# Add demo panel and live monitor to App.jsx
if "LIVE Trip Demo Panel" not in app_jsx:
    # insert before <MapComponent
    app_jsx = app_jsx.replace("<MapComponent", """
        <div className="bg-gray-800 text-white p-4 rounded-xl shadow mb-6">
          <h2 className="text-xl font-bold mb-2 flex items-center">
            <span className="text-red-500 mr-2">●</span> LIVE Trip Demo Panel
          </h2>
          <div className="flex gap-2 flex-wrap">
            <button className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm" onClick={() => fetch(`http://localhost:8000/api/monitor/${trip.id}/simulate`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({event: 'start'})})}>Start Trip</button>
            <button className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm" onClick={() => fetch(`http://localhost:8000/api/monitor/${trip.id}/simulate`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({event: 'delay', value: 5})})}>+5 min delay</button>
            <button className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm" onClick={() => fetch(`http://localhost:8000/api/monitor/${trip.id}/simulate`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({event: 'delay', value: 12})})}>+12 min delay</button>
            <button className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm" onClick={() => fetch(`http://localhost:8000/api/monitor/${trip.id}/simulate`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({event: 'weather'})})}>Simulate Rain</button>
          </div>
        </div>
        <MapComponent""")
    
    # insert websocket logic and live status UI in the Right Col
    ws_logic = """
  const [liveStatus, setLiveStatus] = useState("Not Started");
  const [liveMessages, setLiveMessages] = useState([]);
  
  useEffect(() => {
    if (!trip) return;
    const ws = new WebSocket(`ws://localhost:8000/api/monitor/ws/${trip.id}`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'trip_started') {
        setLiveStatus("Active - On schedule");
        setLiveMessages(prev => ["Trip started!", ...prev]);
      } else if (data.type === 'delay_detected') {
        setLiveStatus(`${data.payload.minutes} min behind schedule`);
        setLiveMessages(prev => [data.payload.message, ...prev]);
      } else if (data.type === 'weather_warning') {
        setLiveMessages(prev => [data.payload.message, ...prev]);
      }
    };
    return () => ws.close();
  }, [trip]);
"""
    app_jsx = app_jsx.replace("useEffect(() => {", ws_logic + "\n  useEffect(() => {", 1)
    
    live_ui = """
          <div className="mb-4 bg-gray-100 p-3 rounded border border-gray-300">
            <h3 className="font-bold text-gray-800 flex justify-between">
              <span>● LIVE Status</span>
              <span className="text-sm font-normal bg-gray-200 px-2 rounded text-gray-600">{liveStatus}</span>
            </h3>
            <div className="mt-2 text-sm text-gray-600 space-y-1">
              {liveMessages.slice(0,3).map((msg, idx) => (
                <div key={idx} className="border-l-2 border-blue-400 pl-2">{msg}</div>
              ))}
            </div>
            {liveStatus.includes('behind') && (
               <div className="mt-3 flex gap-2">
                 <button className="flex-1 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600">I'm okay</button>
                 <button className="flex-1 py-1 bg-orange-500 text-white rounded text-sm hover:bg-orange-600" onClick={() => simulateDisruption('stop-4')}>I'm stuck</button>
               </div>
            )}
          </div>
"""
    app_jsx = app_jsx.replace("</h2>", "</h2>\n" + live_ui)
    write_file(app_jsx_path, app_jsx)
