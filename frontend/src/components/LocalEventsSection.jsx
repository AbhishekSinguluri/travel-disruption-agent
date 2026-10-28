import React, { useState, useEffect, useRef } from 'react';
import { useTripStore } from '../store/tripStore';

// All 28 Indian States + 8 Union Territories
const ALL_INDIAN_STATES = [
  { key: "andaman and nicobar", name: "Andaman & Nicobar Islands", hub: "Port Blair", icon: "🏝️", is_cached: false },
  { key: "andhra pradesh", name: "Andhra Pradesh", hub: "Visakhapatnam", icon: "🌊", is_cached: false },
  { key: "arunachal pradesh", name: "Arunachal Pradesh", hub: "Itanagar", icon: "⛰️", is_cached: false },
  { key: "assam", name: "Assam", hub: "Guwahati", icon: "🦏", is_cached: false },
  { key: "bihar", name: "Bihar", hub: "Patna", icon: "🏛️", is_cached: false },
  { key: "chandigarh", name: "Chandigarh", hub: "Chandigarh", icon: "🌹", is_cached: false },
  { key: "chhattisgarh", name: "Chhattisgarh", hub: "Raipur", icon: "🌳", is_cached: false },
  { key: "dadra and nagar haveli", name: "Dadra & Nagar Haveli and Daman & Diu", hub: "Daman", icon: "🏖️", is_cached: false },
  { key: "delhi", name: "Delhi NCR", hub: "New Delhi", icon: "🏛️", is_cached: false },
  { key: "goa", name: "Goa", hub: "Panaji", icon: "🏖️", is_cached: false },
  { key: "gujarat", name: "Gujarat", hub: "Ahmedabad", icon: "🪁", is_cached: false },
  { key: "haryana", name: "Haryana", hub: "Gurugram", icon: "🏙️", is_cached: false },
  { key: "himachal pradesh", name: "Himachal Pradesh", hub: "Shimla", icon: "🏔️", is_cached: false },
  { key: "jammu and kashmir", name: "Jammu & Kashmir", hub: "Srinagar", icon: "🛶", is_cached: false },
  { key: "jharkhand", name: "Jharkhand", hub: "Ranchi", icon: "🌲", is_cached: false },
  { key: "karnataka", name: "Karnataka", hub: "Bengaluru", icon: "💻", is_cached: false },
  { key: "kerala", name: "Kerala", hub: "Kochi", icon: "🌴", is_cached: false },
  { key: "ladakh", name: "Ladakh", hub: "Leh", icon: "🏔️", is_cached: false },
  { key: "lakshadweep", name: "Lakshadweep", hub: "Kavaratti", icon: "🐠", is_cached: false },
  { key: "madhya pradesh", name: "Madhya Pradesh", hub: "Indore", icon: "🐅", is_cached: false },
  { key: "maharashtra", name: "Maharashtra", hub: "Mumbai", icon: "🎬", is_cached: true },
  { key: "manipur", name: "Manipur", hub: "Imphal", icon: "🌸", is_cached: false },
  { key: "meghalaya", name: "Meghalaya", hub: "Shillong", icon: "☁️", is_cached: false },
  { key: "mizoram", name: "Mizoram", hub: "Aizawl", icon: "🎋", is_cached: false },
  { key: "nagaland", name: "Nagaland", hub: "Kohima", icon: "🪶", is_cached: false },
  { key: "odisha", name: "Odisha", hub: "Bhubaneswar", icon: "🛕", is_cached: false },
  { key: "puducherry", name: "Puducherry", hub: "Puducherry", icon: "⛵", is_cached: false },
  { key: "punjab", name: "Punjab", hub: "Amritsar", icon: "🌾", is_cached: false },
  { key: "rajasthan", name: "Rajasthan", hub: "Jaipur", icon: "🏰", is_cached: true },
  { key: "sikkim", name: "Sikkim", hub: "Gangtok", icon: "❄️", is_cached: false },
  { key: "tamil nadu", name: "Tamil Nadu", hub: "Chennai", icon: "🏛️", is_cached: false },
  { key: "telangana", name: "Telangana", hub: "Hyderabad", icon: "🕌", is_cached: true },
  { key: "tripura", name: "Tripura", hub: "Agartala", icon: "🍃", is_cached: false },
  { key: "uttar pradesh", name: "Uttar Pradesh", hub: "Varanasi", icon: "🪔", is_cached: false },
  { key: "uttarakhand", name: "Uttarakhand", hub: "Dehradun", icon: "🏔️", is_cached: false },
  { key: "west bengal", name: "West Bengal", hub: "Kolkata", icon: "🎨", is_cached: false }
];

