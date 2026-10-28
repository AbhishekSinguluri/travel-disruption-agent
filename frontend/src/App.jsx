import Spline from '@splinetool/react-spline';
import { motion } from 'framer-motion';
import React, { useEffect, useState } from 'react';

import VoiceItineraryModal from './components/VoiceItineraryModal';
import RomeBuddyDrawer from './components/RomeBuddyDrawer';
import { useTripStore } from './store/tripStore';
import { useAuthStore } from './store/authStore';
import DisruptionRecoveryCard from './components/DisruptionRecoveryCard';


import MapComponent from './components/MapComponent';
import LocalEventsSection from './components/LocalEventsSection';

export const getTripCoverImage = (t) => {
  if (!t) return '/images for rome/charminar.jpg';
  if (t.cover_image) return t.cover_image;
  if (t.image_url) return t.image_url;
  if (t.image) return t.image;
  
  const text = `${t.name || ''} ${t.destination || ''} ${t.days?.map(d => d.stops?.map(s => `${s.title || ''} ${s.location_name || ''} ${s.address || ''}`).join(' ')).join(' ') || ''}`.toLowerCase();
  
  if (text.includes('jaipur') || text.includes('rajasthan') || text.includes('jodhpur') || text.includes('udaipur') || text.includes('jaisalmer') || text.includes('hawa mahal') || text.includes('amber fort') || text.includes('amer')) {
    return '/images for rome/rajasthan.jpg';
  }
  if (text.includes('alleppey') || text.includes('kerala') || text.includes('alappuzha') || text.includes('kochi') || text.includes('munnar') || text.includes('wayanad') || text.includes('backwaters')) {
    return '/images for rome/kerala.jpg';
  }
  if (text.includes('delhi') || text.includes('qutub') || text.includes('india gate') || text.includes('red fort') || text.includes('connaught') || text.includes('humayun')) {
    return '/images for rome/delhi.jpg';
  }
  if (text.includes('goa') || text.includes('panaji') || text.includes('baga') || text.includes('calangute') || text.includes('anjuna') || text.includes('aguada') || text.includes('candolim')) {
    return '/images for rome/goa.jpg';
  }
  if (text.includes('mumbai') || text.includes('bombay') || text.includes('marine drive') || text.includes('gateway of india') || text.includes('colaba') || text.includes('bandra')) {
    return '/images for rome/mumbai.jpg';
  }
  if (text.includes('maharashtra') || text.includes('pune') || text.includes('lonavala') || text.includes('nashik') || text.includes('ajanta') || text.includes('ellora') || text.includes('shaniwar') || text.includes('sinhagad')) {
    return '/images for rome/maharashtra.jpg';
  }
  if (text.includes('tamil') || text.includes('tamilnadu') || text.includes('chennai') || text.includes('madurai') || text.includes('coimbatore') || text.includes('ooty') || text.includes('rameshwaram') || text.includes('mahabalipuram') || text.includes('kapaleeshwarar')) {
    return '/images for rome/tamilnadu.jpg';
  }
  if (text.includes('hyderabad') || text.includes('charminar') || text.includes('telangana') || text.includes('bachupally') || text.includes('hussain sagar') || text.includes('vnr') || text.includes('inorbit') || text.includes('banjara') || text.includes('jubilee') || text.includes('gachibowli') || text.includes('madhapur') || text.includes('falaknuma') || text.includes('secunderabad')) {
    return '/images for rome/charminar.jpg';
  }
  
  return '/images for rome/charminar.jpg';
};

