import re

with open('src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace the Right Video Container (which was at lines 567-580) with the Right Image Composition
video_container_pattern = re.compile(r'\s*\{\/\* Right Video Container \*\/\}.*?</div>\s*</div>', re.DOTALL)

right_image_composition = """
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
              </div>"""

content = re.sub(video_container_pattern, right_image_composition, content)

# 2. Add the video container back to the top of the hero area
video_top_container = """
              <div className="absolute inset-0 overflow-hidden pointer-events-none z-[1] rounded-[2rem]">
                <video 
                  ref={videoRef}
                  src="/Untitled_Scene_09-27_18_15_21_20260927234837.mp4"
                  autoPlay={false}
                  muted
                  playsInline
                  loop
                  preload="metadata"
                  className="w-full h-full object-cover mix-blend-multiply"
                />
              </div>"""

# Find the glows and replace them, appending the video container
glows_pattern = re.compile(r'<div className="absolute -top-32 -right-32 w-96 h-96 bg-blue-100/40 rounded-full blur-3xl z-0 pointer-events-none"></div>\s*<div className="absolute -bottom-32 left-1/2 w-96 h-96 bg-orange-50/40 rounded-full blur-3xl z-0 pointer-events-none"></div>')

new_glows = """<div className="absolute -top-32 -right-32 w-96 h-96 bg-blue-300/60 rounded-full blur-3xl z-0 pointer-events-none"></div>
              <div className="absolute -bottom-32 left-1/2 w-96 h-96 bg-orange-300/60 rounded-full blur-3xl z-0 pointer-events-none"></div>""" + video_top_container

content = re.sub(glows_pattern, new_glows, content)

with open('src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch 8 applied.")
