import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

frontend_src = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\frontend\src"

map_component = """
import React, { useState, useEffect } from 'react';
import { APIProvider, Map, AdvancedMarker } from '@vis.gl/react-google-maps';

export default function MapComponent({ stops, affectedStopId, candidates, selectedCandidateId }) {
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
  const [center, setCenter] = useState({ lat: 17.3850, lng: 78.4867 });

  useEffect(() => {
    if (stops && stops.length > 0) {
      setCenter({ lat: stops[0].latitude, lng: stops[0].longitude });
    }
  }, [stops]);

  if (!apiKey) {
    return (
      <div className="w-full h-64 bg-gray-200 rounded flex items-center justify-center text-gray-500">
        Google Maps API Key Missing. Map Placeholder.
      </div>
    );
  }

  return (
    <APIProvider apiKey={apiKey}>
      <div className="w-full h-64 rounded overflow-hidden">
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
        </Map>
      </div>
    </APIProvider>
  );
}
"""
write_file(f"{frontend_src}/components/MapComponent.jsx", map_component)

app_update = """
import React, { useEffect, useState } from 'react';
import useTripStore from './store/tripStore';
import MapComponent from './components/MapComponent';

export default function App() {
  const { trip, fetchDemoTrip, simulateDisruption, disruption, impact, submitPreferences, candidates, selectCandidate } = useTripStore();
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);

  useEffect(() => {
    fetchDemoTrip();
  }, [fetchDemoTrip]);

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
        
        <button onClick={handleValidate} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          {isValidating ? 'Checking itinerary...' : 'Validate Itinerary'}
        </button>

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
        />

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
          
          {!impact && (
            <button
              onClick={() => simulateDisruption('stop-4')}
              className="w-full py-2 bg-red-100 text-red-700 rounded font-medium hover:bg-red-200 transition"
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
write_file(f"{frontend_src}/App.jsx", app_update)
