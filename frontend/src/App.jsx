import Spline from '@splinetool/react-spline';
import { motion } from 'framer-motion';
import React, { useEffect, useState } from 'react';

const VoiceButton = ({ onTranscribed, disabled }) => {
  const [recording, setRecording] = React.useState(false);
  const [statusText, setStatusText] = React.useState('Voice');
  const mediaRecorder = React.useRef(null);
  const audioChunks = React.useRef([]);

  const toggleRecording = async () => {
    if (recording) {
      mediaRecorder.current.stop();
      setRecording(false);
      setStatusText('Processing...');
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        mediaRecorder.current.ondataavailable = e => { if (e.data.size > 0) audioChunks.current.push(e.data); };
        mediaRecorder.current.onstop = async () => {
          const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' });
          audioChunks.current = [];
          setStatusText('Structuring...');

          const fd = new FormData();
          fd.append('file', audioBlob, 'recording.webm');

          try {
            const res = await fetch('http://localhost:8000/api/voice/transcribe', {
              method: 'POST',
              body: fd
            });
            const data = await res.json();
            if (data.success || data.text) {
              setStatusText('Ready');
              onTranscribed(data.text);
              setTimeout(() => setStatusText('Voice'), 2000);
            } else {
              setStatusText('Error');
              setTimeout(() => setStatusText('Voice'), 2000);
            }
          } catch (e) {
            setStatusText('Network Error');
            setTimeout(() => setStatusText('Voice'), 2000);
          }
        };
        mediaRecorder.current.start();
        setRecording(true);
        setStatusText('Listening...');
      } catch (e) {
        setStatusText('Mic Denied');
        setTimeout(() => setStatusText('Voice'), 2000);
      }
    }
  };

  return (
    <button 
      onClick={toggleRecording} 
      disabled={disabled || (statusText !== 'Voice' && statusText !== 'Listening...' && statusText !== 'Ready')} 
      className={`bg-[#F9F8F6] border border-slate-200 px-6 py-3 rounded-full text-sm font-medium transition-all shadow-sm ${recording ? 'bg-red-500 text-white border-red-500 hover:bg-red-600' : 'text-slate-800 hover:bg-white'}`}
    >
      {recording ? (statusText === 'Listening...' ? 'Stop Recording' : statusText) : statusText}
    </button>
  );
};
import { useTripStore } from './store/tripStore';
import { useAuthStore } from './store/authStore';
import DisruptionRecoveryCard from './components/DisruptionRecoveryCard';


import MapComponent from './components/MapComponent';

