import re

with open('src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

voice_button_replacement = """  return (
    <div className="fixed bottom-0 left-0 right-0 p-4 bg-[#FAF9F6] border-t border-slate-200 shadow-2xl flex flex-col items-center z-50 md:sticky md:bottom-0 md:bg-transparent md:shadow-none md:border-none md:p-0">
      <p className="text-xs text-slate-500 mb-2 font-bold uppercase tracking-widest text-center">{statusText}</p>
      <button
        onClick={toggleRecording}
        aria-label="Voice Command"
        className={`w-16 h-16 text-2xl rounded-full text-white shadow-xl transition-all flex items-center justify-center ${recording ? 'bg-orange-500 animate-pulse scale-110' : 'bg-slate-900 hover:bg-slate-800 hover:scale-105'}`}
      >
        🎤
      </button>
    </div>
  );
"""
content = re.sub(
    r'  return \(\n    <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t shadow-2xl flex flex-col items-center z-50 md:sticky md:bottom-0 md:bg-transparent md:shadow-none md:border-none">\n      <p className="text-sm text-gray-700 mb-2 font-semibold text-center">\{statusText\}</p>\n      <button\n        onClick=\{toggleRecording\}\n        aria-label="Voice Command"\n        className=\{`w-20 h-20 text-3xl rounded-full text-white shadow-lg transition-all \$\{recording \? \'bg-red-500 animate-pulse scale-110\' : \'bg-blue-600 hover:bg-blue-700 hover:scale-105\'\}`\}\n      >\n        🎤\n      </button>\n    </div>\n  \);',
    voice_button_replacement,
    content
)

render_trips_replacement = """  const renderTrips = () => (
    <div className="min-h-screen relative font-sans bg-[#F9F8F6]"> {/* Warm cream background */}
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
          <button onClick={() => { logout(); setCurrentView('LOGIN'); }} className="text-sm font-medium hover:text-stone-500 transition-colors uppercase tracking-widest">Logout</button>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-8 py-12 relative z-10">
        {!showImportModal ? (
          <>
            <div className="mb-16 max-w-2xl">
              <span className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-4 block">YOUR JOURNEYS</span>
              <h1 className="text-5xl md:text-6xl font-serif text-slate-900 mb-6 leading-tight">Where are you going next?</h1>
              <p className="text-xl text-slate-600 font-light leading-relaxed mb-8">Your trips, ready for whatever changes along the way.</p>
              
              <div className="flex gap-4">
                <button onClick={() => handleImport('text')} disabled={importing} className="bg-slate-900 text-white px-6 py-3 rounded-full text-sm font-medium hover:bg-slate-800 transition-all shadow-md">Paste Text</button>
                <button onClick={() => handleImport('pdf')} disabled={importing} className="bg-white border border-slate-200 text-slate-800 px-6 py-3 rounded-full text-sm font-medium hover:bg-slate-50 transition-all shadow-sm">Upload PDF</button>
                <button onClick={() => handleImport('image')} disabled={importing} className="bg-white border border-slate-200 text-slate-800 px-6 py-3 rounded-full text-sm font-medium hover:bg-slate-50 transition-all shadow-sm">Upload Image</button>
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
              {!pendingTrip ? (
                <>
                  <button onClick={() => { setShowImportModal(false); setImportStatus(""); setImportText(""); }} className="mb-12 text-sm font-bold tracking-widest text-slate-400 hover:text-slate-800 uppercase transition-colors">&larr; Back</button>
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-4 block">IMPORT YOUR JOURNEY</span>
                  <h2 className="text-4xl md:text-5xl font-serif text-slate-900 mb-6 leading-tight">Bring your journey into Roam.</h2>
                  <p className="text-lg text-slate-600 mb-8 font-light leading-relaxed">Paste an itinerary or upload the plan you already have.</p>
                  
                  <textarea 
                    className="w-full h-64 bg-white border border-slate-200 shadow-inner rounded-2xl p-6 font-serif text-lg mb-6 focus:ring-2 focus:ring-slate-300 focus:outline-none resize-none transition-shadow"
                    placeholder="Paste your text itinerary here..."
                    value={importText}
                    onChange={(e) => setImportText(e.target.value)}
                    disabled={importing}
                  ></textarea>
                  
                  <div className="flex items-center gap-4">
                    {importStatus.includes("couldn't") ? (
                      <button onClick={handleImportTextSubmit} disabled={importing || !importText} className="px-8 py-4 bg-slate-900 text-white rounded-full hover:bg-slate-800 shadow-lg text-sm font-bold uppercase tracking-widest transition-all">Try again</button>
                    ) : (
                      <button onClick={handleImportTextSubmit} disabled={importing || !importText} className="px-8 py-4 bg-slate-900 text-white rounded-full hover:bg-slate-800 shadow-lg text-sm font-bold uppercase tracking-widest transition-all">Create itinerary</button>
                    )}
                    {importStatus && <p className={`text-sm font-medium ${importStatus.includes("couldn't") ? 'text-red-500' : 'text-slate-500'}`}>{importStatus}</p>}
                  </div>
                </>
              ) : (
                <>
                  <h2 className="text-4xl font-serif text-slate-900 mb-4 leading-tight">Your journey is taking shape.</h2>
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
      </div>
    </div>
  );
"""

# Extract the old renderTrips and replace it
import re
render_trips_pattern = re.compile(r'  const renderTrips = \(\) => \((.*?)\n  \);', re.DOTALL)
content = render_trips_pattern.sub(render_trips_replacement.strip(), content, count=1)


main_return_replacement = """  return (
    <div className="min-h-screen bg-[#F9F8F6] font-sans pb-24">
      <header className="p-8 flex justify-between items-center text-slate-800 max-w-7xl mx-auto">
        <button onClick={() => setCurrentView('TRIPS')} className="text-sm font-bold uppercase tracking-widest text-slate-400 hover:text-slate-800 transition-colors">&larr; Back to Trips</button>
        <div className="font-serif font-bold text-xl tracking-widest opacity-50">ROAM</div>
      </header>

      <div className="max-w-7xl mx-auto px-8">
        
        {/* HERO SECTION */}
        <div className="flex flex-col md:flex-row gap-16 items-center mb-16">
          <div className="flex-1 w-full">
            <span className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-4 block">YOUR JOURNEY</span>
            <h1 className="text-5xl md:text-7xl font-serif text-slate-900 mb-6 leading-tight">{trip.destination}</h1>
            <p className="text-xl text-slate-600 mb-8 font-light leading-relaxed">{trip.start_date} &mdash; {trip.end_date}</p>
            <div className="flex gap-4 items-center flex-wrap">
              <span className="bg-emerald-100 text-emerald-800 px-4 py-2 rounded-full font-bold text-xs uppercase tracking-wider">Active Trip</span>
              <button onClick={handleValidate} className="px-6 py-2 border border-slate-300 text-slate-600 rounded-full hover:bg-slate-100 text-sm font-bold uppercase tracking-widest transition-all">
                {isValidating ? 'Validating...' : 'Validate'}
              </button>
              <div className="text-xs px-3 py-2 bg-slate-100 text-slate-600 rounded-full uppercase tracking-widest font-bold">
                📍 Location:
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
                <button className="px-4 py-2 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 rounded-full text-xs font-medium transition-colors shadow-sm" onClick={() => fetch(`http://localhost:8000/api/monitor/${trip.id}/simulate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event: 'delay', value: 18 }) })}>+15 min Delay</button>
                <button className="px-4 py-2 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 rounded-full text-xs font-medium transition-colors shadow-sm" onClick={() => fetch(`http://localhost:8000/api/monitor/${trip.id}/simulate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event: 'weather' }) })}>Weather Disruption</button>
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
              <div className="text-emerald-600 font-medium">✓ All good! Your itinerary is physically possible.</div>
            ) : (
              <div className="text-orange-600 font-medium mb-4">⚠ {validationResult.issues.length} potential issues found</div>
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
                <MapComponent
                  stops={stops}
                  affectedStopId={disruption?.affected_stop_id}
                  candidates={candidates}
                  currentLocation={currentLocation}
                />
              </div>
            </div>

            {/* ITINERARY TIMELINE */}
            <div>
              <h2 className="text-3xl font-serif font-bold text-slate-800 mb-8">Itinerary</h2>
              <div className="pl-6 border-l border-slate-300 space-y-12">
                {stops.map((stop) => (
                  <div key={stop.id} className="relative">
                    <div className={`absolute -left-[29px] w-4 h-4 rounded-full border-[3px] border-[#F9F8F6] ${stop.status === 'REPLACED' ? 'bg-emerald-500' : 'bg-slate-800'}`}></div>
                    <div className="pl-8">
                      <div className="flex items-baseline gap-4 mb-2">
                        <span className="font-bold text-slate-800 w-16">{stop.start_time}</span>
                        <h3 className={`text-2xl font-serif ${stop.status === 'REPLACED' ? 'text-emerald-700' : 'text-slate-900'}`}>{stop.title}</h3>
                      </div>
                      <div className="ml-20">
                        <span className="text-sm text-slate-500 font-medium uppercase tracking-widest">{stop.duration_minutes} MIN &bull; {stop.category}</span>
                        {stop.location_name && <p className="text-slate-600 mt-2">{stop.location_name}</p>}
                        {stop.notes && <p className="text-slate-500 mt-2 italic border-l-2 border-slate-200 pl-4">{stop.notes}</p>}
                        {stop.status === 'REPLACED' && <span className="inline-block mt-3 bg-emerald-50 text-emerald-700 text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider">Replaced</span>}
                        {stop.id === impact?.affected_stop_id && <span className="inline-block mt-3 bg-orange-50 text-orange-700 text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider border border-orange-200">Disrupted</span>}
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
                  {liveStatus.includes('behind') && (
                    <div className="mt-6 flex gap-3">
                      <button className="flex-1 py-2 bg-slate-100 text-slate-700 rounded-full text-xs font-bold uppercase tracking-wider hover:bg-slate-200 transition-colors">I'm okay</button>
                      <button className="flex-1 py-2 bg-slate-900 text-white rounded-full text-xs font-bold uppercase tracking-wider hover:bg-slate-800 transition-colors" onClick={() => simulateDisruption('stop-4')}>I'm stuck</button>
                    </div>
                  )}
                </div>
              )}

              {impact && (
                <motion.div initial={{opacity:0, scale:0.95}} animate={{opacity:1, scale:1}} className="mt-8 p-6 bg-[#FAF9F6] rounded-2xl border border-orange-100 shadow-inner">
                  <h3 className="font-serif font-bold text-lg text-slate-900 mb-2">Disruption Detected</h3>
                  <p className="text-sm text-slate-700 leading-relaxed">{impact.message}</p>

                  {!candidates.length && (
                    <button
                      onClick={() => submitPreferences(['Indoor'])}
                      className="mt-6 w-full py-3 bg-slate-900 text-white rounded-full text-xs font-bold uppercase tracking-widest hover:bg-slate-800 transition-all shadow-md"
                    >
                      Find Alternatives
                    </button>
                  )}
                  <div className="mt-4 flex justify-center">
                    <VoiceButton />
                  </div>
                </motion.div>
              )}

              {candidates.length > 0 && (
                <div className="mt-8">
                  <h3 className="font-serif font-bold text-lg text-slate-900 mb-4">Suggested Alternatives</h3>
                  <div className="space-y-4">
                    {candidates.map(cand => (
                      <motion.div initial={{opacity:0, y:10}} animate={{opacity:1, y:0}} key={cand.id} className="p-4 border border-slate-200 bg-white rounded-xl hover:border-slate-400 hover:shadow-md cursor-pointer transition-all group" onClick={() => selectCandidate(cand.id)}>
                        <h4 className="font-bold text-slate-800 group-hover:text-slate-900">{cand.name}</h4>
                        <p className="text-xs text-slate-500 mt-1 mb-2 font-medium tracking-wide">{cand.category}</p>
                        <p className="text-sm text-slate-600 leading-relaxed">{cand.why_recommended}</p>
                        <div className="mt-3 text-right">
                          <span className="text-xs font-bold uppercase tracking-widest text-blue-600 group-hover:text-blue-800">Select &rarr;</span>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
"""

main_return_pattern = re.compile(r'  return \(\n    <div className="min-h-screen relative font-sans">.*?  \);\n}', re.DOTALL)
content = main_return_pattern.sub(main_return_replacement.strip() + "\n}", content, count=1)

with open('src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated App.jsx")
