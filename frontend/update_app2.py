import re

with open('src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the hero section in renderTrips (when !showImportModal)
old_hero = """            <div className="mb-16 max-w-2xl">
              <span className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-4 block">YOUR JOURNEYS</span>
              <h1 className="text-5xl md:text-6xl font-serif text-slate-900 mb-6 leading-tight">Where are you going next?</h1>
              <p className="text-xl text-slate-600 font-light leading-relaxed mb-8">Your trips, ready for whatever changes along the way.</p>
              
              <div className="flex gap-4">
                <button onClick={() => handleImport('text')} disabled={importing} className="bg-slate-900 text-white px-6 py-3 rounded-full text-sm font-medium hover:bg-slate-800 transition-all shadow-md">Paste Text</button>
                <button onClick={() => handleImport('pdf')} disabled={importing} className="bg-white border border-slate-200 text-slate-800 px-6 py-3 rounded-full text-sm font-medium hover:bg-slate-50 transition-all shadow-sm">Upload PDF</button>
                <button onClick={() => handleImport('image')} disabled={importing} className="bg-white border border-slate-200 text-slate-800 px-6 py-3 rounded-full text-sm font-medium hover:bg-slate-50 transition-all shadow-sm">Upload Image</button>
              </div>
            </div>"""

new_hero = """            <div className="flex flex-col md:flex-row gap-16 items-center mb-24 relative">
              <div className="absolute -top-32 -right-32 w-96 h-96 bg-blue-100/40 rounded-full blur-3xl z-0 pointer-events-none"></div>
              <div className="absolute -bottom-32 left-1/2 w-96 h-96 bg-orange-50/40 rounded-full blur-3xl z-0 pointer-events-none"></div>
              
              <div className="flex-1 w-full relative z-10">
                <span className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-4 block">YOUR JOURNEYS</span>
                <h1 className="text-5xl md:text-6xl font-serif text-slate-900 mb-6 leading-tight">Where are you going next?</h1>
                <p className="text-xl text-slate-600 font-light leading-relaxed mb-8">Your trips, ready for whatever changes along the way.</p>
                
                <div className="flex gap-4">
                  <button onClick={() => handleImport('text')} disabled={importing} className="bg-slate-900 text-white px-6 py-3 rounded-full text-sm font-medium hover:bg-slate-800 transition-all shadow-md">Paste Text</button>
                  <button onClick={() => handleImport('pdf')} disabled={importing} className="bg-[#F9F8F6] border border-slate-200 text-slate-800 px-6 py-3 rounded-full text-sm font-medium hover:bg-white transition-all shadow-sm">Upload PDF</button>
                  <button onClick={() => handleImport('image')} disabled={importing} className="bg-[#F9F8F6] border border-slate-200 text-slate-800 px-6 py-3 rounded-full text-sm font-medium hover:bg-white transition-all shadow-sm">Upload Image</button>
                </div>
              </div>
              
              <div className="hidden md:block w-1/2 relative h-[500px] z-10">
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
            </div>"""

content = content.replace(old_hero, new_hero)

with open('src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated App.jsx with new hero layout.")
