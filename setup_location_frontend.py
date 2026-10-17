import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

frontend_src = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\frontend\src"

# Rewrite App.jsx fully to ensure correct state and integration
app_jsx_content = """
import React, { useEffect, useState } from 'react';
import { useTripStore } from './store/tripStore';
import MapComponent from './components/MapComponent';

export default function App() {
  const { trip, fetchDemoTrip, simulateDisruption, disruption, impact, submitPreferences, candidates, selectCandidate } = useTripStore();
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);

  // Monitoring State
  const [liveStatus, setLiveStatus] = useState("Not Started");
  const [liveMessages, setLiveMessages] = useState([]);
  const [locationEnabled, setLocationEnabled] = useState(false);
  const [locationPermission, setLocationPermission] = useState("Prompt");
  const [currentLocation, setCurrentLocation] = useState(null);
  
  useEffect(() => {
    fetchDemoTrip();
  }, [fetchDemoTrip]);

  // WebSocket
  useEffect(() => {
    if (!trip) return;
    const ws = new WebSocket(`ws://localhost:8000/api/monitor/ws/${trip.id}`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'trip_started') {
        setLiveStatus("Active - On schedule");
        setLiveMessages(prev => ["Trip started!", ...prev]);
      } else if (data.type === 'delay_detected') {
        setLiveStatus(`${data.payload.minutes} min behind`);
        setLiveMessages(prev => [data.payload.message, ...prev]);
      } else if (data.type === 'weather_warning') {
        setLiveMessages(prev => [data.payload.message, ...prev]);
      } else if (data.type === 'stop_nearby') {
        setLiveMessages(prev => [data.payload.message, ...prev]);
      } else if (data.type === 'location_updated') {
        setCurrentLocation({lat: data.payload.latitude, lng: data.payload.longitude});
      }
    };
    return () => ws.close();
  }, [trip]);

  // Geolocation
  useEffect(() => {
    let watchId;
    if (locationEnabled && navigator.geolocation) {
      setLocationPermission("Active");
      watchId = navigator.geolocation.watchPosition(
        (pos) => {
          const loc = {
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            accuracy: pos.coords.accuracy,
            timestamp: new Date(pos.timestamp).toISOString()
          };
          // Send to backend
          if (trip) {
            fetch(`http://localhost:8000/api/monitor/${trip.id}/location`, {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify(loc)
            });
          }
        },
        (err) => {
          console.error("GPS Error", err);
          setLocationPermission("Denied/Error");
        },
        { enableHighAccuracy: true, maximumAge: 10000, timeout: 5000 }
      );
    }
    return () => {
      if (watchId) navigator.geolocation.clearWatch(watchId);
    };
  }, [locationEnabled, trip]);

  const handleValidate = async () => {
    setIsValidating(true);
    try {
      const res = await fetch(`http://localhost:8000/api/trips/${trip.id}/validate`, { method: 'POST' });
      const data = await res.json();
      setValidationResult(data);
    } catch (e) {
      console.error(e);
    }
    setIsValidating(false);
  };

  if (!trip) return <div className="p-8">Loading...</div>;

  const stops = trip.days[0].stops;

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans p-8 flex flex-col md:flex-row gap-8">
      {/* LEFT COL */}
      <div className="flex-1 space-y-6">
        <h1 className="text-3xl font-bold">Trip to {trip.destination}</h1>
        
        <div className="flex gap-4 items-center">
            <button onClick={handleValidate} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            {isValidating ? 'Checking itinerary...' : 'Validate Itinerary'}
            </button>
            <div className="text-sm px-3 py-1 bg-gray-200 rounded">
                📍 Location tracking: 
                <span className={`ml-1 font-bold ${locationPermission==='Active' ? 'text-green-600' : 'text-orange-600'}`}>
                    {locationPermission}
                </span>
                {!locationEnabled && (
                    <button className="ml-2 text-blue-600 underline" onClick={() => setLocationEnabled(true)}>Enable</button>
                )}
            </div>
        </div>

        {validationResult && (
          <div className="bg-white p-4 rounded shadow border border-gray-200">
            <h3 className="font-bold mb-2">Validation Report</h3>
            {validationResult.valid ? (
              <div className="text-green-600">✓ All good!</div>
            ) : (
              <div className="text-orange-600">⚠ {validationResult.issues.length} issues found</div>
            )}
            {validationResult.issues.map(issue => (
              <div key={issue.id} className="mt-2 text-sm bg-orange-50 p-2 rounded border border-orange-100">
                <strong>{issue.severity}:</strong> {issue.message}<br/>
                <span className="text-gray-600">{issue.details}</span><br/>
                <span className="text-blue-600">{issue.suggested_action}</span>
              </div>
            ))}
          </div>
        )}

        <MapComponent 
          stops={stops} 
          affectedStopId={disruption?.affected_stop_id} 
          candidates={candidates}
          currentLocation={currentLocation}
        />

        <div className="bg-gray-800 text-white p-4 rounded-xl shadow mb-6">
          <h2 className="text-xl font-bold mb-2 flex items-center">
            <span className="text-red-500 mr-2">●</span> LIVE Trip Demo Panel
          </h2>
          <div className="flex gap-2 flex-wrap">
            <button className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm" onClick={() => fetch(`http://localhost:8000/api/monitor/${trip.id}/simulate`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({event: 'start'})})}>Start Trip</button>
            <button className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm" onClick={() => fetch(`http://localhost:8000/api/monitor/${trip.id}/simulate`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({event: 'delay', value: 18})})}>Simulate Delay</button>
            <button className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm" onClick={() => fetch(`http://localhost:8000/api/monitor/${trip.id}/simulate`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({event: 'weather'})})}>Simulate Rain</button>
            <button className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm" onClick={() => {
                 fetch(`http://localhost:8000/api/monitor/${trip.id}/location`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({latitude: 17.385, longitude: 78.486, accuracy: 10, timestamp: new Date().toISOString()})});
            }}>Simulate GPS Near Stop</button>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h2 className="text-xl font-semibold mb-4">Itinerary</h2>
          <div className="space-y-4 border-l-2 border-gray-200 ml-3 pl-4">
            {stops.map((stop) => (
              <div key={stop.id} className="relative">
                <div className={`absolute -left-6 w-4 h-4 rounded-full border-2 border-white ${stop.status === 'REPLACED' ? 'bg-green-500' : 'bg-blue-500'}`}></div>
                <div className={`p-4 rounded-lg border ${stop.id === impact?.affected_stop_id ? 'border-red-300 bg-red-50' : stop.status === 'REPLACED' ? 'border-green-300 bg-green-50' : 'border-gray-100'}`}>
                  <h3 className="font-semibold text-lg">{stop.title}</h3>
                  <p className="text-sm text-gray-500">{stop.start_time} - {stop.end_time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* RIGHT COL - AI Companion */}
      <div className="w-full md:w-96 space-y-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 sticky top-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            AI Companion
          </h2>

          <div className="mb-4 bg-gray-100 p-3 rounded border border-gray-300">
            <h3 className="font-bold text-gray-800 flex justify-between">
              <span>● LIVE Status</span>
              <span className="text-sm font-normal bg-gray-200 px-2 rounded text-gray-600">{liveStatus}</span>
            </h3>
            <div className="mt-2 text-sm text-gray-600 space-y-2">
              {liveMessages.slice(0,3).map((msg, idx) => (
                <div key={idx} className="border-l-2 border-blue-400 pl-2 bg-white p-1 rounded">
                    {msg}
                    {msg.includes('near') && (
                        <div className="mt-1"><button className="px-2 py-1 bg-green-500 text-white rounded text-xs">Mark Arrived</button></div>
                    )}
                </div>
              ))}
            </div>
            {liveStatus.includes('behind') && (
               <div className="mt-3 flex gap-2">
                 <button className="flex-1 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600">I'm okay</button>
                 <button className="flex-1 py-1 bg-orange-500 text-white rounded text-sm hover:bg-orange-600" onClick={() => simulateDisruption('stop-4')}>I'm stuck</button>
               </div>
            )}
          </div>
          
          {!impact && (
            <button
              onClick={() => simulateDisruption('stop-4')}
              className="w-full py-2 bg-red-100 text-red-700 rounded font-medium hover:bg-red-200 transition mt-4"
            >
              Simulate Weather Disruption
            </button>
          )}

          {impact && (
            <div className="mt-4 p-4 bg-orange-50 rounded border border-orange-200">
              <h3 className="font-bold text-orange-800">Disruption Detected</h3>
              <p className="text-sm text-orange-900 mt-1">{impact.message}</p>
              
              {!candidates.length && (
                <button
                  onClick={() => submitPreferences(['Indoor'])}
                  className="mt-4 w-full py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
                >
                  Find Indoor Alternatives
                </button>
              )}
            </div>
          )}

          {candidates.length > 0 && (
            <div className="mt-6 space-y-4">
              <h3 className="font-bold">Alternatives</h3>
              {candidates.map(cand => (
                <div key={cand.id} className="p-3 border rounded hover:border-blue-500 cursor-pointer" onClick={() => selectCandidate(cand.id)}>
                  <h4 className="font-semibold">{cand.name}</h4>
                  <p className="text-xs text-gray-600">{cand.why_recommended}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
"""
write_file(f"{frontend_src}/App.jsx", app_jsx_content)