export default function App() {
  const [activeStopId, setActiveStopId] = useState(null);
  const [selectedStateFilter, setSelectedStateFilter] = useState('ALL');
  const { isDemoMode, isAuthenticated, user, setUser } = useAuthStore();
  const [currentView, setCurrentView] = useState('TRIPS'); // TRIPS, DASHBOARD, LOGIN

  if (!isAuthenticated && !isDemoMode && currentView !== 'LOGIN') {
    setCurrentView('LOGIN');
  }

  const { trip, trips, loadDemoTrip, fetchTrips, saveTrip, loadTrip, updateTrip, deleteTrip, toggleStopCheck, sendCompanionMessage, simulateDisruption, impactAnalysis: impact, submitPreferences, selectCandidate, alerts, addAlert, markAlertRead, setDelayAlert, delayAlert } = useTripStore();
  const activeDisruption = useTripStore(state => state.activeDisruption);
  const recoveryCandidates = useTripStore(state => state.recoveryCandidates);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importText, setImportText] = useState("");
  const [importStatus, setImportStatus] = useState("");
  const [importError, setImportError] = useState(null);
  const [pendingTrip, setPendingTrip] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [showVoiceModal, setShowVoiceModal] = useState(false);
  const [isBookingVoiceListening, setIsBookingVoiceListening] = useState(false);
  const bookingMicStreamRef = React.useRef(null);
  const bookingRecognitionRef = React.useRef(null);
  const [exploreMenuOpen, setExploreMenuOpen] = useState(false);
  const [savedBookings, setSavedBookings] = useState([]);
  const exploreRef = React.useRef(null);
  const exploreTimerRef = React.useRef(null);
  const navBarRef = React.useRef(null);

  // Initialize WebGL LiquidGlass effect from @ybouane/liquidglass
  useEffect(() => {
    let instance = null;
    let isCancelled = false;

    async function initLiquidGlass() {
      try {
        if (!navBarRef.current) return;
        const parentRoot = navBarRef.current.parentElement;
        if (!parentRoot) return;

        const { LiquidGlass } = await import('@ybouane/liquidglass');
        if (isCancelled || !navBarRef.current) return;

        navBarRef.current.dataset.config = JSON.stringify({
          blurAmount: 0.25,
          refraction: 0.69,
          chromAberration: 0.05,
          edgeHighlight: 0.12,
          fresnel: 1.0,
          specular: 0.15,
          cornerRadius: 32,
          zRadius: 40,
          opacity: 1.0,
          saturation: 0.0,
          tintStrength: 0.02,
          brightness: 0.03,
          shadowOpacity: 0.2,
          shadowSpread: 12,
          shadowOffsetY: 2,
          floating: false,
          button: false,
        });

        instance = await LiquidGlass.init({
          root: parentRoot,
          glassElements: [navBarRef.current],
          defaults: {
            cornerRadius: 32,
            refraction: 0.69,
            blurAmount: 0.25,
          }
        });
      } catch (err) {
        console.debug('LiquidGlass WebGL shader initialized or active with CSS fallback');
      }
    }

    const timer = setTimeout(initLiquidGlass, 200);

    return () => {
      isCancelled = true;
      clearTimeout(timer);
      if (instance && typeof instance.destroy === 'function') {
        try { instance.destroy(); } catch (e) {}
      }
    };
  }, [currentView]);

  const handleExploreMouseEnter = () => {
    if (exploreTimerRef.current) {
      clearTimeout(exploreTimerRef.current);
      exploreTimerRef.current = null;
    }
    setExploreMenuOpen(true);
  };

  const handleExploreMouseLeave = () => {
    if (exploreTimerRef.current) {
      clearTimeout(exploreTimerRef.current);
    }
    exploreTimerRef.current = setTimeout(() => {
      setExploreMenuOpen(false);
    }, 250);
  };

  const handleExploreToggle = (e) => {
    e.stopPropagation();
    if (exploreTimerRef.current) {
      clearTimeout(exploreTimerRef.current);
      exploreTimerRef.current = null;
    }
    setExploreMenuOpen(prev => !prev);
  };

  const stopBookingVoiceRecording = () => {
    if (bookingMicStreamRef.current) {
      bookingMicStreamRef.current.getTracks().forEach(track => {
        try { track.stop(); } catch (e) {}
      });
      bookingMicStreamRef.current = null;
    }
    if (bookingRecognitionRef.current) {
      bookingRecognitionRef.current.onresult = null;
      bookingRecognitionRef.current.onerror = null;
      bookingRecognitionRef.current.onend = null;
      try { bookingRecognitionRef.current.stop(); } catch (e) {}
      bookingRecognitionRef.current = null;
    }
    setIsBookingVoiceListening(false);
  };

  const startBookingVoiceRecording = async () => {
    stopBookingVoiceRecording();

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      bookingMicStreamRef.current = stream;

      const recognition = new SpeechRecognition();
      bookingRecognitionRef.current = recognition;
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      let baseText = importText ? importText.trim() + " " : "";

      recognition.onresult = (event) => {
        let finalChunk = '';
        let interimChunk = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const item = event.results[i];
          if (item.isFinal) {
            finalChunk += item[0].transcript;
          } else {
            interimChunk += item[0].transcript;
          }
        }
        if (finalChunk) {
          baseText += finalChunk + " ";
          setImportText(baseText + interimChunk);
        } else {
          setImportText(baseText + interimChunk);
        }
      };

      recognition.onerror = (event) => {
        console.warn("Speech recognition error:", event.error);
        if (event.error !== 'no-speech') {
          stopBookingVoiceRecording();
        }
      };

      recognition.onend = () => {
        stopBookingVoiceRecording();
      };

      recognition.start();
      setIsBookingVoiceListening(true);
    } catch (err) {
      console.error("Microphone access error:", err);
      alert("Could not access microphone. Please allow microphone permissions in your browser.");
      stopBookingVoiceRecording();
    }
  };

  const toggleBookingVoiceRecording = () => {
    if (isBookingVoiceListening) {
      stopBookingVoiceRecording();
    } else {
      startBookingVoiceRecording();
    }
  };

  useEffect(() => {
    if (!showImportModal && isBookingVoiceListening) {
      stopBookingVoiceRecording();
    }
  }, [showImportModal, isBookingVoiceListening]);

  const fetchBookings = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/bookings');
      if (res.ok) {
        const data = await res.json();
        setSavedBookings(Array.isArray(data) ? data : []);
      }
    } catch (e) {
      console.error("Failed to fetch bookings:", e);
    }
  };

  useEffect(() => {
    fetchBookings();
    fetchTrips();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (exploreRef.current && !exploreRef.current.contains(event.target)) {
        if (exploreTimerRef.current) {
          clearTimeout(exploreTimerRef.current);
          exploreTimerRef.current = null;
        }
        setExploreMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      if (exploreTimerRef.current) {
        clearTimeout(exploreTimerRef.current);
      }
    };
  }, []);

  const handleDeleteBooking = async (bId) => {
    if (!window.confirm("Are you sure you want to delete this booking? This will remove the record and stop active monitoring.")) {
      return;
    }
    try {
      const res = await fetch(`http://localhost:8000/api/bookings/${bId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        setSavedBookings(prev => prev.filter(b => b.id !== bId));
        if (bookingSummary?.id === bId) {
          setBookingSummary(null);
        }
      }
    } catch (e) {
      console.error("Failed to delete booking:", e);
    }
  };

  const handleVoiceItinerarySubmit = async (transcribedText) => {
    setImporting(true);
    setImportStatus("Reading your journey...");
    setShowImportModal(true);
    setImportText(transcribedText);
    try {
      const res = await fetch('http://localhost:8000/api/import/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: transcribedText })
      });
      setImportStatus("Structuring your itinerary...");
      if (!res.ok) throw new Error("Failed to structure itinerary from voice");
      const extracted = await res.json();
      setPendingTrip(extracted);
      setImportStatus("Your journey is taking shape.");
    } catch (err) {
      console.error(err);
      setImportStatus("We couldn't structure that itinerary.");
    } finally {
      setImporting(false);
    }
  };

  useEffect(() => {
    if (trip?.days?.[0]?.stops) {
      const currentStops = trip.days[0].stops;
      const nextPhysical = currentStops.find(s => s.status !== 'COMPLETED' && s.latitude != null);
      if (nextPhysical) {
         setActiveStopId(prev => (prev === nextPhysical.id ? prev : nextPhysical.id));
      }
    }
  }, [trip]);

  const fileInputRef = React.useRef(null);
  const [importFileType, setImportFileType] = React.useState(null);

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setImporting(true);
    setImportError(null);
    setBookingSummary(null);
    setBookingMonitoringActive(false);
    try {
      const fd = new FormData();
      fd.append('file', file);
      
      if (monitoringMode === 'BOOKINGS') {
        const res = await fetch('http://localhost:8000/api/bookings/extract', {
          method: 'POST',
          body: fd
        });
        if (!res.ok) throw new Error('Failed to extract booking');
        const data = await res.json();
        setBookingSummary(data);
        setBookingId(data.id || data.flight_number || "mock-booking");
        fetchBookings();
      } else {
        // Monitoring mode TRIP (Upload Image)
        const res = await fetch(`http://localhost:8000/api/import/${importFileType}`, {
          method: 'POST',
          body: fd
        });
        if (!res.ok) throw new Error('Failed to import trip');
        const data = await res.json();
        
        loadDemoTrip();
        setShowImportModal(false);
      }
    } catch (err) {
      console.error("Import error:", err);
      if (err.message === "Failed to fetch") {
        setImportError("Unable to connect to the agent server.");
      } else if (err.message.includes("400") || err.message.includes("422")) {
        setImportError("The provided document is invalid or empty.");
      } else if (err.message.includes("500") || err.message.includes("extract")) {
        setImportError("The AI agent failed to process the document.");
      } else {
        setImportError(err.message || 'Failed to process import');
      }
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = null;
    }
  };


  // Monitoring State
  const [liveStatus, setLiveStatus] = useState("Not Started");
  const [liveMessages, setLiveMessages] = useState([]);
  const [chatMessagesByTrip, setChatMessagesByTrip] = useState({});
  const activeTripKey = trip?.id ? String(trip.id) : 'default';
  const chatMessages = chatMessagesByTrip[activeTripKey] || [];

  const [romeBuddyOpen, setRomeBuddyOpen] = useState(false);

  const appendChatMessage = (tripId, msg) => {
    const key = tripId ? String(tripId) : 'default';
    setChatMessagesByTrip(prev => ({
      ...prev,
      [key]: [...(prev[key] || []), msg]
    }));
  };

  const handleRomeBuddyMessage = async (messageText) => {
    const tId = trip?.id ? String(trip.id) : 'default';
    appendChatMessage(tId, { role: 'user', content: messageText });
    try {
      const reply = await sendCompanionMessage(trip?.id, messageText);
      appendChatMessage(tId, { role: 'assistant', content: reply });
      return reply;
    } catch (err) {
      appendChatMessage(tId, { role: 'assistant', content: "Error connecting to AI companion." });
      throw err;
    }
  };

  const handleRomeBuddyClear = () => {
    const tId = trip?.id ? String(trip.id) : 'default';
    setChatMessagesByTrip(prev => ({
      ...prev,
      [tId]: []
    }));
  };
  const [chatInput, setChatInput] = useState('');
  const [locationEnabled, setLocationEnabled] = useState(true);
  const [locationPermission, setLocationPermission] = useState("Prompt");
  const [currentLocation, setCurrentLocation] = useState(null);

  // Auto-sync or request browser geolocation permissions on mount
  useEffect(() => {
    if (typeof window !== 'undefined' && navigator.geolocation) {
      if (navigator.permissions && navigator.permissions.query) {
        navigator.permissions.query({ name: 'geolocation' }).then(result => {
          if (result.state === 'granted') {
            setLocationPermission('Active');
            setLocationEnabled(true);
          } else if (result.state === 'prompt') {
            setLocationPermission('Prompt');
          } else if (result.state === 'denied') {
            setLocationPermission('Denied');
          }
          result.onchange = () => {
            if (result.state === 'granted') {
              setLocationPermission('Active');
              setLocationEnabled(true);
            } else if (result.state === 'denied') {
              setLocationPermission('Denied');
            }
          };
        }).catch(() => {
          setLocationEnabled(true);
        });
      } else {
        setLocationEnabled(true);
      }
    }
  }, []);
  const [monitoringMode, setMonitoringMode] = useState('TRIP');
  const [bookingSummary, setBookingSummary] = useState(null);
  const [bookingId, setBookingId] = useState(null);
  const [gmailConnected, setGmailConnected] = useState(false);
  const [gmailEmail, setGmailEmail] = useState(null);
  const [importing, setImporting] = useState(false);
  const [bookingMonitoringActive, setBookingMonitoringActive] = useState(false);
  const [bookingAlert, setBookingAlert] = useState(null);
  const [isExtractingBuddyBooking, setIsExtractingBuddyBooking] = useState(false);
  const [isExtractingBuddyItinerary, setIsExtractingBuddyItinerary] = useState(false);
  const videoRef = React.useRef(null);
  
  const [autoMonitorStatus, setAutoMonitorStatus] = useState({ enabled: true, interval_seconds: 60, last_check_at: null });
  const [selectedAlertToAssess, setSelectedAlertToAssess] = useState(null);
  useEffect(() => {
    const fetchStatus = () => {
      fetch('http://localhost:8000/api/monitor/status')
        .then(res => res.json())
        .then(data => setAutoMonitorStatus(data))
        .catch(err => console.error("Failed to fetch monitor status", err));
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const setMonitorSettings = async (enabled, intervalSeconds) => {
    try {
      await fetch('http://localhost:8000/api/monitor/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled, interval_seconds: intervalSeconds })
      });
      setAutoMonitorStatus(prev => ({ ...prev, enabled, interval_seconds: intervalSeconds }));
    } catch(e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetch('http://localhost:8000/api/gmail/status')
      .then(res => res.json())
      .then(data => {
        if (data.connected) {
          setGmailConnected(true);
          setGmailEmail(data.email);
        } else {
          setGmailConnected(false);
          setGmailEmail(null);
        }
      })
      .catch(err => console.error("Failed to fetch Gmail status", err));
  }, []);

  const handleGmailDisconnect = () => {
    fetch('http://localhost:8000/api/gmail/disconnect', { method: 'POST' })
      .then(() => {
        setGmailConnected(false);
        setGmailEmail(null);
      })
      .catch(err => console.error("Failed to disconnect Gmail", err));
  };
  
  useEffect(() => {
    fetchTrips();
    loadDemoTrip();
  }, [fetchTrips, loadDemoTrip]);

  // WebSocket
  useEffect(() => {
    if (!trip || !trip.id || trip.id === 'undefined') return;
    const ws = new WebSocket(`ws://localhost:8000/api/monitor/ws/${trip.id}`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'trip_started') {
        setLiveStatus("Active - On schedule");
        setLiveMessages(prev => ["Trip started!", ...prev]);
      } else if (data.type === 'delay_detected') {
        const mins = data.payload.minutes || 15;
        setLiveStatus(`${mins} min behind`);
        setLiveMessages(prev => [data.payload.message, ...prev]);
        const stopId = data.payload.stop_id || trip?.days?.[0]?.stops?.find(s => s.status !== 'COMPLETED' && !s.completed)?.id;
        if (stopId && !useTripStore.getState().activeDisruption) {
          simulateDisruption('NORMAL_DELAY', stopId, mins);
        }
      } else if (data.type === 'weather_warning') {
        setLiveMessages(prev => [data.payload.message, ...prev]);
        const stopId = data.payload.stop_id || trip?.days?.[0]?.stops?.find(s => s.status !== 'COMPLETED' && !s.completed)?.id;
        if (stopId && !alertedWeatherStopsRef.current.has(stopId) && !useTripStore.getState().activeDisruption) {
          alertedWeatherStopsRef.current.add(stopId);
          simulateDisruption('WEATHER_DISRUPTION', stopId, 15);
        }
      } else if (data.type === 'stop_nearby') {
        setLiveMessages(prev => [data.payload.message, ...prev]);
        const stopId = data.payload.stop_id;
        if (stopId) {
          arrivedStopsRef.current.add(stopId);
          useTripStore.setState(state => {
            if (!state.trip) return state;
            const updated = JSON.parse(JSON.stringify(state.trip));
            updated.days?.forEach(d => {
              d.stops?.forEach(s => {
                if (s.id === stopId) {
                  s.status = 'COMPLETED';
                  s.completed = true;
                }
              });
            });
            return { trip: updated };
          });
        }
      } else if (data.type === 'location_updated') {
        setCurrentLocation({ lat: data.payload.latitude, lng: data.payload.longitude });
      } else if (data.type === 'booking_alert') {
        addAlert(data.payload);
        setBookingAlert(data.payload);
        setTimeout(() => setBookingAlert(null), 8000);
      } else if (data.type === 'recovery_required') {
        // Core Integration: Trigger Recovery workflow UI
        useTripStore.setState({
            activeDisruption: data.payload.disruption,
            impactAnalysis: data.payload.impact,
            recoveryCandidates: []
        });
        
        // Show alert and redirect to dashboard
        setBookingAlert({
            title: "Disruption Detected",
            message: "Impact analysis complete. Please view alternatives.",
            severity: "HIGH"
        });
        setTimeout(() => setBookingAlert(null), 5000);
        setCurrentView('DASHBOARD');
      }
    };
    return () => ws.close();
  }, [trip]);

  // Geolocation & Single Active Stop Proximity Verification
  const arrivedStopsRef = React.useRef(new Set());
  const alertedDelayStopsRef = React.useRef(new Set());
  const alertedWeatherStopsRef = React.useRef(new Set());

  useEffect(() => {
    let watchId;
    if (locationEnabled && typeof window !== 'undefined' && navigator.geolocation) {
      watchId = navigator.geolocation.watchPosition(
        (pos) => {
          const lat = pos.coords.latitude;
          const lng = pos.coords.longitude;
          setCurrentLocation({ lat, lng });
          setLocationPermission("Active");

          const loc = {
            latitude: lat,
            longitude: lng,
            accuracy: pos.coords.accuracy,
            timestamp: new Date(pos.timestamp).toISOString()
          };

          // Client-side single active stop proximity check (within 400m)
          // ONLY checks the active upcoming stop. NEVER auto-completes other stops!
          if (trip?.days && trip.days[0]?.stops) {
            const activeStop = trip.days[0].stops.find(s => s.status !== 'COMPLETED' && !s.completed);
            if (activeStop && activeStop.latitude && activeStop.longitude) {
              const R = 6371e3;
              const φ1 = (lat * Math.PI) / 180;
              const φ2 = (activeStop.latitude * Math.PI) / 180;
              const Δφ = ((activeStop.latitude - lat) * Math.PI) / 180;
              const Δλ = ((activeStop.longitude - lng) * Math.PI) / 180;
              const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
                        Math.cos(φ1) * Math.cos(φ2) *
                        Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
              const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
              const dist = R * c;

              // Only verify if within 400m and not already verified
              if (dist <= 400 && !arrivedStopsRef.current.has(activeStop.id)) {
                arrivedStopsRef.current.add(activeStop.id);
                useTripStore.setState(state => {
                  if (!state.trip) return state;
                  const updated = JSON.parse(JSON.stringify(state.trip));
                  updated.days?.forEach(d => {
                    d.stops?.forEach(s => {
                      if (s.id === activeStop.id) {
                        s.status = 'COMPLETED';
                        s.completed = true;
                      }
                    });
                  });
                  return { trip: updated };
                });
                setLiveMessages(prev => [`📍 Geotag Verified: You have arrived at ${activeStop.title}! Checked in itinerary.`, ...prev]);
              }
            }
          }

          // Send to backend
          if (trip && trip.id) {
            fetch(`http://localhost:8000/api/monitor/${trip.id}/location`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(loc)
            }).catch(e => console.warn("Location send error:", e));
          }
        },
        (err) => {
          console.warn("GPS Warning:", err.message);
          if (err.code === 1) {
            setLocationPermission("Denied");
          } else {
            setLocationPermission("Prompt");
          }
        },
        { enableHighAccuracy: true, maximumAge: 1000, timeout: 15000 }
      );
    }
    return () => {
      if (watchId && navigator.geolocation) navigator.geolocation.clearWatch(watchId);
    };
  }, [locationEnabled, trip?.id]);

  // Real-Time Schedule & Disruption Monitor (Continuous wall-clock & geotag assessment)
  useEffect(() => {
    if (!trip || !trip.days || !trip.days[0]?.stops) return;

    const parseTimeToMinutes = (timeStr) => {
      if (!timeStr || typeof timeStr !== 'string') return null;
      const cleaned = timeStr.trim().toLowerCase();
      const isPM = cleaned.includes('pm');
      const isAM = cleaned.includes('am');
      const timeOnly = cleaned.replace(/[^\d:]/g, '');
      const parts = timeOnly.split(':');
      if (parts.length < 2) return null;
      let hours = parseInt(parts[0], 10);
      const minutes = parseInt(parts[1], 10);
      if (isNaN(hours) || isNaN(minutes)) return null;
      if (isPM && hours < 12) hours += 12;
      if (isAM && hours === 12) hours = 0;
      return hours * 60 + minutes;
    };

    const checkRealTimeSchedule = () => {
      const now = new Date();
      const currentMinutes = now.getHours() * 60 + now.getMinutes();

      const stops = trip.days[0].stops || [];
      // Find the first uncompleted stop that has a scheduled start time
      const activeStop = stops.find(s => s.status !== 'COMPLETED' && !s.completed);
      if (!activeStop) return;

      // Check if user is physically at the stop
      let isAtLocation = false;
      let distMeters = 999999;
      if (currentLocation && activeStop.latitude && activeStop.longitude) {
        const R = 6371e3;
        const φ1 = (currentLocation.lat * Math.PI) / 180;
        const φ2 = (activeStop.latitude * Math.PI) / 180;
        const Δφ = ((activeStop.latitude - currentLocation.lat) * Math.PI) / 180;
        const Δλ = ((activeStop.longitude - currentLocation.lng) * Math.PI) / 180;
        const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
                  Math.cos(φ1) * Math.cos(φ2) *
                  Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        distMeters = R * c;
        if (distMeters <= 400) {
          isAtLocation = true;
        }
      }

      // If user is at location, verify arrival for ONLY this active stop
      if (isAtLocation) {
        if (!arrivedStopsRef.current.has(activeStop.id)) {
          arrivedStopsRef.current.add(activeStop.id);
          useTripStore.setState(state => {
            if (!state.trip) return state;
            const updated = JSON.parse(JSON.stringify(state.trip));
            updated.days?.forEach(d => {
              d.stops?.forEach(s => {
                if (s.id === activeStop.id) {
                  s.status = 'COMPLETED';
                  s.completed = true;
                }
              });
            });
            return { trip: updated };
          });
          setLiveMessages(prev => [`📍 Geotag Verified: You have arrived at ${activeStop.title}! Checked in itinerary.`, ...prev]);
        }
        return;
      }

      // User is in a DIFFERENT place (distMeters > 400m / not arrived)
      // When wall-clock time has reached or passed scheduled start time:
      const scheduledMinutes = parseTimeToMinutes(activeStop.start_time);
      if (scheduledMinutes !== null && currentMinutes >= scheduledMinutes) {
        const diffMins = currentMinutes - scheduledMinutes;
        const delayMins = Math.max(15, diffMins > 0 ? diffMins : 15);

        // Update Rome Buddy live status immediately
        setLiveStatus(`${delayMins} min behind`);

        // Check if we haven't popped the disruption card for this stop yet
        if (!alertedDelayStopsRef.current.has(activeStop.id) && !useTripStore.getState().activeDisruption) {
          alertedDelayStopsRef.current.add(activeStop.id);

          const timeDisplay = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
          const kmAway = distMeters < 999999 ? ` (${(distMeters / 1000).toFixed(1)} km away)` : '';
          const delayMsg = `⚠️ Real-Time Disruption: It is ${timeDisplay} and geotag finds your location in a different place${kmAway}. You haven't arrived at ${activeStop.title} (scheduled for ${activeStop.start_time}). You are ${delayMins} min behind schedule!`;
          setLiveMessages(prev => [delayMsg, ...prev]);

          // Trigger Disruption Recovery popup!
          simulateDisruption('NORMAL_DELAY', activeStop.id, delayMins);
        }
      }
    };

    checkRealTimeSchedule();
    const scheduleInterval = setInterval(checkRealTimeSchedule, 3000);
    return () => clearInterval(scheduleInterval);
  }, [trip?.id, currentLocation]);

  // Real-Time OpenWeather Live Disruption Monitor (Checks upcoming stops)
  useEffect(() => {
    if (!trip || !trip.id || trip.id === 'undefined' || !trip.days || !trip.days[0]?.stops) return;

    const checkRealTimeWeather = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/monitor/${trip.id}/weather`);
        if (!res.ok) return;
        const data = await res.json();
        const weatherList = data.stops_weather || [];

        const uncompletedStops = trip.days[0].stops.filter(s => s.status !== 'COMPLETED' && !s.completed);
        for (const stop of uncompletedStops) {
          const w = weatherList.find(item => item.stop_id === stop.id);
          if (w && w.is_raining) {
            // Trigger popup ONLY ONCE for each stop
            if (!alertedWeatherStopsRef.current.has(stop.id) && !useTripStore.getState().activeDisruption) {
              alertedWeatherStopsRef.current.add(stop.id);
              
              const rainMsg = `🌧 Live OpenWeather Alert: Rain detected at ${stop.title} (${w.description || 'Rain'}, ${w.temperature || 24}°C). Outdoor activities may be disrupted!`;
              setLiveMessages(prev => [rainMsg, ...prev]);
              
              // Automatically trigger the weather disruption popup once!
              simulateDisruption('WEATHER_DISRUPTION', stop.id, 15);
              break;
            }
          }
        }
      } catch (err) {
        console.warn("Weather check error:", err);
      }
    };

    checkRealTimeWeather();
    const weatherInterval = setInterval(checkRealTimeWeather, 15000);
    return () => clearInterval(weatherInterval);
  }, [trip?.id]);

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



  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const { login, signup, loading, error, logout } = useAuthStore();

  
  const renderLogin = () => (
    <div className="min-h-screen flex items-center justify-center bg-[#E5DED2] p-4 relative overflow-hidden">
      <div className="absolute inset-0 z-0">
        <img src="/login%20page%20bg.jpg" className="w-full h-full object-cover opacity-25" alt="Background" />
      </div>
      <div className="bg-white p-10 rounded-[2rem] shadow-2xl max-w-md w-full z-10 relative">
          <div className="text-center mb-8">
          <h1 className="text-4xl font-serif text-slate-900 tracking-tight mb-2">ROAM</h1>
          <p className="text-slate-500 font-light tracking-wide uppercase text-xs">Your Journeys</p>
        </div>
        

        
        <div className="space-y-4 mb-6">
          <input 
            type="text" 
            placeholder="Full Name (for signup)" 
            className="w-full p-4 bg-slate-50 border border-slate-100 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:bg-white transition-all"
            value={name} 
            onChange={(e) => setName(e.target.value)} 
          />
          <input 
            type="email" 
            placeholder="Email address" 
            className="w-full p-4 bg-slate-50 border border-slate-100 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:bg-white transition-all"
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
          />
          <input 
            type="tel" 
            placeholder="Phone Number (for signup)" 
            className="w-full p-4 bg-slate-50 border border-slate-100 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:bg-white transition-all"
            value={phone} 
            onChange={(e) => setPhone(e.target.value)} 
          />
          <input 
            type="password" 
            placeholder="Password" 
            className="w-full p-4 bg-slate-50 border border-slate-100 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:bg-white transition-all"
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            onKeyDown={(e) => e.key === 'Enter' && login(email, password)}
          />
        </div>
        
        <div className="space-y-3">
          <button 
            onClick={() => { login(email, password); setCurrentView('TRIPS'); }} 
            disabled={loading || !email || !password} 
            className="w-full bg-slate-900 text-white py-4 rounded-xl font-bold tracking-wide hover:bg-slate-800 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
          
          <button 
            onClick={() => { signup(email, password); setCurrentView('TRIPS'); }} 
            disabled={loading || !email || !password || !name || !phone} 
            className="w-full bg-white text-slate-900 border border-slate-200 py-4 rounded-xl font-bold tracking-wide hover:bg-slate-50 transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Create Account
          </button>
          
          <div className="relative flex py-4 items-center">
            <div className="flex-grow border-t border-slate-200"></div>
            <span className="flex-shrink-0 mx-4 text-slate-400 text-sm">or</span>
            <div className="flex-grow border-t border-slate-200"></div>
          </div>
          
          <button 
            onClick={() => { 
                fetch("http://localhost:8000/api/auth/google/login", { method: 'POST', body: JSON.stringify({mock: true}) })
                  .then(() => { setUser({ id: 'google-user', email: email || 'demo@gmail.com', name: name || 'Demo User' }); setCurrentView('TRIPS'); })
            }} 
            className="w-full bg-white text-slate-700 border border-slate-200 py-4 rounded-xl font-bold tracking-wide hover:bg-slate-50 transition-all shadow-sm flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Continue with Google
          </button>
          
          <button 
            onClick={() => { login('demo', 'demo'); setCurrentView('TRIPS'); }} 
            className="w-full mt-4 text-xs font-bold uppercase tracking-widest text-slate-400 hover:text-slate-600 transition-colors"
          >
            Continue in Demo Mode
          </button>
        </div>
      </div>
    </div>
  );
const renderTripsDummy = () => (

    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded shadow-md w-96 text-center">
        <h2 className="text-2xl font-bold mb-4">Login to Trip Agent</h2>

          <div className="mb-4 bg-gray-100 p-3 rounded border border-gray-300">
            <h3 className="font-bold text-gray-800 flex justify-between">
              <span>●  LIVE Status</span>
              <span className="text-sm font-normal bg-gray-200 px-2 rounded text-gray-600">{liveStatus}</span>
            </h3>
            <div className="mt-2 text-sm text-gray-600 space-y-1">
              {liveMessages.slice(0,3).map((msg, idx) => (
                <div key={idx} className="border-l-2 border-blue-400 pl-2">{msg}</div>
              ))}
            </div>
            
          </div>

        <p className="text-gray-500 mb-6">Supabase credentials not fully configured. Using DEMO MODE.</p>
        <button onClick={() => { setUser({ id: 'demo-user', email: 'demo@example.com' }); setCurrentView('TRIPS'); }} className="w-full bg-blue-600 text-white py-2 rounded">
          Continue in Demo Mode
        </button>
      </div>
    </div>
  );


  
  

  
  const handleImport = (type) => {
    setImportFileType(type);
    if (fileInputRef.current) {
      fileInputRef.current.accept = type === 'pdf' ? '.pdf' : 'image/*';
      fileInputRef.current.value = null;
      fileInputRef.current.click();
    }
  };


    const handleImportTextSubmit = async () => {
      if (!importText) return;
      setImporting(true);
      setImportStatus("Reading your journey...");
      try {
        const res = await fetch('http://localhost:8000/api/import/text', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({text: importText})
        });
        setImportStatus("Structuring your itinerary...");
        if (!res.ok) throw new Error("Failed to parse");
        const extracted = await res.json();
        setPendingTrip(extracted);
        setImportStatus("Your journey is taking shape.");
      } catch(e) {
        console.error(e);
        setImportStatus("We couldn't structure that itinerary.");
      }
      setImporting(false);
    };
    
    const handleExtractBooking = async () => {
      if (!importText) return;
      setImporting(true);
      setImportError(null);
      setBookingSummary(null);
      setBookingMonitoringActive(false);
      try {
        const fd = new FormData();
        fd.append('text', importText);
        const res = await fetch('http://localhost:8000/api/bookings/extract', {
          method: 'POST',
          body: fd
        });
        if (!res.ok) throw new Error("Failed to extract");
        const data = await res.json();
        setBookingSummary(data);
        setBookingId(data.id || data.flight_number || "mock-booking");
        setShowImportModal(false);
        setImportText("");
        fetchBookings();
      } catch (err) {
        console.error("Extraction error:", err);
        if (err.message === "Failed to fetch") {
          setImportError("Unable to connect to the agent server.");
        } else if (err.message.includes("400") || err.message.includes("422")) {
          setImportError("The provided document is invalid or empty.");
        } else if (err.message.includes("500") || err.message.includes("extract")) {
          setImportError("The AI agent failed to process the document.");
        } else {
          setImportError(err.message || 'Failed to extract booking');
        }
      } finally {
        setImporting(false);
      }
    };
    
    const handleExtractItineraryFromRomeBuddy = async (itineraryText) => {
      if (!itineraryText) return;
      setIsExtractingBuddyItinerary(true);

      // 1. Switch to Trips view with MONITOR TRIP selected
      setCurrentView('TRIPS');
      setMonitoringMode('TRIP');

      // 2. Put the generated itinerary into the text section
      setImportText(itineraryText);

      // 3. Open the import modal so the user visibly sees the text section populated
      setShowImportModal(true);
      setImportStatus("⚡ Rome Buddy: Transferring itinerary to Trip Structuring Engine...");
      setImportError(null);
      setImporting(true);

      // 4. Automatically trigger itinerary structuring after a brief visual delay
      setTimeout(async () => {
        try {
          setImportStatus("⚡ Rome Buddy: Structuring itinerary stops and timings...");
          const res = await fetch('http://localhost:8000/api/import/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: itineraryText })
          });

          if (!res.ok) throw new Error("Failed to structure itinerary");
          const extracted = await res.json();

          // 5. Automatically save the structured itinerary as a canonical Trip in the database
          await saveTrip(extracted);
          await fetchTrips();

          if (extracted.id) {
            await loadTrip(extracted.id);
          }

          // 6. Close modal and clear import states
          setShowImportModal(false);
          setImportText("");
          setImportStatus("");
          setImporting(false);
          setIsExtractingBuddyItinerary(false);

          // 7. Navigate directly to Explore -> Trips so the user sees the saved trip!
          setCurrentView('EXPLORE_TRIPS');

          // 8. Post confirmation message in Rome Buddy chat
          const tId = extracted.id ? String(extracted.id) : (trip?.id ? String(trip.id) : 'default');
          const tripName = extracted.name || extracted.destination || "Trip";
          const totalStops = extracted.days?.reduce((acc, d) => acc + (d.stops?.length || 0), 0) || 0;
          appendChatMessage(tId, {
            role: 'assistant',
            content: `⚡ **Itinerary Extracted into Trips!**\nI've automatically structured **${tripName}** (${totalStops} stops) and saved it into **Explore → Trips**!`
          });
        } catch (err) {
          console.error("Agentic itinerary extraction error:", err);
          setImportError(err.message || 'Failed to structure itinerary');
          setImporting(false);
          setIsExtractingBuddyItinerary(false);
        }
      }, 650);
    };

    const handleExtractBookingFromRomeBuddy = async (bookingText) => {
      if (!bookingText) return;
      setIsExtractingBuddyBooking(true);

      // 1. Ensure user is in TRIPS view with MONITOR BOOKINGS selected
      setCurrentView('TRIPS');
      setMonitoringMode('BOOKINGS');

      // 2. Put the generated text into the text section
      setImportText(bookingText);

      // 3. Open the import modal so the user visibly sees the text section populated
      setShowImportModal(true);
      setImportStatus("⚡ Rome Buddy transferring booking details to text section...");
      setImportError(null);
      setImporting(true);

      // 4. Automatically trigger extraction after a brief visual delay so user sees the automated action
      setTimeout(async () => {
        try {
          setImportStatus("⚡ Rome Buddy: Extracting booking from text...");
          const fd = new FormData();
          fd.append('text', bookingText);
          const res = await fetch('http://localhost:8000/api/bookings/extract', {
            method: 'POST',
            body: fd
          });

          if (!res.ok) throw new Error("Failed to extract booking");
          const data = await res.json();

          // Update booking summary & active booking ID
          setBookingSummary(data);
          setBookingId(data.id || data.flight_number || "itinerary-booking");

          // Close modal and clear import states so dashboard immediately shows booking card
          setShowImportModal(false);
          setImportText("");
          setImportStatus("");
          setImporting(false);
          setIsExtractingBuddyBooking(false);

          // Refresh saved bookings list so it's persisted in the system and visible in Explore Bookings
          await fetchBookings();

          // Post a confirmation message in Rome Buddy chat
          const tId = trip?.id ? String(trip.id) : 'default';
          const providerName = data.provider || "Booking";
          const routeDesc = data.origin && data.destination ? ` (${data.origin} → ${data.destination})` : '';
          const refDesc = data.booking_reference ? ` • Ref: ${data.booking_reference}` : '';
          appendChatMessage(tId, {
            role: 'assistant',
            content: `⚡ **Booking Extracted!**\nI've automatically extracted and saved **${providerName}**${routeDesc}${refDesc} as an active booking under **Explore → Bookings**.`
          });
        } catch (err) {
          console.error("Agentic booking extraction error:", err);
          setImportError(err.message || 'Failed to extract booking');
          setImporting(false);
          setIsExtractingBuddyBooking(false);
        }
      }, 650);
    };

  const handleSaveTrip = async () => {
    if (!pendingTrip) return;
    await saveTrip(pendingTrip);
    setPendingTrip(null);
    setShowImportModal(false);
    setImportText("");
  };
  const renderExploreDropdown = (currentActive = 'TRIPS') => {
    const isExploreActive = currentActive === 'EXPLORE_TRIPS' || currentActive === 'EXPLORE_BOOKINGS';
    return (
      <div 
        className="relative inline-block"
        ref={exploreRef}
        onMouseEnter={handleExploreMouseEnter}
        onMouseLeave={handleExploreMouseLeave}
      >
        <button 
          type="button"
          onClick={handleExploreToggle}
          className={`cursor-pointer flex items-center gap-1.5 focus:outline-none transition-all px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider ${
            isExploreActive
              ? 'bg-slate-900 text-white shadow-xs'
              : 'liquid-glass-pill text-slate-700 hover:text-slate-950'
          }`}
          aria-haspopup="true"
          aria-expanded={exploreMenuOpen}
        >
          <span>Explore</span>
          <svg 
            className={`w-3.5 h-3.5 transition-transform duration-150 ${exploreMenuOpen ? 'rotate-180' : ''} ${isExploreActive ? 'text-white' : 'opacity-60'}`} 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {exploreMenuOpen && (
          <div 
            className="absolute left-0 top-full -mt-1 pt-2 z-50 w-52"
            onMouseEnter={handleExploreMouseEnter}
            onMouseLeave={handleExploreMouseLeave}
          >
            <div 
              className="liquid-glass-bar bg-white/90 backdrop-blur-2xl rounded-2xl shadow-xl p-1.5 ring-1 ring-black/5 animate-in fade-in duration-150"
              role="menu"
            >
              <button
                type="button"
                onClick={() => { 
                  if (exploreTimerRef.current) clearTimeout(exploreTimerRef.current);
                  setExploreMenuOpen(false); 
                  setCurrentView('EXPLORE_TRIPS'); 
                }}
                className={`w-full text-left px-3.5 py-2.5 text-xs font-bold uppercase tracking-wider rounded-xl flex items-center justify-between transition-colors ${
                  currentActive === 'EXPLORE_TRIPS'
                    ? 'bg-slate-900 text-white font-extrabold shadow-xs'
                    : 'text-slate-700 hover:bg-slate-100/80 hover:text-slate-900'
                }`}
                role="menuitem"
              >
                <span>Trips</span>
                <span className={`text-[10px] font-normal ${currentActive === 'EXPLORE_TRIPS' ? 'text-slate-300' : 'text-slate-400'}`}>({trips.length})</span>
              </button>
              <button
                type="button"
                onClick={() => { 
                  if (exploreTimerRef.current) clearTimeout(exploreTimerRef.current);
                  setExploreMenuOpen(false); 
                  setCurrentView('EXPLORE_BOOKINGS'); 
                }}
                className={`w-full text-left px-3.5 py-2.5 text-xs font-bold uppercase tracking-wider rounded-xl flex items-center justify-between transition-colors ${
                  currentActive === 'EXPLORE_BOOKINGS'
                    ? 'bg-slate-900 text-white font-extrabold shadow-xs'
                    : 'text-slate-700 hover:bg-slate-100/80 hover:text-slate-900'
                }`}
                role="menuitem"
              >
                <span>Bookings</span>
                <span className={`text-[10px] font-normal ${currentActive === 'EXPLORE_BOOKINGS' ? 'text-slate-300' : 'text-slate-400'}`}>({savedBookings.length})</span>
              </button>
              <button
                type="button"
                onClick={() => { 
                  if (exploreTimerRef.current) clearTimeout(exploreTimerRef.current);
                  setExploreMenuOpen(false); 
                  setCurrentView('LOCAL_EVENTS'); 
                }}
                className={`w-full text-left px-3.5 py-2.5 text-xs font-bold uppercase tracking-wider rounded-xl flex items-center justify-between transition-colors ${
                  currentActive === 'LOCAL_EVENTS'
                    ? 'bg-slate-900 text-white font-extrabold shadow-xs'
                    : 'text-slate-700 hover:bg-slate-100/80 hover:text-slate-900'
                }`}
                role="menuitem"
              >
                <span>Live Events & Shows</span>
                <span className="text-[10px] text-amber-600 font-bold">Live</span>
              </button>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderTopNavBar = (view = currentView) => (
    <div className="sticky top-0 z-40 w-full px-4 sm:px-8 pt-3.5 pb-2 pointer-events-none">
      <header 
        ref={navBarRef}
        data-liquid-glass
        className="liquid-glass-bar max-w-7xl mx-auto rounded-[2rem] px-6 sm:px-8 py-3 flex justify-between items-center text-slate-800 transition-all pointer-events-auto"
      >
        <div className="relative z-10 w-full flex justify-between items-center">
          <div className="flex items-center gap-6 sm:gap-8">
            <div 
              className="font-serif font-bold text-2xl tracking-widest cursor-pointer text-slate-900 hover:opacity-80 transition-opacity flex items-center gap-2 select-none" 
              onClick={() => setCurrentView('TRIPS')}
            >
              ROAM
            </div>
            
            <nav className="hidden md:flex gap-2 text-sm font-medium tracking-wide items-center">
              <button 
                type="button"
                onClick={() => setCurrentView('TRIPS')}
                className={`cursor-pointer transition-all px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                  view === 'TRIPS' 
                    ? 'bg-slate-900 text-white shadow-xs' 
                    : 'liquid-glass-pill text-slate-700 hover:text-slate-950'
                }`}
              >
                Trip
              </button>
              
              {renderExploreDropdown(view)}

              <button 
                type="button"
                onClick={() => setCurrentView('LOCAL_EVENTS')}
                className={`cursor-pointer transition-all px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 ${
                  view === 'LOCAL_EVENTS' 
                    ? 'bg-slate-900 text-white shadow-xs' 
                    : 'liquid-glass-pill text-slate-700 hover:text-slate-950'
                }`}
              >
                <span>🎪</span>
                <span>Live Events</span>
              </button>

              <button 
                type="button" 
                onClick={() => setRomeBuddyOpen(true)} 
                className="cursor-pointer liquid-glass-pill text-slate-700 hover:text-slate-950 px-3.5 py-1.5 rounded-full flex items-center gap-2 focus:outline-none transition-all group"
              >
                <img src="/rome_buddy_logo.png" alt="RB" className="w-5 h-5 rounded-full object-contain border border-slate-300 group-hover:scale-110 transition-transform bg-white shadow-xs" />
                <span className="text-xs font-bold uppercase tracking-wider">Rome Buddy</span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              </button>
            </nav>
          </div>

          <div className="flex items-center gap-3 sm:gap-4">
            {isDemoMode ? (
              <span className="bg-amber-100/90 text-amber-900 border border-amber-200/80 px-3 py-1 rounded-full font-bold text-[11px] uppercase tracking-wider shadow-2xs">
                Demo
              </span>
            ) : (
              <span className="bg-emerald-100/90 text-emerald-900 border border-emerald-200/80 px-3 py-1 rounded-full font-bold text-[11px] uppercase tracking-wider shadow-2xs">
                Live
              </span>
            )}

            <button 
              onClick={() => setCurrentView('ALERTS')} 
              className={`text-xs font-bold uppercase tracking-widest px-3.5 py-1.5 rounded-full transition-all relative ${
                view === 'ALERTS'
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'liquid-glass-pill text-slate-700 hover:text-slate-950'
              }`}
            >
              ALERTS
              {alerts.some(a => !a.is_read) && (
                <span className="absolute top-1 right-1.5 w-2 h-2 rounded-full bg-orange-500 ring-2 ring-white"></span>
              )}
            </button>

            <button 
              onClick={() => { logout(); setCurrentView('LOGIN'); }} 
              className="text-xs font-bold uppercase tracking-widest text-slate-500 hover:text-red-600 hover:bg-red-50/80 px-3.5 py-1.5 rounded-full transition-all"
            >
              Logout
            </button>
          </div>
        </div>
      </header>
    </div>
  );

  const renderTrips = () => (
    <div className="min-h-screen relative font-sans bg-[#E5DED2]"> {/* Warm cream background */}
      
      {bookingAlert && (
        <div className="absolute top-8 right-8 z-50 animate-fade-in">
          <div className="bg-[#FAF9F6] border border-orange-100 p-6 rounded-2xl shadow-xl max-w-sm">
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse"></span>
              <h3 className="font-serif font-bold text-lg text-slate-900">{bookingAlert.headline || bookingAlert.title}</h3>
            </div>
            
            {bookingAlert.headline ? (
              <>
                <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">{bookingAlert.operator} {bookingAlert.service_number} • {bookingAlert.route?.origin} &rarr; {bookingAlert.route?.destination}</p>
                <p className="text-sm text-slate-700 leading-relaxed mb-4">{bookingAlert.summary}</p>
                <div className="flex gap-3">
                  <button onClick={() => setCurrentView('ALERTS')} className="text-xs font-bold uppercase tracking-widest text-white bg-slate-900 px-4 py-2 rounded-full hover:bg-slate-800 transition-colors">View Alert</button>
                  <button onClick={() => setBookingAlert(null)} className="text-xs font-bold uppercase tracking-widest text-slate-500 hover:text-slate-900 transition-colors">Dismiss</button>
                </div>
              </>
            ) : (
              <>
                <p className="text-sm text-slate-700 leading-relaxed">{bookingAlert.message}</p>
                <button onClick={() => setBookingAlert(null)} className="mt-4 text-xs font-bold uppercase tracking-widest text-slate-500 hover:text-slate-900 transition-colors">Dismiss</button>
              </>
            )}
          </div>
        </div>
      )}

      {/* White Glassy Top Bar */}
      {renderTopNavBar('TRIPS')}
      <main className="max-w-7xl mx-auto px-8 py-16 relative">
        {!showImportModal ? (
          <>
            <div 
              className="flex flex-col md:flex-row gap-16 items-center mb-24 relative"
              onMouseEnter={() => {
                const playPromise = videoRef.current?.play();
                if (playPromise !== undefined) {
                  playPromise.catch(() => {});
                }
              }}
              onMouseLeave={() => {
                videoRef.current?.pause();
              }}
            >
              <div className="absolute -top-32 -right-32 w-96 h-96 bg-blue-300/60 rounded-full blur-3xl z-0 pointer-events-none"></div>
              <div className="absolute -bottom-32 left-1/2 w-96 h-96 bg-orange-300/60 rounded-full blur-3xl z-0 pointer-events-none"></div>
              <div className="absolute inset-y-0 left-[calc(-50vw+50%)] right-0 md:right-[30%] lg:right-[40%] overflow-hidden pointer-events-none z-[0] opacity-20 md:opacity-30">
                <video 
                  ref={videoRef}
                  src="/Untitled_Scene_09-27_18_15_21_20260927234837.mp4"
                  autoPlay={false}
                  muted
                  playsInline
                  loop
                  preload="metadata"
                  className="w-full h-full object-cover object-left mix-blend-multiply"
                />
              </div>
              
              <div className="flex-1 w-full relative z-10">
                <span className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-4 block">YOUR JOURNEYS</span>
                <h1 className="text-5xl md:text-6xl font-serif text-slate-900 mb-6 leading-tight">Where are you going next?</h1>
                
                <div className="flex gap-4 mb-4">
                  <button onClick={() => setMonitoringMode('TRIP')} className={`text-xs font-bold uppercase tracking-widest px-4 py-2 rounded-full transition-all ${monitoringMode === 'TRIP' ? 'bg-slate-200 text-slate-900 shadow-sm' : 'text-slate-500 hover:bg-slate-100'}`}>MONITOR TRIP</button>
                  <button onClick={() => setMonitoringMode('BOOKINGS')} className={`text-xs font-bold uppercase tracking-widest px-4 py-2 rounded-full transition-all ${monitoringMode === 'BOOKINGS' ? 'bg-slate-200 text-slate-900 shadow-sm' : 'text-slate-500 hover:bg-slate-100'}`}>MONITOR BOOKINGS</button>
                </div>
                {monitoringMode === 'TRIP' ? (
                  <p className="text-xl text-slate-600 font-light leading-relaxed mb-8">Your trips, ready for whatever changes along the way.</p>
                ) : (
                  <p className="text-xl text-slate-600 font-light leading-relaxed mb-8">Upload a booking, reservation, or ticket and Roam will keep watch for changes.</p>
                )}

                
                <div className="flex flex-col gap-6">
                  {bookingSummary && monitoringMode === 'BOOKINGS' && (
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 w-full">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="font-serif font-bold text-2xl tracking-widest">{(bookingSummary.provider || "BOOKING").toUpperCase()}</h3>
                          <p className="text-sm font-bold text-slate-500 tracking-widest">{bookingSummary.service_number || "ITINERARY"}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="bg-slate-100 text-slate-800 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest">{bookingSummary.booking_status || bookingSummary.status || "Confirmed"}</span>
                          <button 
                            type="button"
                            onClick={() => setBookingSummary(null)}
                            title="Dismiss booking result"
                            className="text-slate-400 hover:text-slate-700 p-1 rounded-full hover:bg-slate-100 transition-colors"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
                          </button>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4 mb-4 mt-4">
                        <div className="flex-1">
                          <p className="text-sm text-slate-500 uppercase tracking-widest font-bold">Origin</p>
                          <p className="font-serif text-lg">{bookingSummary.origin || "Origin"}</p>
                        </div>
                        <span className="text-slate-300">&rarr;</span>
                        <div className="flex-1 text-right">
                          <p className="text-sm text-slate-500 uppercase tracking-widest font-bold">Destination</p>
                          <p className="font-serif text-lg">{bookingSummary.destination || "Destination"}</p>
                        </div>
                      </div>

                      <div className="flex justify-between items-end border-t border-slate-100 pt-3 pb-3">
                        <div>
                          <p className="text-xs text-slate-500 uppercase tracking-widest font-bold mb-1">Departure</p>
                          <p className="text-sm font-medium">{bookingSummary.departure_time || (bookingSummary.original_departure ? new Date(bookingSummary.original_departure).toLocaleString() : "Scheduled")}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-slate-500 uppercase tracking-widest font-bold mb-1">Booking Ref</p>
                          <p className="text-sm font-medium font-mono">{bookingSummary.booking_reference || bookingSummary.id || "N/A"}</p>
                        </div>
                      </div>

                      {/* Email Date, Time, Sender (Requirement 5) */}
                      <div className="grid grid-cols-3 gap-2 border-t border-slate-100 pt-3 text-xs bg-slate-50/70 p-3 rounded-xl">
                        <div>
                          <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Email Date</p>
                          <p className="font-medium text-slate-700">{bookingSummary.email_date || "Unavailable"}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Email Time</p>
                          <p className="font-medium text-slate-700">{bookingSummary.email_time || "Unavailable"}</p>
                        </div>
                        <div className="truncate">
                          <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Sender Email</p>
                          <p className="font-medium text-slate-700 truncate" title={bookingSummary.sender_email}>{bookingSummary.sender_email || "Unavailable"}</p>
                        </div>
                      </div>
                      
                      {!gmailConnected ? (
                        <button onClick={() => {
                          window.location.href = 'http://localhost:8000/api/gmail/connect';
                        }} className="mt-6 w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold tracking-widest text-xs uppercase rounded-full shadow-md transition-all flex items-center justify-center gap-2">
                          <svg className="w-4 h-4" viewBox="0 0 24 24"><path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" /><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" /><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" /><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" /></svg>
                          Connect Gmail to Monitor
                        </button>
                      ) : !bookingMonitoringActive ? (
                        <button onClick={async () => {
                          try {
                            const res = await fetch('http://localhost:8000/api/monitor/booking/activate', {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify(bookingSummary)
                            });
                            if (res.ok) {
                              const data = await res.json();
                              setBookingMonitoringActive(true);
                              setBookingId(data.monitor_id);
                            }
                          } catch(e) {
                            console.error(e);
                          }
                        }} className="mt-6 w-full px-6 py-3 bg-slate-900 text-white font-bold tracking-widest text-xs uppercase rounded-full shadow-md transition-all flex items-center justify-center hover:bg-slate-800">
                          Keep an eye on this booking
                        </button>
                      ) : (
                        <div className="mt-6">
                          <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-xl text-emerald-800 mb-4">
                            <p className="font-bold text-sm mb-1 uppercase tracking-widest flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Actively Monitoring</p>
                            <p className="text-xs">Roam is scanning emails for updates to this booking.</p>
                            
                            <div className="mt-4 pt-3 border-t border-emerald-200/50">
                              <div className="flex items-center justify-between">
                                <span className="text-[10px] font-bold uppercase tracking-widest">Auto Monitor</span>
                                <div className="flex gap-1">
                                  <button onClick={() => setMonitorSettings(false, autoMonitorStatus.interval_seconds)} className={`px-2 py-1 text-[10px] font-bold uppercase tracking-widest rounded transition-colors ${!autoMonitorStatus.enabled ? 'bg-emerald-600 text-white' : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'}`}>Off</button>
                                  <button onClick={() => setMonitorSettings(true, 30)} className={`px-2 py-1 text-[10px] font-bold uppercase tracking-widest rounded transition-colors ${autoMonitorStatus.enabled && autoMonitorStatus.interval_seconds === 30 ? 'bg-emerald-600 text-white' : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'}`}>30s</button>
                                  <button onClick={() => setMonitorSettings(true, 60)} className={`px-2 py-1 text-[10px] font-bold uppercase tracking-widest rounded transition-colors ${autoMonitorStatus.enabled && autoMonitorStatus.interval_seconds === 60 ? 'bg-emerald-600 text-white' : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'}`}>1m</button>
                                </div>
                              </div>
                              <p className="text-[10px] opacity-70 mt-2">
                                {autoMonitorStatus.enabled ? `Checking automatically every ${autoMonitorStatus.interval_seconds === 30 ? '30 sec' : '1 min'}` : 'Automatic monitoring off'}
                                {autoMonitorStatus.last_check_at && ` • Last checked: ${new Date(autoMonitorStatus.last_check_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`}
                              </p>
                            </div>
                          </div>
                          <button onClick={async () => {
                            try {
                              const res = await fetch(`http://localhost:8000/api/monitor/check/${bookingId}`, {
                                method: 'POST'
                              });
                              if (res.ok) {
                                const data = await res.json();
                                if (data.status === "change_detected" && data.alert) {
                                  setBookingAlert(data.alert);
                                } else if (data.status === "no_change") {
                                  setBookingAlert({ title: "No new update found", message: "Your booking is on schedule." });
                                  setTimeout(() => setBookingAlert(null), 3000);
                                } else {
                                  alert("Error: " + (data.message || "Unknown error"));
                                }
                              }
                            } catch(e) {
                              console.error(e);
                              alert("Error checking for updates.");
                            }
                          }} className="w-full px-6 py-3 bg-slate-100 text-slate-700 font-bold tracking-widest text-xs uppercase rounded-full shadow-sm transition-all flex items-center justify-center hover:bg-slate-200 border border-slate-300">
                            Check for Updates
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Input options: always available for multiple searches (Requirement 6.1) */}
                  <div className="flex gap-4 items-center flex-wrap">
                    <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept="image/*" />
                    <button 
                      type="button"
                      onClick={() => setShowImportModal(true)} 
                      disabled={importing} 
                      className="bg-slate-900 text-white px-6 py-3 rounded-full text-sm font-medium hover:bg-slate-800 transition-all shadow-md"
                    >
                      {bookingSummary && monitoringMode === 'BOOKINGS' ? "Search Another Booking" : "Paste Text"}
                    </button>
                    
                    {/* Upload Image: ONLY for MONITOR TRIP */}
                    {monitoringMode === 'TRIP' && (
                      <button 
                        type="button"
                        onClick={() => handleImport('image')} 
                        disabled={importing} 
                        className="bg-[#F9F8F6] border border-slate-200 text-slate-800 px-6 py-3 rounded-full text-sm font-medium hover:bg-white transition-all shadow-sm"
                      >
                        Upload Image
                      </button>
                    )}

                    {/* Voice Option for both MONITOR TRIP and MONITOR BOOKINGS */}
                    <button 
                      type="button"
                      onClick={() => {
                        if (monitoringMode === 'BOOKINGS') {
                          setShowImportModal(true);
                          setTimeout(() => startBookingVoiceRecording(), 150);
                        } else {
                          setShowVoiceModal(true);
                        }
                      }} 
                      disabled={importing} 
                      className="bg-[#F9F8F6] border border-slate-200 text-slate-800 px-6 py-3 rounded-full text-sm font-medium hover:bg-white transition-all shadow-sm flex items-center gap-2"
                    >
                      <svg className="w-4 h-4 text-slate-600 fill-current" viewBox="0 0 24 24">
                        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                      </svg>
                      Voice
                    </button>

                    {monitoringMode === 'BOOKINGS' && (
                      !gmailConnected ? (
                        <button onClick={() => {
                          window.location.href = 'http://localhost:8000/api/gmail/connect';
                        }} disabled={importing} className="bg-blue-600 border border-blue-600 text-white px-6 py-3 rounded-full text-sm font-medium hover:bg-blue-700 transition-all shadow-sm flex items-center gap-2">
                          Connect Gmail
                        </button>
                      ) : (
                        <div className="flex items-center gap-2">
                          <span className="bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-3 rounded-full text-sm font-medium shadow-sm flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                            Gmail Connected &middot; {gmailEmail || 'Unknown'}
                          </span>
                          <button onClick={handleGmailDisconnect} className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-full text-sm font-medium hover:bg-red-100 transition-all shadow-sm">
                            Disconnect
                          </button>
                        </div>
                      )
                    )}
                  </div>
                </div>
              </div>
              {/* Right Image Composition */}
              <div className="hidden md:block w-1/2 relative h-[500px] z-10 translate-x-[60px]">
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} className="absolute inset-0 rounded-[3rem] overflow-hidden shadow-2xl">
                      <img src="/roam_image_assets/destinations/destination_city_street.png" className="w-full h-full object-cover" alt="Destination" />
                  </motion.div>
                  
                  <motion.div 
                      animate={{ y: [0, -5, 0], rotate: [-2, -2, -2] }}
                      transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
                      className="absolute top-12 -left-12 w-48 p-3 bg-white shadow-xl polaroid-frame"
                  >
                      <div className="border border-slate-100 h-48 overflow-hidden mb-4 relative">
                          <img src="/roam_image_assets/instax/instax_blue_city_view.png" className="w-full h-full object-cover" alt="Memory 1" />
                      </div>
                  </motion.div>
                  
                  <motion.div 
                      animate={{ y: [0, 5, 0], rotate: [4, 4, 4] }}
                      transition={{ duration: 7, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                      className="absolute bottom-12 -right-8 w-56 p-3 bg-white shadow-2xl polaroid-frame"
                  >
                      <div className="border border-slate-100 h-56 overflow-hidden mb-4 relative">
                          <img src="/roam_image_assets/instax/instax_florence_evening.png" className="w-full h-full object-cover" alt="Memory 2" />
                      </div>
                  </motion.div>
                  
                  <motion.div 
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1, duration: 1 }}
                      className="absolute -bottom-8 left-4 rotate-[-5deg]"
                  >
                      <span className="font-['Caveat',_cursive] text-3xl text-blue-800/80 drop-shadow-sm">Make room for the unexpected.</span>
                  </motion.div>
              </div>

            </div>


            {/* Landing page saved trips removed per Requirement 4.4 */}
          </>
        ) : (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col md:flex-row gap-16 items-center"
          >
            {/* Left Content */}
            <div className="flex-1 w-full">
              {!pendingTrip ? (
                <>
                  <button onClick={() => { setShowImportModal(false); stopBookingVoiceRecording(); setImportStatus(""); setImportText(""); }} className="mb-12 text-sm font-bold tracking-widest text-slate-400 hover:text-slate-800 uppercase transition-colors">&larr; Back</button>
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-4 block">
                    {monitoringMode === 'BOOKINGS' ? "IMPORT BOOKING" : "IMPORT YOUR JOURNEY"}
                  </span>
                  <h2 className="text-4xl md:text-5xl font-serif text-slate-900 mb-6 leading-tight">
                    {monitoringMode === 'BOOKINGS' ? "Paste your booking details." : "Bring your journey into Roam."}
                  </h2>

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
            
          </div>

                  <p className="text-lg text-slate-600 mb-8 font-light leading-relaxed">
                    {monitoringMode === 'BOOKINGS' ? "Paste or speak your flight ticket, hotel confirmation, train ticket, reservation, or booking details here..." : "Paste an itinerary or upload the plan you already have."}
                  </p>
                  
                  <div className="relative mb-6">
                    <textarea 
                      className="w-full h-64 bg-white border border-slate-200 shadow-inner rounded-2xl p-6 pb-16 font-serif text-lg focus:ring-2 focus:ring-slate-300 focus:outline-none resize-none transition-shadow"
                      placeholder={monitoringMode === 'BOOKINGS' ? "Paste or speak your booking information..." : "Paste your text itinerary here..."}
                      value={importText}
                      onChange={(e) => setImportText(e.target.value)}
                      disabled={importing}
                    ></textarea>

                    {/* Voice recording button at bottom-left inside textarea, exactly as indicated by user */}
                    <div className="absolute bottom-4 left-4 flex items-center gap-2">
                      <button
                        type="button"
                        onClick={toggleBookingVoiceRecording}
                        disabled={importing}
                        title={isBookingVoiceListening ? "Stop voice recording" : "Record voice booking"}
                        className={`p-2.5 rounded-full border transition-all flex items-center justify-center gap-2 ${
                          isBookingVoiceListening
                            ? 'bg-red-500 text-white border-red-600 shadow-md animate-pulse ring-4 ring-red-100'
                            : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100 hover:text-slate-900 shadow-sm'
                        }`}
                        aria-label="Voice input"
                      >
                        <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
                          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                        </svg>
                        {isBookingVoiceListening && (
                          <span className="text-xs font-bold uppercase tracking-wider pr-1">Listening...</span>
                        )}
                      </button>
                      {isBookingVoiceListening && (
                        <span className="text-xs text-red-600 font-medium animate-pulse">
                          Speak now — recording booking details...
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    {monitoringMode === 'BOOKINGS' ? (
                      <button onClick={handleExtractBooking} disabled={importing || !importText} className="px-8 py-4 bg-slate-900 text-white rounded-full hover:bg-slate-800 shadow-lg text-sm font-bold uppercase tracking-widest transition-all">Extract Booking</button>
                    ) : importStatus.includes("couldn't") ? (
                      <button onClick={handleImportTextSubmit} disabled={importing || !importText} className="px-8 py-4 bg-slate-900 text-white rounded-full hover:bg-slate-800 shadow-lg text-sm font-bold uppercase tracking-widest transition-all">Try again</button>
                    ) : (
                      <button onClick={handleImportTextSubmit} disabled={importing || !importText} className="px-8 py-4 bg-slate-900 text-white rounded-full hover:bg-slate-800 shadow-lg text-sm font-bold uppercase tracking-widest transition-all">Create itinerary</button>
                    )}
                    {importStatus && <p className={`text-sm font-medium ${importStatus.includes("couldn't") ? 'text-red-500' : 'text-slate-500'}`}>{importStatus}</p>}
                    {importError && <p className={`text-sm font-medium text-red-500`}>{importError}</p>}
                  </div>
                </>
              ) : (
                <>
                  <h2 className="text-4xl font-serif text-slate-900 mb-4 leading-tight">Your journey is taking shape.</h2>

          <div className="mb-4 bg-gray-100 p-3 rounded border border-gray-300">
            <h3 className="font-bold text-gray-800 flex justify-between">
              <span>●  LIVE Status</span>
              <span className="text-sm font-normal bg-gray-200 px-2 rounded text-gray-600">{liveStatus}</span>
            </h3>
            <div className="mt-2 text-sm text-gray-600 space-y-1">
              {liveMessages.slice(0,3).map((msg, idx) => (
                <div key={idx} className="border-l-2 border-blue-400 pl-2">{msg}</div>
              ))}
            </div>
            
          </div>

                  <p className="text-lg text-slate-600 mb-8 font-light">Review the extracted itinerary below.</p>
                  
                  <div className="mb-8 max-h-96 overflow-y-auto p-8 bg-white border border-slate-200 rounded-3xl shadow-sm">
                    <h3 className="font-serif font-bold text-2xl text-slate-800 mb-6 pb-4 border-b border-slate-100">{pendingTrip?.name || "Trip"} to {pendingTrip?.destination || "Unknown"}</h3>
                    {pendingTrip.days?.map((day, idx) => (
                      <div key={idx} className="mb-6 last:mb-0">
                        <strong className="text-slate-900 tracking-wide font-sans text-sm uppercase">{day.date}</strong>
                        <div className="mt-4 space-y-4">
                          {day.stops?.map((stop, sidx) => (
                            <div key={sidx} className="flex gap-4 border-l-2 border-slate-100 pl-4">
                              <span className="font-bold text-slate-800 w-16 flex-shrink-0">{stop.start_time}</span>
                              <span className="text-slate-600">{stop.title}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="flex gap-4">
                    <button onClick={() => { setPendingTrip(null); setImportStatus(""); }} className="px-8 py-4 border border-slate-200 bg-white text-slate-600 rounded-full hover:bg-slate-50 shadow-sm text-sm font-bold uppercase tracking-widest transition-all">Discard</button>
                    <button onClick={handleSaveTrip} className="px-8 py-4 bg-slate-900 text-white rounded-full hover:bg-slate-800 shadow-lg text-sm font-bold uppercase tracking-widest transition-all">Save & Continue &rarr;</button>
                  </div>
                </>
              )}
            </div>
            
            {/* Right Image Composition */}
            <div className="hidden md:block w-5/12 relative h-[600px]">
              <div className="absolute inset-0 rounded-[2rem] overflow-hidden shadow-2xl">
                <img src="/roam_image_assets/destinations/destination_city_street.png" className="w-full h-full object-cover" alt="Destination" />
              </div>
              <motion.div 
                animate={{ y: [0, -5, 0], rotate: [-2, -2, -2] }}
                transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
                className="absolute top-12 -left-12 w-48 p-3 bg-white shadow-xl"
              >
                <div className="border border-slate-100 h-48 overflow-hidden mb-4">
                  <img src="/roam_image_assets/instax/instax_blue_city_view.png" className="w-full h-full object-cover" alt="Memory 1" />
                </div>
              </motion.div>
              <motion.div 
                animate={{ y: [0, 5, 0], rotate: [3, 3, 3] }}
                transition={{ duration: 7, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                className="absolute bottom-12 -right-8 w-56 p-3 bg-white shadow-2xl"
              >
                <div className="border border-slate-100 h-56 overflow-hidden mb-4">
                  <img src="/roam_image_assets/instax/instax_florence_evening.png" className="w-full h-full object-cover" alt="Memory 2" />
                </div>
              </motion.div>
            </div>
          </motion.div>
        )}
      </main>
      <VoiceItineraryModal 
        isOpen={showVoiceModal} 
        onClose={() => setShowVoiceModal(false)} 
        onSubmitItinerary={handleVoiceItinerarySubmit} 
      />
    </div>
  );

  const renderExploreTrips = () => (
    <div className="min-h-screen bg-[#E5DED2] font-sans pb-24">
      {/* White Glassy Top Bar */}
      {renderTopNavBar('EXPLORE_TRIPS')}

      <main className="w-full px-4 sm:px-6 md:px-8 lg:px-10 py-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 mb-8">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2 block">EXPLORE / TRIPS</span>
            <h1 className="text-4xl md:text-5xl font-serif text-slate-900 leading-tight">Your Saved Itineraries</h1>
            <p className="text-slate-600 mt-2">Manage and view all your state-planned journeys with curated regional imagery.</p>
          </div>
          <button 
            type="button"
            onClick={() => { setMonitoringMode('TRIP'); setCurrentView('TRIPS'); }} 
            className="bg-slate-900 text-white px-6 py-3 rounded-full text-xs font-bold uppercase tracking-widest hover:bg-slate-800 transition-all shadow-md"
          >
            + Create New Trip
          </button>
        </div>

        {/* State Filter Buttons */}
        <div className="flex items-center gap-2 overflow-x-auto pb-4 mb-8 no-scrollbar">
          {[
            { id: 'ALL', label: 'All Plans' },
            { id: 'RAJASTHAN', label: 'Rajasthan' },
            { id: 'KERALA', label: 'Kerala' },
            { id: 'DELHI', label: 'Delhi' },
            { id: 'GOA', label: 'Goa' },
            { id: 'MUMBAI', label: 'Mumbai' },
            { id: 'MAHARASHTRA', label: 'Maharashtra' },
            { id: 'TAMILNADU', label: 'Tamil Nadu' },
            { id: 'HYDERABAD', label: 'Hyderabad' }
          ].map(f => (
            <button
              key={f.id}
              onClick={() => setSelectedStateFilter(f.id)}
              className={`px-4 py-2 rounded-full text-xs font-bold uppercase tracking-wider transition-all whitespace-nowrap shadow-sm border ${
                selectedStateFilter === f.id
                  ? 'bg-slate-900 text-white border-slate-900'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {trips.length === 0 ? (
          <div className="bg-white p-12 rounded-3xl shadow-sm border border-slate-100 text-center max-w-xl mx-auto my-12">
            <h3 className="text-2xl font-serif text-slate-800 mb-3">No Saved Itineraries Yet</h3>
            <p className="text-slate-500 text-sm mb-6">Create your first itinerary by describing your trip with voice, pasting text, or uploading an image.</p>
            <button 
              type="button"
              onClick={() => { setMonitoringMode('TRIP'); setCurrentView('TRIPS'); }} 
              className="bg-slate-900 text-white px-6 py-3 rounded-full text-xs font-bold uppercase tracking-widest hover:bg-slate-800 transition-all"
            >
              Start Planning
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {trips.filter(t => {
              if (selectedStateFilter === 'ALL') return true;
              const img = getTripCoverImage(t);
              if (selectedStateFilter === 'RAJASTHAN') return img.includes('rajasthan');
              if (selectedStateFilter === 'KERALA') return img.includes('kerala');
              if (selectedStateFilter === 'DELHI') return img.includes('delhi');
              if (selectedStateFilter === 'GOA') return img.includes('goa');
              if (selectedStateFilter === 'MUMBAI') return img.includes('mumbai');
              if (selectedStateFilter === 'MAHARASHTRA') return img.includes('maharashtra');
              if (selectedStateFilter === 'TAMILNADU') return img.includes('tamilnadu');
              if (selectedStateFilter === 'HYDERABAD') return img.includes('charminar');
              return true;
            }).map(t => {
              const coverImg = getTripCoverImage(t);
              return (
                <div 
                  key={t.id} 
                  className="group bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden hover:shadow-xl transition-all duration-300 flex flex-col justify-between"
                >
                  <div className="h-44 bg-slate-100 overflow-hidden relative">
                    <img 
                      src={coverImg} 
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" 
                      alt={t.name || t.destination || "Trip destination"} 
                    />
                    <div className="absolute top-4 left-4">
                      <span className="bg-emerald-500/90 text-white backdrop-blur-sm text-[10px] uppercase font-bold tracking-wider px-3 py-1 rounded-full shadow-sm">
                        {t.destination || "Active"}
                      </span>
                    </div>
                    <div className="absolute top-4 right-4">
                      <button 
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.confirm("Are you sure you want to delete this trip?")) {
                            deleteTrip(t.id);
                          }
                        }}
                        className="w-8 h-8 rounded-full bg-white/90 text-slate-400 hover:text-red-600 hover:bg-white flex items-center justify-center transition-colors shadow-sm"
                        title="Delete trip"
                      >
                        &times;
                      </button>
                    </div>
                  </div>
                  <div className="p-6 flex-1 flex flex-col justify-between">
                    <div>
                      <span className="text-xs font-bold uppercase tracking-widest text-slate-400 block mb-1">{t.start_date} &mdash; {t.end_date}</span>
                      <h3 className="text-2xl font-bold font-serif text-slate-800 mb-2">{t.name || t.destination || "Trip"}</h3>
                      <p className="text-slate-500 text-xs mb-4">
                        {t.days?.reduce((acc, d) => acc + (d.stops?.length || 0), 0) || 0} Stops Planned &middot; {t.destination || "Multiple locations"}
                      </p>
                    </div>
                    <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                      <button 
                        type="button"
                        onClick={() => { loadTrip(t.id); setCurrentView('DASHBOARD'); }}
                        className="text-xs font-bold uppercase tracking-widest text-blue-600 hover:text-blue-800 flex items-center gap-1"
                      >
                        Open Itinerary &rarr;
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );

  const renderExploreBookings = () => (
    <div className="min-h-screen bg-[#E5DED2] font-sans pb-24">
      {/* White Glassy Top Bar */}
      {renderTopNavBar('EXPLORE_BOOKINGS')}

      <main className="w-full px-4 sm:px-6 md:px-8 lg:px-10 py-8">
        <div className="flex justify-between items-end mb-12">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2 block">EXPLORE / BOOKINGS</span>
            <h1 className="text-4xl md:text-5xl font-serif text-slate-900 leading-tight">Your Saved Bookings</h1>
            <p className="text-slate-600 mt-2">Track flights, trains, hotels, and reservations across your journeys.</p>
          </div>
          <button 
            type="button"
            onClick={() => { setMonitoringMode('BOOKINGS'); setCurrentView('TRIPS'); setShowImportModal(true); }} 
            className="bg-slate-900 text-white px-6 py-3 rounded-full text-xs font-bold uppercase tracking-widest hover:bg-slate-800 transition-all shadow-md"
          >
            + Add Booking
          </button>
        </div>

        {savedBookings.length === 0 ? (
          <div className="bg-white p-12 rounded-3xl shadow-sm border border-slate-100 text-center max-w-xl mx-auto my-12">
            <h3 className="text-2xl font-serif text-slate-800 mb-3">No Saved Bookings</h3>
            <p className="text-slate-500 text-sm mb-6">You haven't monitored any bookings yet. Paste a booking confirmation, upload a ticket, or connect Gmail under Monitor Bookings.</p>
            <button 
              type="button"
              onClick={() => { setMonitoringMode('BOOKINGS'); setCurrentView('TRIPS'); }} 
              className="bg-slate-900 text-white px-6 py-3 rounded-full text-xs font-bold uppercase tracking-widest hover:bg-slate-800 transition-all"
            >
              Monitor a Booking
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {savedBookings.map(b => (
              <div key={b.id} className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 flex flex-col justify-between relative hover:shadow-md transition-shadow">
                {/* Header: Provider & X Delete Button */}
                <div>
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400 block">{b.booking_type || "TRAVEL BOOKING"}</span>
                      <h3 className="font-serif font-bold text-2xl text-slate-900 tracking-wide">{b.provider?.toUpperCase()}</h3>
                      <p className="text-xs font-mono font-bold text-slate-500 tracking-wider mt-0.5">{b.service_number}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="bg-slate-100 text-slate-800 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest">
                        {b.booking_status || "Confirmed"}
                      </span>
                      {/* X Delete Button (Requirement 6.5) */}
                      <button 
                        type="button"
                        onClick={() => handleDeleteBooking(b.id)}
                        className="w-7 h-7 rounded-full border border-slate-200 text-slate-400 hover:text-red-600 hover:border-red-300 hover:bg-red-50 flex items-center justify-center transition-colors ml-1"
                        title="Delete booking"
                      >
                        <span className="text-base font-bold leading-none">&times;</span>
                      </button>
                    </div>
                  </div>

                  {/* Origin & Destination */}
                  <div className="flex items-center gap-3 my-4 py-3 bg-slate-50/60 rounded-xl px-4">
                    <div className="flex-1">
                      <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Origin</p>
                      <p className="font-serif text-base font-bold text-slate-800 truncate">{b.origin || "Unknown"}</p>
                    </div>
                    <span className="text-slate-400 font-bold">&rarr;</span>
                    <div className="flex-1 text-right">
                      <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Destination</p>
                      <p className="font-serif text-base font-bold text-slate-800 truncate">{b.destination || "Unknown"}</p>
                    </div>
                  </div>

                  {/* Departure & Ref */}
                  <div className="flex justify-between items-center text-xs py-2 border-b border-slate-100">
                    <div>
                      <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Departure</p>
                      <p className="font-medium text-slate-700">{b.original_departure ? new Date(b.original_departure).toLocaleString() : "Unknown"}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Booking Ref</p>
                      <p className="font-medium font-mono text-slate-700">{b.booking_reference || "N/A"}</p>
                    </div>
                  </div>

                  {/* Email Date, Time, Sender (Requirement 5) */}
                  <div className="grid grid-cols-3 gap-2 py-3 border-b border-slate-100 text-xs">
                    <div>
                      <p className="text-[9px] text-slate-400 uppercase tracking-widest font-bold">Email Date</p>
                      <p className="font-medium text-slate-700 text-[11px] truncate">{b.email_date || "Unavailable"}</p>
                    </div>
                    <div>
                      <p className="text-[9px] text-slate-400 uppercase tracking-widest font-bold">Email Time</p>
                      <p className="font-medium text-slate-700 text-[11px] truncate">{b.email_time || "Unavailable"}</p>
                    </div>
                    <div className="truncate">
                      <p className="text-[9px] text-slate-400 uppercase tracking-widest font-bold">Sender Email</p>
                      <p className="font-medium text-slate-700 text-[11px] truncate" title={b.sender_email}>{b.sender_email || "Unavailable"}</p>
                    </div>
                  </div>
                </div>

                {/* Monitoring Status & Controls (Requirement 6.4) */}
                <div className="pt-4 mt-2">
                  {b.monitored ? (
                    <div>
                      <div className="flex items-center justify-between text-xs mb-3 text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
                        <span className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[10px]">
                          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                          Actively Monitoring
                        </span>
                        <span className="text-[10px] text-emerald-600 font-medium">Scanning</span>
                      </div>
                      <button 
                        type="button"
                        onClick={async () => {
                          try {
                            const res = await fetch(`http://localhost:8000/api/monitor/check/${b.id}`, { method: 'POST' });
                            if (res.ok) {
                              const data = await res.json();
                              if (data.status === "change_detected" && data.alert) {
                                setBookingAlert(data.alert);
                              } else {
                                alert(`Update check for ${b.service_number}: Booking is on schedule.`);
                              }
                            }
                          } catch(err) {
                            alert("Failed to check for updates");
                          }
                        }}
                        className="w-full py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold tracking-widest text-[11px] uppercase rounded-full transition-all border border-slate-200"
                      >
                        Check for Updates
                      </button>
                    </div>
                  ) : (
                    <div>
                      <div className="flex items-center justify-between text-xs mb-3 text-slate-500 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-100">
                        <span className="text-[10px] font-bold uppercase tracking-wider">Not Monitored</span>
                      </div>
                      <button 
                        type="button"
                        onClick={async () => {
                          try {
                            const res = await fetch('http://localhost:8000/api/monitor/booking/activate', {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify(b)
                            });
                            if (res.ok) {
                              setSavedBookings(prev => prev.map(item => item.id === b.id ? { ...item, monitored: true } : item));
                              fetchBookings();
                            }
                          } catch(err) {
                            console.error("Failed to activate monitoring:", err);
                          }
                        }}
                        className="w-full py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-bold tracking-widest text-[11px] uppercase rounded-full transition-all shadow-sm"
                      >
                        Keep an Eye on this
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );

  const renderAlertCenter = () => (
    <div className="min-h-screen relative font-sans bg-[#E5DED2] pb-24">
      {/* Liquid Glass Top Bar */}
      <div className="sticky top-0 z-40 w-full px-4 sm:px-8 pt-3.5 pb-2 pointer-events-none mb-6">
        <header className="liquid-glass-bar max-w-4xl mx-auto rounded-[2rem] px-6 sm:px-8 py-3 flex justify-between items-center text-slate-800 pointer-events-auto">
          <div className="relative z-10 w-full flex justify-between items-center">
            <button 
              onClick={() => setCurrentView('TRIPS')} 
              className="text-xs font-bold uppercase tracking-widest liquid-glass-pill text-slate-700 hover:text-slate-950 px-3.5 py-1.5 rounded-full transition-all flex items-center gap-1.5"
            >
              <span>&larr;</span> Back to Trips
            </button>
            <div className="font-serif font-bold text-xl tracking-widest text-slate-900">ALERT CENTER</div>
          </div>
        </header>
      </div>
      <div className="max-w-4xl mx-auto px-8 relative">

        <div className="space-y-6">
          {alerts.length === 0 ? (
            <div className="text-center py-20 text-slate-500 font-serif">No alerts yet.</div>
          ) : (
            alerts.map(alert => (
              <div key={alert.id} className={`p-6 rounded-2xl shadow-sm border ${alert.is_read ? 'bg-[#F5F1EB] border-slate-200 opacity-70' : 'bg-[#FAF9F6] border-orange-200'}`}>
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="flex gap-2 items-center mb-1">
                      {!alert.is_read && <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse"></span>}
                      <span className="text-xs font-bold uppercase tracking-widest text-slate-500">{new Date(alert.created_at).toLocaleString()}</span>
                    </div>
                    <h3 className="font-serif font-bold text-2xl text-slate-900">{alert.headline}</h3>
                    <p className="text-sm font-bold text-slate-600 uppercase tracking-widest">{alert.operator} {alert.service_number} • {alert.route.origin} &rarr; {alert.route.destination}</p>
                  </div>
                  <div className="text-right">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${alert.impact?.level === 'high' ? 'bg-red-100 text-red-800' : 'bg-orange-100 text-orange-800'}`}>{alert.impact?.level} IMPACT</span>
                  </div>
                </div>

                <p className="text-base text-slate-700 leading-relaxed mb-6">{alert.summary}</p>
                
                {alert.recommendations && alert.recommendations.length > 0 && (
                  <div className="mb-6 bg-white p-4 rounded-xl border border-slate-100">
                    <h4 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Agent Recommendations</h4>
                    {alert.recommendations.map((rec, idx) => (
                      <div key={idx} className="mb-2 last:mb-0">
                        <span className="font-bold text-sm text-slate-800">{rec.title}: </span>
                        <span className="text-sm text-slate-600">{rec.reason}</span>
                      </div>
                    ))}
                  </div>
                )}
                
                <div className="flex gap-4">
                  {!alert.is_read && (
                    <button onClick={() => markAlertRead(alert.id)} className="text-xs font-bold uppercase tracking-widest px-4 py-2 bg-slate-200 text-slate-800 hover:bg-slate-300 rounded-full transition-colors">Mark as Read</button>
                  )}
                  {alert.actions && alert.actions.includes("CHECK_TRIP_IMPACT") && (
                    <button onClick={() => {
                      setSelectedAlertToAssess(alert);
                    }} className="text-xs font-bold uppercase tracking-widest px-4 py-2 bg-slate-900 text-white hover:bg-slate-800 rounded-full transition-colors">Assess Trip Impact</button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Select Trip Modal */}
      {selectedAlertToAssess && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full relative">
            <button onClick={() => setSelectedAlertToAssess(null)} className="absolute top-6 right-6 text-slate-400 hover:text-slate-900">✕</button>
            <h3 className="font-serif font-bold text-2xl text-slate-900 mb-2">Select Trip to Reschedule</h3>
            <p className="text-sm text-slate-500 mb-6">Which itinerary should be updated for this disruption?</p>
            
            <div className="space-y-3 mb-4 max-h-64 overflow-y-auto pr-2">
              {trips.length === 0 ? (
                <p className="text-slate-500 text-sm italic">No trips available.</p>
              ) : (
                trips.map(t => (
                  <div 
                    key={t.id}
                    onClick={async () => {
                      await loadTrip(t.id);
                      if (!selectedAlertToAssess.is_read) markAlertRead(selectedAlertToAssess.id);
                      
                      const delayMins = selectedAlertToAssess.delay_minutes > 0 ? selectedAlertToAssess.delay_minutes : 15;
                      
                      // We must fetch the updated trip from the store, not 't' which might be stale or just a summary
                      const latestTrip = useTripStore.getState().trip || t;
                      const firstActiveStop = latestTrip.days?.[0]?.stops?.find(s => s.status !== 'COMPLETED');
                      
                      simulateDisruption('NORMAL_DELAY', firstActiveStop?.id, delayMins);
                      setSelectedAlertToAssess(null);
                      setCurrentView('DASHBOARD');
                    }}
                    className="p-4 border border-slate-200 rounded-2xl hover:border-blue-500 hover:bg-blue-50 cursor-pointer transition-colors"
                  >
                    <p className="font-bold text-slate-800">{t.name || t.destination}</p>
                    <p className="text-xs text-slate-500 uppercase tracking-widest mt-1">{t.start_date} - {t.end_date}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderDashboard = () => {
    if (!trip) return <div className="p-8">Loading...</div>;
    const stops = trip?.days?.[0]?.stops || [];

    return (
    <div className="h-screen bg-[#E5DED2] font-sans flex flex-col relative overflow-hidden">
      <DisruptionRecoveryCard />

      {/* DECORATIVE POLAROIDS FLANKING BOTH SIDES (3 ON LEFT, 3 ON RIGHT) - OUTSIDE THE FRAME */}
      <div className="pointer-events-none select-none hidden lg:block">
        {/* Left 1: Top-Left (Tilted -8deg) */}
        <motion.div 
          initial={{ opacity: 0, x: -25 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="fixed top-24 left-2 xl:left-6 w-36 xl:w-44 p-2.5 pb-6 bg-white shadow-2xl rounded-sm rotate-[-8deg] pointer-events-auto hover:rotate-0 hover:scale-105 hover:z-30 transition-all duration-300 border border-slate-100/80 z-10"
        >
          <div className="w-full aspect-square overflow-hidden bg-slate-100 border border-slate-100">
            <img src="/roam_image_assets/instax/instax_blue_city_view.png" alt="Memory" className="w-full h-full object-cover" />
          </div>
          <div className="mt-2 text-center font-['Caveat',_cursive] text-slate-500 text-sm">Blue City View</div>
        </motion.div>

        {/* Left 2: Middle-Left (Tilted +8deg) */}
        <motion.div 
          initial={{ opacity: 0, x: -25 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.15 }}
          className="fixed top-[450px] left-1 xl:left-5 w-36 xl:w-44 p-2.5 pb-6 bg-white shadow-2xl rounded-sm rotate-[8deg] pointer-events-auto hover:rotate-0 hover:scale-105 hover:z-30 transition-all duration-300 border border-slate-100/80 z-10"
        >
          <div className="w-full aspect-square overflow-hidden bg-slate-100 border border-slate-100">
            <img src={getTripCoverImage(trip)} alt="State destination" className="w-full h-full object-cover" />
          </div>
          <div className="mt-2 text-center font-['Caveat',_cursive] text-slate-500 text-sm">{trip?.destination || trip?.name || 'Local Destination'}</div>
        </motion.div>

        {/* Left 3: Bottom-Left (Tilted -6deg) */}
        <motion.div 
          initial={{ opacity: 0, x: -25 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="fixed top-[820px] left-2 xl:left-6 w-36 xl:w-44 p-2.5 pb-6 bg-white shadow-2xl rounded-sm rotate-[-6deg] pointer-events-auto hover:rotate-0 hover:scale-105 hover:z-30 transition-all duration-300 border border-slate-100/80 z-10"
        >
          <div className="w-full aspect-square overflow-hidden bg-slate-100 border border-slate-100">
            <img src="/roam_image_assets/instax/instax_beach_escape.png" alt="Memory" className="w-full h-full object-cover" />
          </div>
          <div className="mt-2 text-center font-['Caveat',_cursive] text-slate-500 text-sm">Beach Escape</div>
        </motion.div>

        {/* Right 1: Top-Right (Tilted +9deg) */}
        <motion.div 
          initial={{ opacity: 0, x: 25 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="fixed top-20 right-2 xl:right-6 w-36 xl:w-44 p-2.5 pb-6 bg-white shadow-2xl rounded-sm rotate-[9deg] pointer-events-auto hover:rotate-0 hover:scale-105 hover:z-30 transition-all duration-300 border border-slate-100/80 z-10"
        >
          <div className="w-full aspect-square overflow-hidden bg-slate-100 border border-slate-100">
            <img src="/roam_image_assets/instax/instax_florence_evening.png" alt="Memory" className="w-full h-full object-cover" />
          </div>
          <div className="mt-2 text-center font-['Caveat',_cursive] text-slate-500 text-sm">Florence Dusk</div>
        </motion.div>

        {/* Right 2: Middle-Right (Tilted -7deg) */}
        <motion.div 
          initial={{ opacity: 0, x: 25 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.15 }}
          className="fixed top-[430px] right-1 xl:right-5 w-36 xl:w-44 p-2.5 pb-6 bg-white shadow-2xl rounded-sm rotate-[-7deg] pointer-events-auto hover:rotate-0 hover:scale-105 hover:z-30 transition-all duration-300 border border-slate-100/80 z-10"
        >
          <div className="w-full aspect-square overflow-hidden bg-slate-100 border border-slate-100">
            <img src="/roam_image_assets/destinations/destination_food.png" alt="Memory" className="w-full h-full object-cover" />
          </div>
          <div className="mt-2 text-center font-['Caveat',_cursive] text-slate-500 text-sm">Local Cuisine</div>
        </motion.div>

        {/* Right 3: Bottom-Right (Tilted +8deg) */}
        <motion.div 
          initial={{ opacity: 0, x: 25 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="fixed top-[800px] right-2 xl:right-6 w-36 xl:w-44 p-2.5 pb-6 bg-white shadow-2xl rounded-sm rotate-[8deg] pointer-events-auto hover:rotate-0 hover:scale-105 hover:z-30 transition-all duration-300 border border-slate-100/80 z-10"
        >
          <div className="w-full aspect-square overflow-hidden bg-slate-100 border border-slate-100">
            <img src="/roam_image_assets/instax/instax_cycling_sunset.png" alt="Memory" className="w-full h-full object-cover" />
          </div>
          <div className="mt-2 text-center font-['Caveat',_cursive] text-slate-500 text-sm">Cycling Sunset</div>
        </motion.div>
      </div>

      {/* Liquid Glass Top Bar */}
      <div className="z-40 w-full px-4 sm:px-8 pt-3 pb-2 pointer-events-none shrink-0">
        <header className="liquid-glass-bar max-w-7xl mx-auto rounded-[2rem] px-6 sm:px-8 py-3 flex justify-between items-center text-slate-800 pointer-events-auto">
          <div className="relative z-10 w-full flex justify-between items-center">
            <button 
              onClick={() => setCurrentView('TRIPS')} 
              className="text-xs font-bold uppercase tracking-widest liquid-glass-pill text-slate-700 hover:text-slate-950 px-3.5 py-1.5 rounded-full transition-all flex items-center gap-1.5"
            >
              <span>&larr;</span> Back to Trips
            </button>
            <div className="flex items-center gap-6">
              <button 
                type="button" 
                onClick={() => setRomeBuddyOpen(true)} 
                className="cursor-pointer liquid-glass-pill text-slate-700 hover:text-slate-950 px-3.5 py-1.5 rounded-full flex items-center gap-2 focus:outline-none transition-all group"
              >
                <img src="/rome_buddy_logo.png" alt="RB" className="w-5 h-5 rounded-full object-contain border border-slate-300 group-hover:scale-110 transition-transform bg-white shadow-xs" />
                <span className="text-xs font-bold uppercase tracking-wider">Rome Buddy</span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              </button>
              <div className="font-serif font-bold text-2xl tracking-widest text-slate-900 cursor-pointer" onClick={() => setCurrentView('TRIPS')}>ROAM</div>
            </div>
          </div>
        </header>
      </div>

      {/* GLASSY SCROLLABLE FRAME FLANKED BY POLAROIDS */}
      <div className="flex-1 w-full flex justify-center items-start px-4 sm:px-8 pb-4 relative z-20 overflow-hidden">
        <div className="w-full max-w-[1140px] h-full liquid-glass-frame custom-glass-scrollbar overflow-y-auto p-6 md:p-8 relative">
        
        {/* HERO SECTION */}
        <div className="flex flex-col md:flex-row gap-12 items-center mb-12">
          <div className="flex-1 w-full">
            <span className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-4 block">YOUR JOURNEY</span>
            <div className="flex items-center gap-4 mb-6">
              <h1 className="text-5xl md:text-7xl font-serif text-slate-900 leading-tight">{trip.name || trip.destination}</h1>
              <div className="flex gap-2">
                <button 
                  onClick={() => {
                    const newName = prompt("Enter new trip name:", trip.name);
                    if (newName && newName !== trip.name) {
                      updateTrip(trip.id, { ...trip, name: newName });
                    }
                  }}
                  className="px-3 py-1 border border-slate-200 text-slate-500 rounded-full text-xs font-bold uppercase tracking-widest hover:bg-slate-100 transition-colors"
                >
                  Rename
                </button>
                <button 
                  onClick={() => {
                    if (window.confirm("Are you sure you want to delete this trip?")) {
                      deleteTrip(trip.id);
                      setCurrentView('TRIPS');
                    }
                  }}
                  className="px-3 py-1 border border-red-200 text-red-500 rounded-full text-xs font-bold uppercase tracking-widest hover:bg-red-50 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
            <p className="text-xl text-slate-600 mb-8 font-light leading-relaxed">{trip.start_date} &mdash; {trip.end_date}</p>
            <div className="flex gap-4 items-center flex-wrap">
              <span className="bg-emerald-100 text-emerald-800 px-4 py-2 rounded-full font-bold text-xs uppercase tracking-wider">Active Trip</span>
              <button onClick={handleValidate} className="px-6 py-2 border border-slate-300 text-slate-600 rounded-full hover:bg-slate-100 text-sm font-bold uppercase tracking-widest transition-all">
                {isValidating ? 'Validating...' : 'Validate'}
              </button>
              <div className="text-xs px-3.5 py-2 bg-slate-100 text-slate-700 rounded-full uppercase tracking-wider font-bold flex items-center gap-2 shadow-xs">
                <span className="relative flex h-2.5 w-2.5">
                  {locationPermission === 'Active' && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
                  <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${locationPermission === 'Active' ? 'bg-emerald-500' : 'bg-orange-500'}`}></span>
                </span>
                <span>GPS:</span>
                <span className={`font-black ${locationPermission === 'Active' ? 'text-emerald-600' : 'text-orange-600'}`}>
                  {locationPermission === 'Active' ? 'LIVE ACTIVE' : locationPermission}
                </span>
                {locationPermission !== 'Active' && (
                  <button 
                    className="ml-1 px-2.5 py-1 bg-slate-900 text-white hover:bg-slate-800 rounded-full text-[10px] font-bold tracking-wider transition-all shadow-xs cursor-pointer"
                    onClick={() => {
                      setLocationEnabled(true);
                      if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(
                          (pos) => {
                            setLocationPermission("Active");
                            setCurrentLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
                          },
                          (err) => console.warn(err),
                          { enableHighAccuracy: true }
                        );
                      }
                    }}
                  >
                    Enable Live GPS
                  </button>
                )}
              </div>
            </div>
            
            {/* Demo Controls inline and quiet */}
            {/* Demo Controls inline and quiet */}
            <div className="mt-12 p-6 border border-slate-200 rounded-3xl bg-white/50 backdrop-blur-sm shadow-sm">
              <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-orange-500 animate-pulse"></div>
                  <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500">Live Trip & Weather Demo</h3>
                </div>
                <span className="text-[11px] text-slate-400 font-medium">GPS: {currentLocation ? `${currentLocation.lat.toFixed(4)}, ${currentLocation.lng.toFixed(4)}` : 'Active'}</span>
              </div>
              <div className="flex gap-3 flex-wrap">
                <button 
                  className="px-4 py-2 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 rounded-full text-xs font-medium transition-colors shadow-sm" 
                  onClick={() => {
                    fetch(`http://localhost:8000/api/monitor/${trip.id}/simulate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event: 'start' }) });
                    setLiveStatus("Active - On schedule");
                    setLiveMessages(prev => ["Trip started! Live GPS tracking and OpenWeather monitoring active.", ...prev]);
                  }}
                >
                  Start Trip
                </button>

                <button 
                  className="px-4 py-2 border border-blue-200 bg-blue-50/80 hover:bg-blue-100 text-blue-700 rounded-full text-xs font-medium transition-colors shadow-sm" 
                  onClick={() => {
                    // Arrive at the currently active stop ONLY
                    const currentStops = trip?.days?.[0]?.stops || [];
                    const activeStop = currentStops.find(s => s.status !== 'COMPLETED' && !s.completed) || currentStops[0];
                    if (!activeStop) return;

                    const targetLat = activeStop.latitude || 17.540601;
                    const targetLng = activeStop.longitude || 78.386412;
                    setCurrentLocation({ lat: targetLat, lng: targetLng });

                    fetch(`http://localhost:8000/api/monitor/${trip.id}/location`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ latitude: targetLat, longitude: targetLng, accuracy: 5, timestamp: new Date().toISOString() })
                    }).catch(e => console.warn(e));

                    arrivedStopsRef.current.add(activeStop.id);
                    useTripStore.setState(state => {
                      if (!state.trip) return state;
                      const updated = JSON.parse(JSON.stringify(state.trip));
                      updated.days?.forEach(d => {
                        d.stops?.forEach(s => {
                          if (s.id === activeStop.id) {
                            s.status = 'COMPLETED';
                            s.completed = true;
                          }
                        });
                      });
                      return { trip: updated };
                    });
                    setLiveMessages(prev => [`📍 Geotag Verified: You have arrived at ${activeStop.title}! Checked in itinerary.`, ...prev]);
                  }}
                >
                  📍 GPS Arrived at Stop
                </button>

                <button 
                  className="px-4 py-2 border border-amber-200 bg-amber-50/80 hover:bg-amber-100 text-amber-800 rounded-full text-xs font-medium transition-colors shadow-sm" 
                  onClick={() => {
                    // Geotag finds user in a DIFFERENT place (didn't reach the scheduled stop) -> trigger delay popup
                    const currentStops = trip?.days?.[0]?.stops || [];
                    const activeStop = currentStops.find(s => s.status !== 'COMPLETED' && !s.completed) || currentStops[0];
                    if (!activeStop) return;

                    // Set location ~15 km away (different place)
                    const diffLat = (activeStop.latitude || 17.54) + 0.12;
                    const diffLng = (activeStop.longitude || 78.38) + 0.12;
                    setCurrentLocation({ lat: diffLat, lng: diffLng });

                    fetch(`http://localhost:8000/api/monitor/${trip.id}/location`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ latitude: diffLat, longitude: diffLng, accuracy: 5, timestamp: new Date().toISOString() })
                    }).catch(e => console.warn(e));

                    const delayMins = 15;
                    setLiveStatus(`${delayMins} min behind`);
                    const msg = `⚠️ Real-Time Disruption: Geotag detects your location in a different place (15 km away). You haven't reached ${activeStop.title}!`;
                    setLiveMessages(prev => [msg, ...prev]);

                    if (!alertedDelayStopsRef.current.has(activeStop.id)) {
                      alertedDelayStopsRef.current.add(activeStop.id);
                    }
                    simulateDisruption('NORMAL_DELAY', activeStop.id, delayMins);
                  }}
                >
                  ⚠️ GPS in Diff Place (Delay)
                </button>

                <button 
                  className="px-4 py-2 border border-sky-200 bg-sky-50/80 hover:bg-sky-100 text-sky-800 rounded-full text-xs font-medium transition-colors shadow-sm" 
                  onClick={async () => {
                    // Real-time OpenWeather Disruption check (trigger once for current stop)
                    const currentStops = trip?.days?.[0]?.stops || [];
                    const activeStop = currentStops.find(s => s.status !== 'COMPLETED' && !s.completed) || currentStops[0];
                    if (!activeStop) return;

                    try {
                      const res = await fetch(`http://localhost:8000/api/monitor/${trip.id}/check-weather`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ force_rain: true, stop_id: activeStop.id })
                      });
                      const data = await res.json();
                      const rainInfo = data.rain_stops?.[0];
                      const desc = rainInfo?.description || "Heavy rain";
                      const rainMsg = `🌧 Live OpenWeather Alert: Rain detected at ${activeStop.title} (${desc}). Disruption popup activated.`;
                      setLiveMessages(prev => [rainMsg, ...prev]);
                    } catch (e) {
                      setLiveMessages(prev => [`🌧 Live OpenWeather Alert: Rain detected at ${activeStop.title}. Disruption popup activated.`, ...prev]);
                    }

                    if (!alertedWeatherStopsRef.current.has(activeStop.id)) {
                      alertedWeatherStopsRef.current.add(activeStop.id);
                    }
                    simulateDisruption('WEATHER_DISRUPTION', activeStop.id, 15);
                  }}
                >
                  🌧 OpenWeather Rain Disruption
                </button>

                <button 
                  className="px-4 py-2 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 rounded-full text-xs font-medium transition-colors shadow-sm" 
                  onClick={() => {
                    const activeStop = trip?.days?.[0]?.stops?.find(s => s.status !== 'COMPLETED' && !s.completed) || trip?.days?.[0]?.stops?.[0];
                    if (activeStop) {
                      simulateDisruption('NORMAL_DELAY', activeStop.id, 15);
                    }
                  }}
                >
                  +15 min Delay
                </button>
              </div>
            </div>
          </div>
          
          {/* TOP RIGHT: INTERACTIVE MAP (Replacing the street image with 2 polaroids) */}
          <div className="w-full md:w-5/12 lg:w-1/2 h-[480px] bg-white p-3 rounded-[2.5rem] shadow-xl border border-slate-200 relative overflow-hidden">
            <div className="w-full h-full rounded-[2rem] overflow-hidden relative">
              <MapComponent
                stops={stops}
                activeStopId={activeStopId}
                onStopClick={setActiveStopId}
                affectedStopId={impact?.affected_stop_id}
                candidates={recoveryCandidates || []}
                currentLocation={currentLocation}
              />
            </div>
          </div>
        </div>

        {/* VALIDATION */}
        {validationResult && (
          <div className="mb-12 bg-white p-8 rounded-3xl shadow-sm border border-slate-200 max-w-3xl">
            <h3 className="font-serif font-bold text-2xl mb-6">Validation Report</h3>
            {validationResult.valid ? (
              <div className="text-emerald-600 font-medium">âœ“ All good! Your itinerary is physically possible.</div>
            ) : (
              <div className="text-orange-600 font-medium mb-4">âš  {validationResult.issues.length} potential issues found</div>
            )}
            <div className="space-y-4">
              {validationResult.issues.map(issue => (
                <div key={issue.id} className="text-sm bg-orange-50/50 p-4 rounded-xl border border-orange-100">
                  <strong className="text-orange-800">{issue.severity}:</strong> <span className="text-slate-800">{issue.message}</span><br />
                  <span className="text-slate-600 block mt-1">{issue.details}</span>
                  <span className="text-blue-600 font-medium block mt-2">&rarr; {issue.suggested_action}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex flex-col md:flex-row gap-12">
          {/* LEFT COL: ITINERARY */}
          <div className="flex-[2] space-y-12 w-full">
            {/* ITINERARY TIMELINE */}
            <div>
              <h2 className="text-3xl font-serif font-bold text-slate-800 mb-8">Itinerary</h2>

              <div className="pl-6 border-l border-slate-300 space-y-12">
                {stops.map((stop) => (
                  <div key={stop.id} className="relative" onClick={() => setActiveStopId(stop.id)} style={{cursor: "pointer"}}>
                    <div className={`absolute -left-[29px] w-4 h-4 rounded-full border-[3px] border-[#F9F8F6] ${stop.status === 'REPLACED' ? 'bg-emerald-500' : (stop.status === 'COMPLETED' || stop.completed) ? 'bg-blue-600' : stop.status === 'SKIPPED' ? 'bg-red-500' : 'bg-slate-800'}`}></div>
                    <div className="pl-8 flex gap-4">
                      <div className="pt-1">
                        <input type="checkbox" checked={stop.status === 'COMPLETED' || stop.status === 'ARRIVED' || !!stop.completed} onChange={() => toggleStopCheck(trip.id, trip.days[0].id, stop.id)} className="w-5 h-5 cursor-pointer accent-blue-600" />
                      </div>
                      <div className={`flex-1 ${stop.status === 'COMPLETED' || stop.status === 'ARRIVED' || stop.completed || stop.status === 'SKIPPED' ? 'opacity-50 line-through' : ''}`}>
                        <div className="flex items-baseline gap-4 mb-2">
                          <span className="font-bold text-slate-800 w-16">{stop.start_time}</span>
                          <h3 className={`text-2xl font-serif ${stop.status === 'REPLACED' ? 'text-emerald-700' : 'text-slate-900'}`}>{stop.title}</h3>
                        </div>
                      <div className="ml-20">
                        <span className="text-sm text-slate-500 font-medium uppercase tracking-widest">{stop.duration_minutes} MIN &bull; {stop.category}</span>
                        {stop.location_name && <p className="text-slate-600 mt-2">{stop.location_name}</p>}
                        {stop.notes && <p className="text-slate-500 mt-2 italic border-l-2 border-slate-200 pl-4">{stop.notes}</p>}
                        {stop.status === 'REPLACED' && <span className="inline-block mt-3 bg-emerald-50 text-emerald-700 text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider">Replaced</span>}
                        {stop.status === 'SKIPPED' && <span className="inline-block mt-3 bg-red-50 text-red-700 text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider">Skipped</span>}
                        {stop.id === impact?.affected_stop_id && <span className="inline-block mt-3 bg-orange-50 text-orange-700 text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider border border-orange-200">Disrupted</span>}
                      </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* RIGHT COL: ROME BUDDY */}
          <div className="flex-[1] w-full">
            <div className="bg-white p-8 rounded-[2rem] shadow-sm border border-slate-200 sticky top-8">
              <div className="flex justify-between items-center mb-8 border-b border-slate-100 pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-white border border-slate-200 shadow-xs flex items-center justify-center overflow-hidden">
                    <img src="/rome_buddy_logo.png" alt="Rome Buddy" className="w-full h-full object-contain p-1" />
                  </div>
                  <h2 className="text-xl font-serif font-bold text-slate-800">Rome Buddy</h2>
                </div>

                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${liveStatus.includes('behind') ? 'bg-orange-500' : liveStatus !== 'Not Started' ? 'bg-emerald-500' : 'bg-slate-300'}`}></div>
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-500">{liveStatus}</span>
                </div>
              </div>

              {liveMessages.length > 0 && (
                <div className="mb-8 space-y-3">
                  {liveMessages.slice(0, 3).map((msg, idx) => (
                    <motion.div initial={{opacity:0, y:5}} animate={{opacity:1,y:0}} key={idx} className="border-l-2 border-slate-800 pl-4 py-1">
                      <p className="text-sm text-slate-700">{msg}</p>
                      {msg.includes('near') && (
                        <div className="mt-2"><button className="px-4 py-1 bg-slate-900 text-white rounded-full text-xs font-bold uppercase tracking-wider hover:bg-slate-800 transition-colors">Mark Arrived</button></div>
                      )}
                    </motion.div>
                  ))}
                </div>
              )}
              
              <div className="mt-8 border-t border-slate-100 pt-6">
                <h3 className="font-serif font-bold text-lg text-slate-900 mb-4">Ask Rome Buddy</h3>
                <div className="space-y-4 max-h-56 overflow-y-auto mb-4 pr-1">
                  {chatMessages.map((msg, idx) => (
                    <div key={idx} className={`text-sm p-3.5 rounded-2xl ${msg.role === 'user' ? 'bg-slate-100 ml-8 text-right' : 'bg-blue-50/90 text-slate-800 mr-4 text-left shadow-sm border border-blue-100/60 whitespace-pre-line'}`}>
                      {msg.content}
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input 
                    type="text" 
                    value={chatInput} 
                    onChange={e => setChatInput(e.target.value)} 
                    placeholder="Ask Rome Buddy anything (e.g. food near Charminar)..." 
                    className="flex-1 text-sm p-3 border border-slate-200 rounded-full focus:outline-none focus:border-slate-400"
                    onKeyDown={async e => {
                      if (e.key === 'Enter' && chatInput) {
                        const input = chatInput;
                        const tId = trip?.id ? String(trip.id) : 'default';
                        setChatInput('');
                        appendChatMessage(tId, { role: 'user', content: input });
                        try {
                          const reply = await sendCompanionMessage(trip.id, input);
                          appendChatMessage(tId, { role: 'assistant', content: reply });
                        } catch (err) {
                          appendChatMessage(tId, { role: 'assistant', content: "Error connecting to AI." });
                        }
                      }
                    }}
                  />
                  <button 
                    onClick={async () => {
                      if (chatInput) {
                        const input = chatInput;
                        const tId = trip?.id ? String(trip.id) : 'default';
                        setChatInput('');
                        appendChatMessage(tId, { role: 'user', content: input });
                        try {
                          const reply = await sendCompanionMessage(trip.id, input);
                          appendChatMessage(tId, { role: 'assistant', content: reply });
                        } catch (err) {
                          appendChatMessage(tId, { role: 'assistant', content: "Error connecting to AI." });
                        }
                      }
                    }}
                    className="px-6 py-2 bg-slate-900 text-white rounded-full text-xs font-bold uppercase tracking-wider hover:bg-slate-800 transition-colors"
                  >
                    Send
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  );
};

  const renderCurrentView = () => {
    if (currentView === 'LOGIN') return renderLogin();
    if (currentView === 'ALERTS') return renderAlertCenter();
    if (currentView === 'EXPLORE_TRIPS') return renderExploreTrips();
    if (currentView === 'EXPLORE_BOOKINGS') return renderExploreBookings();
    if (currentView === 'LOCAL_EVENTS') {
      return (
        <div className="min-h-screen bg-[#FDFBF7] text-slate-800 pb-16">
          {renderTopNavBar('LOCAL_EVENTS')}
          <LocalEventsSection 
            onBackToTrips={() => setCurrentView('TRIPS')} 
            onOpenRomeBuddy={() => setRomeBuddyOpen(true)} 
          />
        </div>
      );
    }
    if (currentView === 'TRIPS') return renderTrips();
    return renderDashboard();
  };

  return (
    <>
      {renderCurrentView()}
      {currentView !== 'LOGIN' && (
        <RomeBuddyDrawer 
          isOpen={romeBuddyOpen}
          onClose={() => setRomeBuddyOpen(false)}
          onOpen={() => setRomeBuddyOpen(true)}
          trip={trip}
          liveStatus={liveStatus}
          liveMessages={liveMessages}
          chatMessages={chatMessages}
          onSendMessage={handleRomeBuddyMessage}
          onClearChat={handleRomeBuddyClear}
          onExtractItinerary={handleExtractItineraryFromRomeBuddy}
          isExtractingItinerary={isExtractingBuddyItinerary}
          onExtractBooking={handleExtractBookingFromRomeBuddy}
          isExtractingBooking={isExtractingBuddyBooking}
        />
      )}
    </>
  );
}
