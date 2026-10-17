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

function MapBounds({ stops, candidates, currentLocation }) {
    const map = useMap();
    useEffect(() => {
        const bounds = L.latLngBounds();
        let hasPoints = false;
        if (stops && stops.length > 0) {
            stops.forEach(s => { bounds.extend([s.latitude, s.longitude]); hasPoints = true; });
        }
        if (candidates && candidates.length > 0) {
            candidates.forEach(c => { bounds.extend([c.latitude, c.longitude]); hasPoints = true; });
        }
        if (currentLocation) {
            bounds.extend([currentLocation.lat, currentLocation.lng]);
            hasPoints = true;
        }
        if (hasPoints) {
            map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
        }
    }, [map, stops, candidates, currentLocation]);
    return null;
}

export default function MapComponent({ stops = [], affectedStopId, candidates = [], selectedCandidateId, currentLocation, activeStopId, onStopClick }) {
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

  return (
    <div className="w-full h-full rounded-[2rem] overflow-hidden relative shadow-sm border border-slate-100 z-0">
      <MapContainer center={center} zoom={13} style={{ width: '100%', height: '100%' }} zoomControl={false}>
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
            const googleUrl = stop.place_id 
                ? `https://www.google.com/maps/dir/?api=1&destination=${stop.latitude},${stop.longitude}&destination_place_id=${stop.place_id}`
                : `https://www.google.com/maps/dir/?api=1&destination=${stop.latitude},${stop.longitude}`;
            
            return (
                <Marker key={stop.id} position={[stop.latitude, stop.longitude]} icon={icon} eventHandlers={{ click: () => onStopClick && onStopClick(stop.id) }}>
                    <Popup>
                        <strong>{stop.title}</strong><br/>
                        {stop.start_time} - {stop.end_time}<br/>
                        <a href={googleUrl} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-block', marginTop: '5px', padding: '2px 8px', backgroundColor: '#3b82f6', color: 'white', borderRadius: '4px', textDecoration: 'none', fontWeight: 'bold' }}>START</a>
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

        <MapBounds stops={validStops} candidates={candidates} currentLocation={currentLocation} />
      </MapContainer>

      <style dangerouslySetInnerHTML={{__html: `
        .map-tiles { filter: grayscale(20%) contrast(1.1) opacity(0.9); }
        .leaflet-container { background: #f8fafc; font-family: inherit; }
        .leaflet-popup-content-wrapper { border-radius: 12px; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1); }
      `}} />
    </div>
  );
}
