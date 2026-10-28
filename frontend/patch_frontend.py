import sys

with open("src/App.jsx", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace VoiceButton block
old_voice_snippet = """                      {monitoringMode === 'TRIP' && (
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
                  )}"""

new_voice_snippet = """                    {/* Voice Option for MONITOR TRIP (Requirement 1 & 2) */}
                    {monitoringMode === 'TRIP' && (
                      <button 
                        type="button"
                        onClick={() => setShowVoiceModal(true)} 
                        disabled={importing} 
                        className="bg-[#F9F8F6] border border-slate-200 text-slate-800 px-6 py-3 rounded-full text-sm font-medium hover:bg-white transition-all shadow-sm flex items-center gap-2"
                      >
                        <svg className="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
                        Voice
                      </button>
                    )}
                  </div>"""

if old_voice_snippet in content:
    content = content.replace(old_voice_snippet, new_voice_snippet, 1)
    print("VoiceButton replaced successfully")
else:
    print("ERROR: old_voice_snippet not found")
    sys.exit(1)

# 2. Remove landing page saved trips listing
old_landing_trips = """            <div className="flex flex-col gap-8">
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
            </div>"""

if old_landing_trips in content:
    content = content.replace(old_landing_trips, "            {/* Landing page saved trips removed per Requirement 4.4 */}", 1)
    print("Landing page trips list removed successfully")
else:
    print("ERROR: old_landing_trips not found")
    sys.exit(1)

# 3. Add VoiceItineraryModal to renderTrips end
old_render_trips_end = """        )}
      </main>
    </div>
  );"""

new_render_trips_end = """        )}
      </main>
      <VoiceItineraryModal 
        isOpen={showVoiceModal} 
        onClose={() => setShowVoiceModal(false)} 
        onSubmitItinerary={handleVoiceItinerarySubmit} 
      />
    </div>
  );"""

if old_render_trips_end in content:
    content = content.replace(old_render_trips_end, new_render_trips_end, 1)
    print("VoiceItineraryModal added to renderTrips")
else:
    print("ERROR: old_render_trips_end not found")
    sys.exit(1)

# 4. Define renderExploreTrips and renderExploreBookings before renderAlertCenter
explore_pages_code = '''  const renderExploreTrips = () => (
    <div className="min-h-screen bg-[#E5DED2] font-sans pb-24">
      {/* Header */}
      <header className="p-8 flex justify-between items-center text-slate-800 max-w-7xl mx-auto">
        <div className="flex items-center gap-8">
          <div className="font-serif font-bold text-2xl tracking-widest cursor-pointer" onClick={() => setCurrentView('TRIPS')}>ROAM</div>
          <nav className="hidden md:flex gap-6 text-sm font-medium tracking-wide items-center">
            <span className="cursor-pointer text-slate-500 hover:text-slate-800" onClick={() => setCurrentView('TRIPS')}>Trip</span>
            
            <div 
              className="relative inline-block"
              ref={exploreRef}
              onMouseEnter={() => setExploreMenuOpen(true)}
              onMouseLeave={() => setExploreMenuOpen(false)}
            >
              <button 
                type="button"
                onClick={() => setExploreMenuOpen(!exploreMenuOpen)}
                className="cursor-pointer border-b border-slate-800 pb-1 font-semibold text-slate-900 flex items-center gap-1 focus:outline-none"
                aria-haspopup="true"
                aria-expanded={exploreMenuOpen}
              >
                <span>Explore</span>
                <svg className="w-3.5 h-3.5 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
              </button>

              {exploreMenuOpen && (
                <div className="absolute left-0 mt-2 w-44 bg-white border border-slate-200 rounded-2xl shadow-xl py-2 z-50">
                  <button type="button" onClick={() => { setCurrentView('EXPLORE_TRIPS'); setExploreMenuOpen(false); }} className="w-full text-left px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-slate-900 bg-slate-50 flex items-center justify-between">
                    <span>Trips</span>
                    <span className="text-[10px] text-slate-400 font-normal">({trips.length})</span>
                  </button>
                  <button type="button" onClick={() => { setCurrentView('EXPLORE_BOOKINGS'); setExploreMenuOpen(false); }} className="w-full text-left px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-slate-700 hover:bg-slate-50 flex items-center justify-between">
                    <span>Bookings</span>
                    <span className="text-[10px] text-slate-400 font-normal">({savedBookings.length})</span>
                  </button>
                </div>
              )}
            </div>

            <span className="cursor-pointer text-slate-500 hover:text-slate-800" onClick={() => trip && setCurrentView('DASHBOARD')}>AI Companion</span>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <button onClick={() => setCurrentView('TRIPS')} className="text-sm font-bold uppercase tracking-widest text-slate-400 hover:text-slate-800 transition-colors">&larr; Back to Home</button>
          <button onClick={() => { logout(); setCurrentView('LOGIN'); }} className="text-sm font-medium hover:text-stone-500 transition-colors uppercase tracking-widest">Logout</button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-8">
        <div className="flex justify-between items-end mb-12">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2 block">EXPLORE / TRIPS</span>
            <h1 className="text-4xl md:text-5xl font-serif text-slate-900 leading-tight">Your Saved Itineraries</h1>
            <p className="text-slate-600 mt-2">Manage and view all your planned journeys.</p>
          </div>
          <button 
            type="button"
            onClick={() => { setMonitoringMode('TRIP'); setCurrentView('TRIPS'); }} 
            className="bg-slate-900 text-white px-6 py-3 rounded-full text-xs font-bold uppercase tracking-widest hover:bg-slate-800 transition-all shadow-md"
          >
            + Create New Trip
          </button>
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {trips.map(t => (
              <div 
                key={t.id} 
                className="group bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden hover:shadow-xl transition-all duration-300 flex flex-col justify-between"
              >
                <div className="h-44 bg-slate-100 overflow-hidden relative">
                  <img src="/roam_image_assets/destinations/destination_art_gallery.png" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" alt="Trip destination" />
                  <div className="absolute top-4 left-4">
                    <span className="bg-emerald-500/90 text-white backdrop-blur-sm text-[10px] uppercase font-bold tracking-wider px-3 py-1 rounded-full shadow-sm">Active</span>
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
            ))}
          </div>
        )}
      </main>
    </div>
  );

  const renderExploreBookings = () => (
    <div className="min-h-screen bg-[#E5DED2] font-sans pb-24">
      {/* Header */}
      <header className="p-8 flex justify-between items-center text-slate-800 max-w-7xl mx-auto">
        <div className="flex items-center gap-8">
          <div className="font-serif font-bold text-2xl tracking-widest cursor-pointer" onClick={() => setCurrentView('TRIPS')}>ROAM</div>
          <nav className="hidden md:flex gap-6 text-sm font-medium tracking-wide items-center">
            <span className="cursor-pointer text-slate-500 hover:text-slate-800" onClick={() => setCurrentView('TRIPS')}>Trip</span>
            
            <div 
              className="relative inline-block"
              ref={exploreRef}
              onMouseEnter={() => setExploreMenuOpen(true)}
              onMouseLeave={() => setExploreMenuOpen(false)}
            >
              <button 
                type="button"
                onClick={() => setExploreMenuOpen(!exploreMenuOpen)}
                className="cursor-pointer border-b border-slate-800 pb-1 font-semibold text-slate-900 flex items-center gap-1 focus:outline-none"
                aria-haspopup="true"
                aria-expanded={exploreMenuOpen}
              >
                <span>Explore</span>
                <svg className="w-3.5 h-3.5 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
              </button>

              {exploreMenuOpen && (
                <div className="absolute left-0 mt-2 w-44 bg-white border border-slate-200 rounded-2xl shadow-xl py-2 z-50">
                  <button type="button" onClick={() => { setCurrentView('EXPLORE_TRIPS'); setExploreMenuOpen(false); }} className="w-full text-left px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-slate-700 hover:bg-slate-50 flex items-center justify-between">
                    <span>Trips</span>
                    <span className="text-[10px] text-slate-400 font-normal">({trips.length})</span>
                  </button>
                  <button type="button" onClick={() => { setCurrentView('EXPLORE_BOOKINGS'); setExploreMenuOpen(false); }} className="w-full text-left px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-slate-900 bg-slate-50 flex items-center justify-between">
                    <span>Bookings</span>
                    <span className="text-[10px] text-slate-400 font-normal">({savedBookings.length})</span>
                  </button>
                </div>
              )}
            </div>

            <span className="cursor-pointer text-slate-500 hover:text-slate-800" onClick={() => trip && setCurrentView('DASHBOARD')}>AI Companion</span>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <button onClick={() => setCurrentView('TRIPS')} className="text-sm font-bold uppercase tracking-widest text-slate-400 hover:text-slate-800 transition-colors">&larr; Back to Home</button>
          <button onClick={() => { logout(); setCurrentView('LOGIN'); }} className="text-sm font-medium hover:text-stone-500 transition-colors uppercase tracking-widest">Logout</button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-8">
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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

'''

if "const renderAlertCenter = () => (" in content:
    content = content.replace("  const renderAlertCenter = () => (", explore_pages_code + "  const renderAlertCenter = () => (", 1)
    print("renderExploreTrips and renderExploreBookings added")
else:
    print("ERROR: renderAlertCenter not found")
    sys.exit(1)

# 5. Update view dispatch
old_view_dispatch = """  if (currentView === 'LOGIN') return renderLogin();
  if (currentView === 'ALERTS') return renderAlertCenter();
  if (currentView === 'TRIPS') return renderTrips();"""

new_view_dispatch = """  if (currentView === 'LOGIN') return renderLogin();
  if (currentView === 'ALERTS') return renderAlertCenter();
  if (currentView === 'EXPLORE_TRIPS') return renderExploreTrips();
  if (currentView === 'EXPLORE_BOOKINGS') return renderExploreBookings();
  if (currentView === 'TRIPS') return renderTrips();"""

if old_view_dispatch in content:
    content = content.replace(old_view_dispatch, new_view_dispatch, 1)
    print("View dispatch updated")
else:
    print("ERROR: old_view_dispatch not found")
    sys.exit(1)

with open("src/App.jsx", "w", encoding="utf-8") as f:
    f.write(content)

print("ALL APP.JSX PATCHES APPLIED SUCCESSFULLY!")