export default function App() {
  const [activeStopId, setActiveStopId] = useState(null);
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
        const url = importFileType === 'pdf' ? 'http://localhost:8000/api/import/pdf' : 'http://localhost:8000/api/import/image';
        // Wait, the API for booking extraction is /api/bookings/extract, but it doesn't support file upload yet.
        // Actually, we will update backend to support file on /api/bookings/extract
        const res = await fetch('http://localhost:8000/api/bookings/extract', {
          method: 'POST',
          body: fd
        });
        if (!res.ok) throw new Error('Failed to extract booking');
        const data = await res.json();
        setBookingSummary(data);
        setBookingId(data.flight_number || "mock-booking");
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
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [locationEnabled, setLocationEnabled] = useState(false);
  const [locationPermission, setLocationPermission] = useState("Prompt");
  const [currentLocation, setCurrentLocation] = useState(null);
  const [monitoringMode, setMonitoringMode] = useState('TRIP');
  const [bookingSummary, setBookingSummary] = useState(null);
  const [bookingId, setBookingId] = useState(null);
  const [gmailConnected, setGmailConnected] = useState(false);
  const [gmailEmail, setGmailEmail] = useState(null);
  const [importing, setImporting] = useState(false);
  const [bookingMonitoringActive, setBookingMonitoringActive] = useState(false);
  const [bookingAlert, setBookingAlert] = useState(null);
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
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(loc)
            });
          }
        },
        (err) => {
          console.error("GPS Error", err);
          setLocationPermission("Denied/Error");
        },
        { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
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
        setBookingId(data.flight_number || "mock-booking");
        setShowImportModal(false);
        setImportText("");
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

  const handleSaveTrip = async () => {
    if (!pendingTrip) return;
    await saveTrip(pendingTrip);
    setPendingTrip(null);
    setShowImportModal(false);
    setImportText("");
  };
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

      {/* Header */}
      <header className="p-8 flex justify-between items-center text-slate-800">
        <div className="flex items-center gap-8">
          <div className="font-serif font-bold text-2xl tracking-widest">ROAM</div>
          <nav className="hidden md:flex gap-6 text-sm font-medium tracking-wide">
            <span className="cursor-pointer border-b border-slate-800 pb-1">Trip</span>
            <span className="cursor-pointer text-slate-500 hover:text-slate-800">Explore</span>
            <span className="cursor-pointer text-slate-500 hover:text-slate-800">AI Companion</span>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          {isDemoMode ? (
            <span className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full font-bold text-xs uppercase tracking-wider">Demo</span>
          ) : (
            <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full font-bold text-xs uppercase tracking-wider">Live</span>
          )}
          <button onClick={() => setCurrentView('ALERTS')} className="text-sm font-medium hover:text-stone-500 transition-colors uppercase tracking-widest relative">
            ALERTS
            {alerts.some(a => !a.is_read) && <span className="absolute -top-1 -right-3 text-orange-500 text-lg leading-none">•</span>}
          </button>
          <button onClick={() => { logout(); setCurrentView('LOGIN'); }} className="text-sm font-medium hover:text-stone-500 transition-colors uppercase tracking-widest">Logout</button>
        </div>
      </header>
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

                
                <div className="flex gap-4">
                  {bookingSummary && monitoringMode === 'BOOKINGS' ? (
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 w-full">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="font-serif font-bold text-2xl tracking-widest">{bookingSummary.provider?.toUpperCase()}</h3>
                          <p className="text-sm font-bold text-slate-500 tracking-widest">{bookingSummary.service_number}</p>
                        </div>
                        <div className="text-right">
                          <span className="bg-slate-100 text-slate-800 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest">{bookingSummary.booking_status || "Confirmed"}</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4 mb-6 mt-6">
                        <div className="flex-1">
                          <p className="text-sm text-slate-500 uppercase tracking-widest font-bold">Origin</p>
                          <p className="font-serif text-lg">{bookingSummary.origin || "Unknown"}</p>
                        </div>
                        <span className="text-slate-300">&rarr;</span>
                        <div className="flex-1 text-right">
                          <p className="text-sm text-slate-500 uppercase tracking-widest font-bold">Destination</p>
                          <p className="font-serif text-lg">{bookingSummary.destination || "Unknown"}</p>
                        </div>
                      </div>

                      <div className="flex justify-between items-end border-t border-slate-100 pt-4">
                        <div>
                          <p className="text-xs text-slate-500 uppercase tracking-widest font-bold mb-1">Departure</p>
                          <p className="text-sm font-medium">{bookingSummary.original_departure ? new Date(bookingSummary.original_departure).toLocaleString() : "Unknown"}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-slate-500 uppercase tracking-widest font-bold mb-1">Booking Ref</p>
                          <p className="text-sm font-medium font-mono">{bookingSummary.booking_reference || "N/A"}</p>
                        </div>
                      </div>
                      
                      {!gmailConnected ? (
                        <button onClick={() => {
                          fetch('http://localhost:8000/api/gmail/connect').then(() => setGmailConnected(true));
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
                  ) : (
                    <>
                      <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept={importFileType === 'pdf' ? '.pdf' : 'image/*'} />
                      <button onClick={() => setShowImportModal(true)} disabled={importing} className="bg-slate-900 text-white px-6 py-3 rounded-full text-sm font-medium hover:bg-slate-800 transition-all shadow-md">Paste Text</button>
                      
                      <button onClick={() => handleImport('pdf')} disabled={importing} className="bg-[#F9F8F6] border border-slate-200 text-slate-800 px-6 py-3 rounded-full text-sm font-medium hover:bg-white transition-all shadow-sm">Upload PDF</button>
                      
                      <button onClick={() => handleImport('image')} disabled={importing} className="bg-[#F9F8F6] border border-slate-200 text-slate-800 px-6 py-3 rounded-full text-sm font-medium hover:bg-white transition-all shadow-sm">Upload Image</button>

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
                      {monitoringMode === 'TRIP' && (
                        <VoiceButton disabled={importing} onTranscribed={async (text) => {
                           setImporting(true);
                           try {
                             const res = await fetch('http://localhost:8000/api/import/text', {
                               method: 'POST',
                               headers: { 'Content-Type': 'application/json' },
                               body: JSON.stringify({ text })
                             });
                             if (!res.ok) throw new Error('Failed to structure itinerary from voice');
                             loadDemoTrip();
                           } catch (err) {
                             console.error(err);
                           } finally {
                             setImporting(false);
                           }
                        }} />
                      )}
                    </>
                  )}
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


            <div className="flex flex-col gap-8">
              {trips.length === 0 ? (
                <p className="text-slate-500 font-serif italic text-lg">No trips yet. Import one to get started.</p>
              ) : (
                trips.map(t => (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    key={t.id} 
                    onClick={() => { loadTrip(t.id); setCurrentView('DASHBOARD'); }} 
                    className="group bg-white p-8 rounded-3xl shadow-sm border border-slate-100 cursor-pointer hover:shadow-xl transition-all duration-500 flex flex-col md:flex-row gap-8 items-center"
                  >
                    <div className="w-full md:w-48 h-32 bg-slate-100 rounded-2xl overflow-hidden relative flex-shrink-0">
                      <img src="/roam_image_assets/destinations/destination_art_gallery.png" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" alt="trip cover" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] uppercase font-bold tracking-wider px-2 py-1 rounded-full">Active</span>
                        <span className="text-slate-400 text-sm font-medium tracking-wide">{t.start_date} &mdash; {t.end_date}</span>
                      </div>
                      <h3 className="text-3xl font-bold text-slate-800 font-serif mb-2 group-hover:text-blue-900 transition-colors">{t.name || t.destination || "Trip"}</h3>
                      <p className="text-slate-500 text-sm">{t.days?.reduce((acc, d) => acc + d.stops?.length || 0, 0) || 0} Stops Planned</p>
                    </div>
                    <div className="hidden md:flex opacity-0 group-hover:opacity-100 transition-opacity pr-4">
                      <span className="text-slate-400 text-2xl">&rarr;</span>
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          </>
        ) : (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col md:flex-row gap-16 items-center"
          >
            {/* Left Content */}
            <div className="flex-1 w-full">
              {!pendingTrip && (!bookingSummary || monitoringMode !== 'BOOKINGS') ? (
                <>
                  <button onClick={() => { setShowImportModal(false); setImportStatus(""); setImportText(""); }} className="mb-12 text-sm font-bold tracking-widest text-slate-400 hover:text-slate-800 uppercase transition-colors">&larr; Back</button>
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
                    {monitoringMode === 'BOOKINGS' ? "Paste your flight ticket, hotel confirmation, train ticket, reservation, or booking details here..." : "Paste an itinerary or upload the plan you already have."}
                  </p>
                  
                  <textarea 
                    className="w-full h-64 bg-white border border-slate-200 shadow-inner rounded-2xl p-6 font-serif text-lg mb-6 focus:ring-2 focus:ring-slate-300 focus:outline-none resize-none transition-shadow"
                    placeholder={monitoringMode === 'BOOKINGS' ? "Paste your booking information..." : "Paste your text itinerary here..."}
                    value={importText}
                    onChange={(e) => setImportText(e.target.value)}
                    disabled={importing}
                  ></textarea>
                  
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
                    <h3 className="font-serif font-bold text-2xl text-slate-800 mb-6 pb-4 border-b border-slate-100">{pendingTrip.name || "Trip"} to {pendingTrip.destination || "Unknown"}</h3>
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
    </div>
  );

  const renderAlertCenter = () => (
    <div className="min-h-screen relative font-sans bg-[#E5DED2] pt-8">
      <div className="max-w-4xl mx-auto px-8 relative">
        <header className="flex justify-between items-center text-slate-800 mb-12">
          <button onClick={() => setCurrentView('TRIPS')} className="text-sm font-bold uppercase tracking-widest text-slate-400 hover:text-slate-800 transition-colors">&larr; Back to Dashboard</button>
          <div className="font-serif font-bold text-xl tracking-widest">ALERT CENTER</div>
        </header>

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

  if (currentView === 'LOGIN') return renderLogin();
  if (currentView === 'ALERTS') return renderAlertCenter();
  if (currentView === 'TRIPS') return renderTrips();

  if (!trip) return <div className="p-8">Loading...</div>;
  const stops = trip?.days?.[0]?.stops || [];

return (
    <div className="min-h-screen bg-[#E5DED2] font-sans pb-24">
      <DisruptionRecoveryCard />
      <header className="p-8 flex justify-between items-center text-slate-800 max-w-7xl mx-auto">
        <button onClick={() => setCurrentView('TRIPS')} className="text-sm font-bold uppercase tracking-widest text-slate-400 hover:text-slate-800 transition-colors">&larr; Back to Trips</button>
        <div className="font-serif font-bold text-xl tracking-widest opacity-50">ROAM</div>
      </header>

      <div className="max-w-7xl mx-auto px-8">
        
        {/* HERO SECTION */}
        <div className="flex flex-col md:flex-row gap-16 items-center mb-16">
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
              <div className="text-xs px-3 py-2 bg-slate-100 text-slate-600 rounded-full uppercase tracking-widest font-bold">
                ðŸ“ Location:
                <span className={`ml-1 ${locationPermission === 'Active' ? 'text-emerald-600' : 'text-orange-600'}`}>
                  {locationPermission}
                </span>
                {!locationEnabled && (
                  <button className="ml-2 text-slate-800 hover:text-slate-500 underline" onClick={() => setLocationEnabled(true)}>Enable</button>
                )}
              </div>
            </div>
            
            {/* Demo Controls inline and quiet */}
            <div className="mt-12 p-6 border border-slate-200 rounded-3xl bg-white/50 backdrop-blur-sm shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-2 h-2 rounded-full bg-orange-500 animate-pulse"></div>
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500">Live Trip Demo</h3>
              </div>
              <div className="flex gap-3 flex-wrap">
                <button className="px-4 py-2 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 rounded-full text-xs font-medium transition-colors shadow-sm" onClick={() => fetch(`http://localhost:8000/api/monitor/${trip.id}/simulate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event: 'start' }) })}>Start Trip</button>
                <button className="px-4 py-2 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 rounded-full text-xs font-medium transition-colors shadow-sm" onClick={() => { fetch(`http://localhost:8000/api/monitor/${trip.id}/simulate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event: 'delay', value: 15 }) }); simulateDisruption('NORMAL_DELAY', trip?.days?.[0]?.stops?.find(s => s.status === 'UPCOMING')?.id || trip?.days?.[0]?.stops?.find(s => s.status !== 'COMPLETED' && s.status !== 'SKIPPED')?.id, 15); }}>+15 min Delay</button>
                <button className="px-4 py-2 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 rounded-full text-xs font-medium transition-colors shadow-sm" onClick={() => { fetch(`http://localhost:8000/api/monitor/${trip.id}/simulate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event: 'weather' }) }); simulateDisruption('WEATHER_DISRUPTION', trip?.days?.[0]?.stops?.find(s => s.status === 'UPCOMING')?.id || trip?.days?.[0]?.stops?.find(s => s.status !== 'COMPLETED' && s.status !== 'SKIPPED')?.id, 15); }}>Weather Disruption</button>
                <button className="px-4 py-2 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 rounded-full text-xs font-medium transition-colors shadow-sm" onClick={() => {
                  fetch(`http://localhost:8000/api/monitor/${trip.id}/location`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ latitude: 17.385, longitude: 78.486, accuracy: 10, timestamp: new Date().toISOString() }) });
                }}>GPS Arrive</button>
              </div>
            </div>
          </div>
          
          <div className="hidden md:block w-5/12 relative h-[500px]">
            <div className="absolute inset-0 rounded-[2.5rem] overflow-hidden shadow-2xl">
              <img src="/roam_image_assets/destinations/destination_city_street.png" className="w-full h-full object-cover" alt="Destination" />
            </div>
            <motion.div 
              animate={{ y: [0, 4, 0], rotate: [-3, -3, -3] }}
              transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
              className="absolute top-8 -left-8 w-44 p-3 bg-white shadow-xl"
            >
              <div className="border border-slate-100 h-44 overflow-hidden mb-4">
                <img src="/roam_image_assets/instax/instax_blue_city_view.png" className="w-full h-full object-cover" alt="Memory" />
              </div>
            </motion.div>
            <motion.div 
              animate={{ y: [0, -3, 0], rotate: [4, 4, 4] }}
              transition={{ duration: 6, repeat: Infinity, ease: "easeInOut", delay: 2 }}
              className="absolute bottom-8 -right-6 w-52 p-3 bg-white shadow-xl"
            >
              <div className="border border-slate-100 h-52 overflow-hidden mb-4">
                <img src="/roam_image_assets/instax/instax_cycling_sunset.png" className="w-full h-full object-cover" alt="Memory" />
              </div>
            </motion.div>
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
          {/* LEFT COL: MAP & ITINERARY */}
          <div className="flex-[2] space-y-12 w-full">
            
            {/* MAP SECTION */}
            <div className="w-full h-[400px] bg-white p-4 rounded-[3rem] shadow-lg border border-slate-200 relative">
              <div className="w-full h-full rounded-[2.5rem] overflow-hidden relative">
                
        <div className="bg-gray-800 text-white p-4 rounded-xl shadow mb-6">
          <h2 className="text-xl font-bold mb-2 flex items-center">
            <span className="text-red-500 mr-2">● </span> LIVE Trip Demo Panel
          </h2>

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

          <div className="flex gap-2 flex-wrap">
            <button className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm" onClick={() => fetch(`http://localhost:8000/api/monitor/${trip.id}/simulate`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({event: 'start'})})}>Start Trip</button>
            <button className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm" onClick={() => { fetch(`http://localhost:8000/api/monitor/${trip.id}/simulate`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({event: 'delay', value: 15})}); simulateDisruption('NORMAL_DELAY', stops.find(s => s.status === 'UPCOMING')?.id || stops.find(s => s.status !== 'COMPLETED' && s.status !== 'SKIPPED')?.id, 15); }}>+15 min delay</button>
            <button className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm" onClick={() => { fetch(`http://localhost:8000/api/monitor/${trip.id}/simulate`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({event: 'weather'})}); simulateDisruption('WEATHER_DISRUPTION', stops.find(s => s.status === 'UPCOMING')?.id || stops.find(s => s.status !== 'COMPLETED' && s.status !== 'SKIPPED')?.id); }}>Simulate Rain</button>
          </div>
        </div>
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

            {/* ITINERARY TIMELINE */}
            <div>
              <h2 className="text-3xl font-serif font-bold text-slate-800 mb-8">Itinerary</h2>



              <div className="pl-6 border-l border-slate-300 space-y-12">
                {stops.map((stop) => (
                  <div key={stop.id} className="relative" onClick={() => setActiveStopId(stop.id)} style={{cursor: "pointer"}}>
                    <div className={`absolute -left-[29px] w-4 h-4 rounded-full border-[3px] border-[#F9F8F6] ${stop.status === 'REPLACED' ? 'bg-emerald-500' : stop.status === 'COMPLETED' ? 'bg-blue-600' : stop.status === 'SKIPPED' ? 'bg-red-500' : 'bg-slate-800'}`}></div>
                    <div className="pl-8 flex gap-4">
                      <div className="pt-1">
                        <input type="checkbox" checked={stop.status === 'COMPLETED'} onChange={() => toggleStopCheck(trip.id, trip.days[0].id, stop.id)} className="w-5 h-5 cursor-pointer accent-blue-600" />
                      </div>
                      <div className={`flex-1 ${stop.status === 'COMPLETED' || stop.status === 'SKIPPED' ? 'opacity-50 line-through' : ''}`}>
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

          {/* RIGHT COL: AI COMPANION */}
          <div className="flex-[1] w-full">
            <div className="bg-white p-8 rounded-[2rem] shadow-sm border border-slate-200 sticky top-8">
              <div className="flex justify-between items-center mb-8 border-b border-slate-100 pb-4">
                <h2 className="text-xl font-serif font-bold text-slate-800">AI Companion</h2>



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
                <h3 className="font-serif font-bold text-lg text-slate-900 mb-4">Ask about your trip</h3>
                <div className="space-y-4 max-h-48 overflow-y-auto mb-4">
                  {chatMessages.map((msg, idx) => (
                    <div key={idx} className={`text-sm p-3 rounded-2xl ${msg.role === 'user' ? 'bg-slate-100 ml-8 text-right' : 'bg-blue-50 mr-8 text-left'}`}>
                      {msg.content}
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input 
                    type="text" 
                    value={chatInput} 
                    onChange={e => setChatInput(e.target.value)} 
                    placeholder="E.g. What's next?" 
                    className="flex-1 text-sm p-3 border border-slate-200 rounded-full focus:outline-none focus:border-slate-400"
                    onKeyDown={async e => {
                      if (e.key === 'Enter' && chatInput) {
                        const input = chatInput;
                        setChatInput('');
                        setChatMessages(prev => [...prev, {role: 'user', content: input}]);
                        try {
                          const reply = await sendCompanionMessage(trip.id, input);
                          setChatMessages(prev => [...prev, {role: 'assistant', content: reply}]);
                        } catch (err) {
                          setChatMessages(prev => [...prev, {role: 'assistant', content: "Error connecting to AI."}]);
                        }
                      }
                    }}
                  />
                  <button 
                    onClick={async () => {
                      if (chatInput) {
                        const input = chatInput;
                        setChatInput('');
                        setChatMessages(prev => [...prev, {role: 'user', content: input}]);
                        try {
                          const reply = await sendCompanionMessage(trip.id, input);
                          setChatMessages(prev => [...prev, {role: 'assistant', content: reply}]);
                        } catch (err) {
                          setChatMessages(prev => [...prev, {role: 'assistant', content: "Error connecting to AI."}]);
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
  );
}