export default function LocalEventsSection({ onBackToTrips, onOpenRomeBuddy }) {
  const [selectedState, setSelectedState] = useState(
    ALL_INDIAN_STATES.find(s => s.key === 'maharashtra') || ALL_INDIAN_STATES[0]
  );
  const [statesList, setStatesList] = useState(ALL_INDIAN_STATES);
  const [searchQuery, setSearchQuery] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [cachedCount, setCachedCount] = useState(3);
  
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeCategory, setActiveCategory] = useState('All');
  const [isCached, setIsCached] = useState(true);
  const [creditsUsed, setCreditsUsed] = useState(0);
  const [lastUpdated, setLastUpdated] = useState('');
  
  // Booking modal state
  const [bookingModalEvent, setBookingModalEvent] = useState(null);
  const [ticketCount, setTicketCount] = useState(2);
  const [attendeeName, setAttendeeName] = useState('Demo Traveler');
  const [bookingSubmitting, setBookingSubmitting] = useState(false);
  const [confirmedBooking, setConfirmedBooking] = useState(null);

  const searchContainerRef = useRef(null);
  const { trip, addAlert } = useTripStore();

  const categories = ['All', 'Heritage & Tours', 'Live Music', 'Theater & Comedy', 'Workshops & Crafts'];

  // Load directory status on mount
  useEffect(() => {
    fetch('http://localhost:8000/api/events/states')
      .then(res => res.json())
      .then(data => {
        if (data?.states && data.states.length > 0) {
          setStatesList(data.states);
          setCachedCount(data.cached_count || 0);
        }
      })
      .catch(err => console.error("Error fetching states:", err));
  }, []);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchEvents = async (stateKey, forceRefresh = false) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://localhost:8000/api/events?city=${encodeURIComponent(stateKey)}&force=${forceRefresh}`);
      if (!res.ok) throw new Error("Failed to load local events");
      const data = await res.json();
      setEvents(data.events || []);
      setIsCached(data.cached !== false);
      setCreditsUsed(data.credits_used || 0);
      setLastUpdated(data.last_updated || new Date().toLocaleTimeString());
      
      // Update local cache status
      setStatesList(prev => prev.map(s => s.key === stateKey ? { ...s, is_cached: true } : s));
    } catch (err) {
      console.error("Events fetch error:", err);
      setError("Unable to connect to live event engine. Displaying offline highlights.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents(selectedState.key, false);
  }, [selectedState]);

  // Autocomplete filtering based on relevance and alphabet
  const filteredStates = statesList.filter(s => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase().trim();
    return s.name.toLowerCase().includes(q) || s.hub.toLowerCase().includes(q) || s.key.includes(q);
  }).sort((a, b) => {
    if (!searchQuery.trim()) return a.name.localeCompare(b.name);
    const q = searchQuery.toLowerCase().trim();
    const aStarts = a.name.toLowerCase().startsWith(q) || a.hub.toLowerCase().startsWith(q);
    const bStarts = b.name.toLowerCase().startsWith(q) || b.hub.toLowerCase().startsWith(q);
    if (aStarts && !bStarts) return -1;
    if (!aStarts && bStarts) return 1;
    return a.name.localeCompare(b.name);
  });

  const handleSelectState = (stateObj) => {
    setSelectedState(stateObj);
    setSearchQuery('');
    setIsDropdownOpen(false);
  };

  const filteredEvents = activeCategory === 'All' 
    ? events 
    : events.filter(e => e.category?.toLowerCase().includes(activeCategory.toLowerCase()) || activeCategory.toLowerCase().includes(e.category?.toLowerCase() || ''));

  const handleOpenBooking = (event) => {
    setBookingModalEvent(event);
    setConfirmedBooking(null);
    setTicketCount(2);
  };

  const handleConfirmBooking = async () => {
    if (!bookingModalEvent) return;
    setBookingSubmitting(true);
    try {
      const res = await fetch('http://localhost:8000/api/events/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event: bookingModalEvent,
          tickets: ticketCount,
          attendee_name: attendeeName
        })
      });
      const data = await res.json();
      if (data.success && data.booking) {
        setConfirmedBooking(data.booking);
        // Post notification to store alerts
        if (addAlert) {
          addAlert({
            id: `alert-${Date.now()}`,
            title: "Event Booking Confirmed",
            change: {
              type: "BOOKING_CONFIRMED",
              description: `Reserved ${ticketCount} ticket(s) for ${bookingModalEvent.title} (${data.booking.booking_reference})`
            },
            severity: "LOW",
            timestamp: new Date().toISOString()
          });
        }
      } else {
        alert("Booking failed: " + (data.message || "Unknown error"));
      }
    } catch (err) {
      console.error("Booking error:", err);
      alert("Failed to confirm booking. Backend may be offline.");
    } finally {
      setBookingSubmitting(false);
    }
  };

  return (
    <div className="w-full px-4 sm:px-6 md:px-8 lg:px-10 py-6 animate-in fade-in duration-300">
      {/* Top Banner & Header - relative z-30 without overflow-hidden so autocomplete dropdown is never clipped */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white rounded-[2.5rem] p-8 md:p-12 mb-8 shadow-2xl relative z-30">
        {/* Ambient Blur Backdrop - isolated overflow-hidden so glow doesn't bleed out */}
        <div className="absolute inset-0 rounded-[2.5rem] overflow-hidden pointer-events-none">
          <div className="absolute top-0 right-0 -mr-16 -mt-16 w-80 h-80 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none"></div>
          <div className="absolute bottom-0 left-1/3 -mb-20 w-80 h-80 bg-amber-500/15 rounded-full blur-3xl pointer-events-none"></div>
        </div>

        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <span className="bg-amber-400/20 text-amber-300 border border-amber-400/30 px-3 py-1 rounded-full text-[11px] font-bold tracking-widest uppercase">
                🇮🇳 India-Only Live Intelligence
              </span>
              <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-3 py-1 rounded-full text-[11px] font-bold tracking-widest uppercase flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                BookMyShow & Google Events Verified
              </span>
              <span className="bg-white/10 text-slate-200 border border-white/20 px-3 py-1 rounded-full text-[11px] font-bold tracking-widest uppercase">
                Zero-Waste API Cache ({cachedCount}/36 Saved)
              </span>
            </div>
            <h1 className="text-4xl md:text-5xl font-serif font-bold text-white tracking-tight mb-3">
              Live City Events & Festivals
            </h1>
            <p className="text-slate-300 text-base md:text-lg max-w-2xl font-light leading-relaxed">
              Discover real-time local concerts, monument light shows, heritage walks, and festivals across all 36 Indian States & UTs. Each state is queried at most once and permanently cached.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <button
              onClick={() => fetchEvents(selectedState.key, true)}
              disabled={loading}
              title="Forces live SerpAPI query (uses 1 credit)"
              className="bg-white/10 hover:bg-white/20 border border-white/20 text-white text-xs font-bold uppercase tracking-wider px-4 py-3 rounded-2xl transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {loading ? 'Refreshing...' : 'Live Sync'}
            </button>
            
            {onOpenRomeBuddy && (
              <button
                onClick={onOpenRomeBuddy}
                className="bg-amber-400 hover:bg-amber-300 text-slate-950 text-xs font-bold uppercase tracking-wider px-5 py-3 rounded-2xl shadow-lg transition-all flex items-center justify-center gap-2"
              >
                <span>Ask Rome Buddy</span>
                <span className="text-base">&rarr;</span>
              </button>
            )}
          </div>
        </div>

        {/* State Search Bar with Auto-complete Dropdown & Direct Search Button */}
        <div className="relative z-40 mt-8 pt-6 border-t border-white/10" ref={searchContainerRef}>
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-300 flex-shrink-0">
              <span>📍 Choose State:</span>
            </div>

            {/* Interactive Search / Dropdown Input */}
            <div className="relative flex-1 w-full">
              <div className="relative flex items-center">
                <span className="absolute left-4 text-slate-400 text-sm">🔍</span>
                <input
                  type="text"
                  value={searchQuery !== '' ? searchQuery : `${selectedState?.icon || ''} ${selectedState?.name || ''}`}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setIsDropdownOpen(true);
                  }}
                  onFocus={() => {
                    setIsDropdownOpen(true);
                  }}
                  onClick={() => {
                    setIsDropdownOpen(true);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      if (filteredStates.length > 0) {
                        handleSelectState(filteredStates[0]);
                        fetchEvents(filteredStates[0].key, false);
                      } else {
                        fetchEvents(selectedState.key, false);
                      }
                      setIsDropdownOpen(false);
                    }
                  }}
                  placeholder="Choose from 36 Indian States (e.g. Maharashtra, Goa, Delhi, Kerala...)"
                  className="w-full pl-11 pr-10 py-3.5 bg-white/10 hover:bg-white/15 focus:bg-white text-white focus:text-slate-900 border border-white/20 focus:border-white rounded-2xl text-sm placeholder-slate-400 focus:placeholder-slate-400 focus:outline-none focus:ring-4 focus:ring-amber-400/20 transition-all shadow-inner font-semibold"
                />
                {searchQuery && (
                  <button
                    type="button"
                    onClick={() => {
                      setSearchQuery('');
                      setIsDropdownOpen(true);
                    }}
                    className="absolute right-3.5 text-slate-400 hover:text-white p-1 rounded-full text-xs"
                  >
                    ✕
                  </button>
                )}
              </div>

              {/* Autocomplete Dropdown List - elevated z-[100] with unhindered vertical scrolling */}
              {isDropdownOpen && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-slate-900/98 backdrop-blur-2xl border border-white/20 rounded-2xl shadow-[0_25px_60px_-15px_rgba(0,0,0,0.85)] z-[100] max-h-80 overflow-y-auto divide-y divide-white/10 animate-in fade-in duration-150">
                  <div className="sticky top-0 z-10 p-2.5 bg-slate-950/95 backdrop-blur-md text-[11px] font-bold uppercase tracking-wider text-slate-400 flex justify-between items-center px-4 border-b border-white/10">
                    <span>{filteredStates.length} Indian States & UTs Match</span>
                    <span className="text-amber-400">Click to select & search</span>
                  </div>
                  {filteredStates.length > 0 ? (
                    filteredStates.map((s) => (
                      <button
                        key={s.key}
                        type="button"
                        onClick={() => {
                          handleSelectState(s);
                          fetchEvents(s.key, false);
                        }}
                        className={`w-full px-4 py-3 flex items-center justify-between text-left transition-colors group cursor-pointer ${
                          selectedState.key === s.key ? 'bg-amber-400/20 text-white font-bold' : 'hover:bg-white/10 text-slate-200'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-xl group-hover:scale-110 transition-transform">{s.icon}</span>
                          <div>
                            <span className="text-sm font-semibold text-white block">{s.name}</span>
                            <span className="text-[11px] text-slate-400 font-light">Hub: {s.hub}</span>
                          </div>
                        </div>

                        <div>
                          {s.is_cached ? (
                            <span className="inline-flex items-center gap-1 text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full font-bold">
                              ✓ Saved (0 Credits)
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[10px] bg-sky-500/20 text-sky-300 border border-sky-500/30 px-2 py-0.5 rounded-full font-bold">
                              Live SerpAPI Sync
                            </span>
                          )}
                        </div>
                      </button>
                    ))
                  ) : (
                    <div className="p-4 text-center text-xs text-slate-400">
                      No Indian states found matching "{searchQuery}".
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Direct SEARCH Button */}
            <button
              type="button"
              onClick={() => {
                setIsDropdownOpen(false);
                fetchEvents(selectedState.key, false);
              }}
              disabled={loading}
              className="px-8 py-3.5 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-xs uppercase tracking-wider rounded-2xl shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer active:scale-95 disabled:opacity-50 flex-shrink-0"
            >
              <span>Search</span>
              <span className="text-sm font-bold">&rarr;</span>
            </button>
          </div>
        </div>
      </div>

      {/* Cache & Status bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 px-1">
        <div className="flex flex-wrap items-center gap-2">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-4 py-2 rounded-full text-xs font-bold tracking-wider uppercase transition-all ${
                activeCategory === cat
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3 text-xs text-slate-500 font-medium">
          {isCached ? (
            <span className="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              Cached for Speed & Zero Credits Used
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 bg-blue-50 text-blue-700 px-3 py-1 rounded-full border border-blue-200">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
              Live SerpAPI Google Events Sync (1 Credit Saved)
            </span>
          )}
          {lastUpdated && <span>Updated: {lastUpdated}</span>}
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div className="text-center py-20 bg-white rounded-3xl border border-slate-200 shadow-sm">
          <div className="inline-block animate-spin w-10 h-10 border-4 border-slate-900 border-t-transparent rounded-full mb-4"></div>
          <h3 className="font-serif text-xl font-bold text-slate-800">Querying Live Event Intelligence...</h3>
          <p className="text-slate-500 text-sm mt-1">Connecting to SerpAPI & BookMyShow indexes for {selectedState.name} ({selectedState.hub})...</p>
        </div>
      )}

      {error && !loading && (
        <div className="bg-amber-50 border border-amber-200 text-amber-900 p-4 rounded-2xl mb-6 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => fetchEvents(selectedState.key, false)} className="underline font-bold text-xs">Retry</button>
        </div>
      )}

      {/* Events Grid */}
      {!loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredEvents.map((ev) => (
            <div
              key={ev.id}
              className="bg-white rounded-3xl overflow-hidden border border-slate-200/80 shadow-sm hover:shadow-xl transition-all flex flex-col group"
            >
              {/* Event Image / Thumbnail */}
              <div className="relative h-48 bg-slate-100 overflow-hidden">
                <img
                  src={ev.thumbnail || 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=600&q=80'}
                  alt={ev.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  onError={(e) => {
                    e.target.src = 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=600&q=80';
                  }}
                />
                <div className="absolute top-3 left-3 flex flex-wrap gap-1.5">
                  <span className="bg-slate-900/85 backdrop-blur-md text-white text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full shadow-xs">
                    {ev.category}
                  </span>
                </div>
                <div className="absolute bottom-3 right-3">
                  <span className="bg-emerald-600 text-white font-extrabold text-xs px-3 py-1.5 rounded-full shadow-md flex items-center gap-1">
                    <span>🎟️</span>
                    <span>{ev.price || '₹350'}</span>
                  </span>
                </div>
              </div>

              {/* Event Content */}
              <div className="p-6 flex-1 flex flex-col justify-between">
                <div>
                  <h3 className="font-serif font-bold text-xl text-slate-900 group-hover:text-indigo-900 transition-colors line-clamp-2 mb-2">
                    {ev.title}
                  </h3>

                  <div className="space-y-1.5 mb-4 text-xs text-slate-600">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-400">📍</span>
                      <span className="font-medium truncate">{ev.venue}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-slate-400">🗓️</span>
                      <span className="font-medium text-slate-700">{ev.timing}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-slate-400">🏷️</span>
                      <span className="text-[11px] text-slate-500 font-semibold">{ev.source}</span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-500 font-light line-clamp-2 mb-6">
                    {ev.description}
                  </p>
                </div>

                {/* Actions: Buy Ticket + Direct Arrow Redirection */}
                <div className="pt-4 border-t border-slate-100 flex items-center gap-2">
                  <button
                    onClick={() => handleOpenBooking(ev)}
                    className="flex-1 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold uppercase tracking-wider py-3 rounded-xl transition-all shadow-sm flex items-center justify-center gap-1.5 active:scale-98"
                  >
                    <span>🎟️ Buy Ticket</span>
                    <span>&rarr;</span>
                  </button>

                  {ev.ticket_url && (
                    <a
                      href={ev.ticket_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      title="Open authentic live booking website in a new tab"
                      className="bg-amber-50 hover:bg-amber-100/90 text-amber-950 border border-amber-300/80 text-xs font-bold px-3.5 py-3 rounded-xl transition-all flex items-center gap-1 shadow-xs group"
                    >
                      <span className="hidden sm:inline">Official</span>
                      <span className="font-extrabold text-amber-700 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform">
                        ↗
                      </span>
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Booking Confirmation Modal */}
      {bookingModalEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl max-w-lg w-full p-8 shadow-2xl relative border border-slate-100">
            <button
              onClick={() => setBookingModalEvent(null)}
              className="absolute top-5 right-5 text-slate-400 hover:text-slate-700 p-1 rounded-full hover:bg-slate-100 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            {!confirmedBooking ? (
              <div>
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-indigo-600 mb-2">
                  <span>⚡ Autonomous Agent Tool</span>
                  <span>•</span>
                  <span>Direct Database Reservation</span>
                </div>
                <h2 className="text-2xl font-serif font-bold text-slate-900 mb-1">
                  Reserve Event Passes
                </h2>
                <p className="text-xs text-slate-500 mb-6">
                  {bookingModalEvent.title}
                </p>

                <div className="bg-slate-50 rounded-2xl p-4 border border-slate-100 space-y-3 mb-6 text-sm">
                  <div className="flex justify-between items-center text-xs text-slate-600">
                    <span>Venue:</span>
                    <span className="font-bold text-slate-800">{bookingModalEvent.venue}</span>
                  </div>
                  <div className="flex justify-between items-center text-xs text-slate-600">
                    <span>Timing:</span>
                    <span className="font-bold text-slate-800">{bookingModalEvent.timing}</span>
                  </div>
                  <div className="flex justify-between items-center text-xs text-slate-600">
                    <span>Ticket Price:</span>
                    <span className="font-bold text-slate-800">₹{bookingModalEvent.unit_price || 350} / person</span>
                  </div>
                </div>

                {/* Form fields */}
                <div className="space-y-4 mb-6">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                      Primary Attendee Name
                    </label>
                    <input
                      type="text"
                      value={attendeeName}
                      onChange={(e) => setAttendeeName(e.target.value)}
                      className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                      Number of Tickets
                    </label>
                    <div className="flex items-center gap-4">
                      <button
                        type="button"
                        onClick={() => setTicketCount(Math.max(1, ticketCount - 1))}
                        className="w-10 h-10 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold flex items-center justify-center"
                      >
                        -
                      </button>
                      <span className="font-bold text-lg text-slate-900 w-8 text-center">{ticketCount}</span>
                      <button
                        type="button"
                        onClick={() => setTicketCount(Math.min(10, ticketCount + 1))}
                        className="w-10 h-10 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold flex items-center justify-center"
                      >
                        +
                      </button>
                    </div>
                  </div>
                </div>

                {/* Bill Breakdown */}
                <div className="border-t border-slate-200 pt-4 mb-6 text-xs text-slate-600 space-y-1.5">
                  <div className="flex justify-between">
                    <span>Subtotal ({ticketCount} tickets):</span>
                    <span>₹{(bookingModalEvent.unit_price || 350) * ticketCount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Local Convenience Fee (5%):</span>
                    <span>₹{Math.round((bookingModalEvent.unit_price || 350) * ticketCount * 0.05)}</span>
                  </div>
                  <div className="flex justify-between text-sm font-bold text-slate-900 pt-2 border-t border-slate-100">
                    <span>Total Amount Payable:</span>
                    <span>₹{Math.round((bookingModalEvent.unit_price || 350) * ticketCount * 1.05)}</span>
                  </div>
                </div>

                <button
                  onClick={handleConfirmBooking}
                  disabled={bookingSubmitting}
                  className="w-full bg-slate-900 hover:bg-slate-800 text-white py-4 rounded-xl font-bold text-sm tracking-wide transition-all shadow-md flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {bookingSubmitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Agent Writing to Database...</span>
                    </>
                  ) : (
                    <span>Confirm & Generate Ticket Pass</span>
                  )}
                </button>
              </div>
            ) : (
              /* Success Pass */
              <div className="text-center py-4">
                <div className="w-16 h-16 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
                  ✓
                </div>
                <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold uppercase tracking-widest px-3 py-1 rounded-full">
                  Confirmed & Saved to Database
                </span>
                <h3 className="font-serif text-2xl font-bold text-slate-900 mt-3 mb-1">
                  Ticket Reserved Successfully!
                </h3>
                <p className="text-xs text-slate-500 mb-6 font-mono font-bold">
                  Reference: {confirmedBooking.booking_reference}
                </p>

                <div className="bg-slate-50 border border-dashed border-slate-300 rounded-2xl p-5 text-left text-xs space-y-2 mb-6">
                  <div>
                    <span className="text-slate-400 block uppercase font-bold text-[10px]">Event</span>
                    <span className="font-bold text-slate-800 text-sm">{confirmedBooking.title}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200">
                    <div>
                      <span className="text-slate-400 block uppercase font-bold text-[10px]">Venue</span>
                      <span className="font-medium text-slate-700 truncate">{confirmedBooking.venue}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block uppercase font-bold text-[10px]">Timing</span>
                      <span className="font-medium text-slate-700">{confirmedBooking.timing}</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200">
                    <div>
                      <span className="text-slate-400 block uppercase font-bold text-[10px]">Tickets</span>
                      <span className="font-medium text-slate-700">{confirmedBooking.tickets_count} Pass(es)</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block uppercase font-bold text-[10px]">Total Paid/Due</span>
                      <span className="font-bold text-emerald-700">₹{confirmedBooking.total_amount}</span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      setBookingModalEvent(null);
                      if (onBackToTrips) onBackToTrips();
                    }}
                    className="flex-1 bg-slate-900 text-white py-3.5 rounded-xl font-bold text-xs uppercase tracking-wider hover:bg-slate-800 transition-all"
                  >
                    View in Itinerary
                  </button>
                  <button
                    onClick={() => setBookingModalEvent(null)}
                    className="flex-1 bg-slate-100 text-slate-700 py-3.5 rounded-xl font-bold text-xs uppercase tracking-wider hover:bg-slate-200 transition-all"
                  >
                    Close
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
