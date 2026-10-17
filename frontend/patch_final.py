import re

with open('src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove the old Right Image Composition (lines 567 to 598 in app_dump)
# We will match from `<div className="hidden md:block w-1/2 relative h-[500px] z-10 translate-x-[30px]">`
# to its closing `</div>` right before `<div className="flex flex-col gap-8">`
pattern1 = re.compile(r'(\s*<div className="hidden md:block w-1/2 relative h-\[500px\] z-10 translate-x-\[30px\]">.*?(?=\s*<div className="flex flex-col gap-8">))', re.DOTALL)
match1 = pattern1.search(content)

if match1:
    print("Found right image composition.")
    
# 2. We need to construct the correct right video container
video_container = """
              {/* Right Video Container */}
              <div className="hidden md:block w-1/2 relative h-[500px] z-10 translate-x-[30px]">
                <div className="absolute inset-0 rounded-[2rem] overflow-hidden shadow-2xl">
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
                </div>
              </div>
"""

# Replace the old right image composition with the new video container
if match1:
    content = content.replace(match1.group(1), video_container + "\n            </div>\n")
    print("Replaced right image composition.")
else:
    print("Could not find right image composition.")

# 3. Remove the misplaced video container at the top of the hero
pattern2 = re.compile(r'\s*<div className="absolute inset-0 overflow-hidden pointer-events-none z-\[1\] rounded-\[2rem\]">\s*<video.*?</video>\s*</div>', re.DOTALL)
content = re.sub(pattern2, '', content)
print("Removed misplaced video container.")

# 4. Remove the extra closing </div> that I added in patch4.py (around line 631)
# It looks like:
#             </div>
#             </div>
#           </>
#         ) : (
content = content.replace(
    "            </div>\n            </div>\n          </>\n        ) : (",
    "            </div>\n          </>\n        ) : ("
)

# 5. Fix the trips list to be inside the left content where it belongs!
# Wait! In my replacement above, I added `\n            </div>\n` after the video container.
# This closes `className="flex flex-col md:flex-row gap-16 items-center mb-24 relative"`.
# Then `<div className="flex flex-col gap-8">` starts.
# Actually, if trips list is below the hero container, it's fine! 
# Wait, if trips list is below the hero container, it needs to be inside the `<>` fragment.
# Which it is!

with open('src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied.")
