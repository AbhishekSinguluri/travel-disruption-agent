import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet's default icon issue in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom Icons
const createCustomIcon = (bgColor, text) => {
    return L.divIcon({
        className: 'custom-icon',
        html: `<div style="background-color: ${bgColor}; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">${text}</div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });
};

const blueIcon = createCustomIcon('#3b82f6', '');
const redIcon = createCustomIcon('#ef4444', '');
const yellowIcon = createCustomIcon('#eab308', '');
const greenIcon = createCustomIcon('#22c55e', '');
const dotIcon = L.divIcon({
    className: 'custom-icon',
    html: `<div style="background-color: #2563eb; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8]
});

function MapBounds({ stops, candidates, currentLocation, mapInstanceRef }) {
    const map = useMap();
    const hasInitialFitRef = React.useRef(false);
    const userInteractedRef = React.useRef(false);
    const lastStopsKeyRef = React.useRef('');

    useEffect(() => {
        if (mapInstanceRef) {
            mapInstanceRef.current = map;
        }
        const handleUserInteraction = () => {
            userInteractedRef.current = true;
        };
        map.on('zoomstart', handleUserInteraction);
        map.on('dragstart', handleUserInteraction);
        return () => {
            map.off('zoomstart', handleUserInteraction);
            map.off('dragstart', handleUserInteraction);
        };
    }, [map, mapInstanceRef]);

    const stopsKey = (stops || []).map(s => `${s.id}:${s.latitude?.toFixed(4)}:${s.longitude?.toFixed(4)}`).join('|');

    useEffect(() => {
        const bounds = L.latLngBounds();
        let hasPoints = false;

        const validStops = (stops || []).filter(s => s.latitude != null && s.longitude != null && s.status !== 'SKIPPED');
        
        // Calculate cluster center to exclude extreme distance outliers (>100km)
        let centerLat = 0, centerLng = 0;
        if (validStops.length > 0) {
            centerLat = validStops.reduce((sum, s) => sum + s.latitude, 0) / validStops.length;
            centerLng = validStops.reduce((sum, s) => sum + s.longitude, 0) / validStops.length;
        }

        validStops.forEach(s => {
            const dist = Math.hypot(s.latitude - centerLat, s.longitude - centerLng);
            if (dist < 1.0 || validStops.length <= 2) {
                bounds.extend([s.latitude, s.longitude]);
                hasPoints = true;
            }
        });

        if (candidates && candidates.length > 0) {
            candidates.forEach(c => {
                if (c.latitude != null && c.longitude != null) {
                    bounds.extend([c.latitude, c.longitude]);
                    hasPoints = true;
                }
            });
        }

        const isNewTrip = lastStopsKeyRef.current !== stopsKey;
        if (isNewTrip) {
            lastStopsKeyRef.current = stopsKey;
            userInteractedRef.current = false;
            hasInitialFitRef.current = false;
        }

        // Only auto-fit bounds on initial load of trip or if user hasn't zoomed manually
        if (hasPoints && (!hasInitialFitRef.current || (!userInteractedRef.current && isNewTrip))) {
            map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
            hasInitialFitRef.current = true;
        }
    }, [map, stops, candidates, stopsKey]);

    return null;
}

export default function MapComponent({ stops = [], affectedStopId, candidates = [], selectedCandidateId, currentLocation, activeStopId, onStopClick }) {
  const mapRef = React.useRef(null);
  const validStops = stops.filter(s => s.latitude != null && s.longitude != null && s.status !== 'SKIPPED');
  if (validStops.length === 0 && candidates.length === 0 && !currentLocation) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-100 rounded-[2rem] border border-slate-200">
        <p className="text-slate-500 font-serif italic">No mapped locations yet.</p>
      </div>
    );
  }
  const center = validStops.length > 0 ? [validStops[0].latitude, validStops[0].longitude] : (candidates.length > 0 ? [candidates[0].latitude, candidates[0].longitude] : [currentLocation.lat, currentLocation.lng]);
  const routePositions = validStops.map(s => [s.latitude, s.longitude]);

  const handleRecenter = () => {
    if (!mapRef.current) return;
    const bounds = L.latLngBounds();
    validStops.forEach(s => bounds.extend([s.latitude, s.longitude]));
    if (candidates && candidates.length > 0) {
      candidates.forEach(c => bounds.extend([c.latitude, c.longitude]));
    }
    if (bounds.isValid()) {
      mapRef.current.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
    }
  };

  return (
    <div className="w-full h-full rounded-[2rem] overflow-hidden relative shadow-sm border border-slate-100 z-0 group">
      <MapContainer center={center} zoom={13} style={{ width: '100%', height: '100%' }} zoomControl={true}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          className="map-tiles"
        />
        
        {routePositions.length > 1 && (
            <Polyline positions={routePositions} pathOptions={{ color: '#94a3b8', weight: 3, dashArray: '5, 10' }} />
        )}

        {validStops.map((stop, index) => {
            const num = index + 1;
            const icon = stop.id === affectedStopId ? createCustomIcon('#ef4444', num) : (stop.id === activeStopId ? createCustomIcon('#22c55e', num) : createCustomIcon('#3b82f6', num));
            const googleNavUrl = `https://www.google.com/maps/dir/?api=1&destination=${stop.latitude},${stop.longitude}`;
            const googleSearchUrl = `https://www.google.com/maps/search/?api=1&query=${stop.latitude},${stop.longitude}`;
            
            return (
                <Marker key={stop.id} position={[stop.latitude, stop.longitude]} icon={icon} eventHandlers={{ click: () => onStopClick && onStopClick(stop.id) }}>
                    <Popup>
                        <div className="p-0.5">
                            <strong className="text-sm font-serif block text-slate-900">{stop.title}</strong>
                            {stop.address && <p className="text-[11px] text-slate-500 my-1 leading-tight">{stop.address}</p>}
                            <span className="text-xs text-slate-600 block mb-2">{stop.start_time} - {stop.end_time}</span>
                            <div className="flex items-center gap-2">
                                <a 
                                    href={googleNavUrl} 
                                    target="_blank" 
                                    rel="noopener noreferrer" 
                                    style={{ display: 'inline-block', padding: '4px 10px', backgroundColor: '#2563eb', color: 'white', borderRadius: '6px', textDecoration: 'none', fontWeight: 'bold', fontSize: '11px' }}
                                    title="Start turn-by-turn navigation to exact GPS coordinates"
                                >
                                    NAVIGATE &rarr;
                                </a>
                                <a 
                                    href={googleSearchUrl} 
                                    target="_blank" 
                                    rel="noopener noreferrer" 
                                    style={{ display: 'inline-block', padding: '4px 8px', backgroundColor: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1', borderRadius: '6px', textDecoration: 'none', fontWeight: '500', fontSize: '11px' }}
                                    title="Open exact location on Google Maps"
                                >
                                    Google Maps ↗
                                </a>
                            </div>
                        </div>
                    </Popup>
                </Marker>
            );
        })}

        {candidates.map(cand => (
            <Marker key={cand.id} position={[cand.latitude, cand.longitude]} icon={cand.id === selectedCandidateId ? greenIcon : yellowIcon}>
                <Popup>
                    <strong>{cand.name}</strong><br/>
                    {cand.category}
                </Popup>
            </Marker>
        ))}

        {currentLocation && (
            <Marker position={[currentLocation.lat, currentLocation.lng]} icon={dotIcon}>
                <Popup>Current Location</Popup>
            </Marker>
        )}

        <MapBounds stops={validStops} candidates={candidates} currentLocation={currentLocation} mapInstanceRef={mapRef} />
      </MapContainer>

      {/* Recenter Button */}
      <button 
        type="button" 
        onClick={handleRecenter}
        className="absolute bottom-4 right-4 z-[400] bg-white/90 hover:bg-white text-slate-800 text-[11px] font-bold uppercase tracking-wider px-3 py-1.5 rounded-full shadow-md border border-slate-200 transition-all flex items-center gap-1.5 backdrop-blur-sm cursor-pointer"
        title="Fit whole route into view"
      >
        <svg className="w-3.5 h-3.5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>
        Recenter
      </button>

      <style dangerouslySetInnerHTML={{__html: `
        .map-tiles { filter: grayscale(20%) contrast(1.1) opacity(0.9); }
        .leaflet-container { background: #f8fafc; font-family: inherit; }
        .leaflet-popup-content-wrapper { border-radius: 12px; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1); }
        .leaflet-top.leaflet-left { top: 12px; left: 12px; }
        .leaflet-control-zoom { border: none !important; box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important; border-radius: 8px !important; overflow: hidden; }
        .leaflet-control-zoom a { background-color: rgba(255,255,255,0.95) !important; color: #1e293b !important; }
      `}} />
    </div>
  );
}