map_patch = """
import React, { useState, useEffect } from 'react';
import { APIProvider, Map, AdvancedMarker } from '@vis.gl/react-google-maps';

export default function MapComponent({ stops, affectedStopId, candidates, selectedCandidateId, currentLocation }) {
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
  const [center, setCenter] = useState({ lat: 17.3850, lng: 78.4867 });

  useEffect(() => {
    if (stops && stops.length > 0) {
      setCenter({ lat: stops[0].latitude, lng: stops[0].longitude });
    }
  }, [stops]);

  if (!apiKey || apiKey === "your_google_maps_api_key_here") {
    return (
      <div className="w-full h-64 bg-gray-200 rounded flex items-center justify-center text-gray-500">
        Google Maps API Key Missing. Map Placeholder.
      </div>
    );
  }

  return (
    <APIProvider apiKey={apiKey}>
      <div className="w-full h-64 rounded overflow-hidden relative">
        <Map defaultZoom={13} center={center} mapId="DEMO_MAP_ID">
          {stops.map(stop => (
            <AdvancedMarker 
              key={stop.id} 
              position={{lat: stop.latitude, lng: stop.longitude}}
            >
              <div className={`p-2 rounded-full ${stop.id === affectedStopId ? 'bg-red-500' : 'bg-blue-500'} text-white text-xs`}>
                {stop.title.substring(0,2)}
              </div>
            </AdvancedMarker>
          ))}
          {candidates && candidates.map(cand => (
            <AdvancedMarker 
              key={cand.id} 
              position={{lat: cand.latitude, lng: cand.longitude}}
            >
              <div className={`p-2 rounded-full ${cand.id === selectedCandidateId ? 'bg-green-500' : 'bg-yellow-500'} text-white text-xs border border-white shadow`}>
                {cand.name.substring(0,2)}
              </div>
            </AdvancedMarker>
          ))}
          {currentLocation && (
            <AdvancedMarker position={currentLocation}>
                <div className="w-4 h-4 bg-blue-600 border-2 border-white rounded-full shadow-lg"></div>
            </AdvancedMarker>
          )}
        </Map>
      </div>
    </APIProvider>
  );
}
"""
write_file(f"{frontend_src}/components/MapComponent.jsx", map_patch)
