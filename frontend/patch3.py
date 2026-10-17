import re

with open('src/App.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "</header>" in line:
        start_idx = i + 1
        break

for i in range(start_idx, len(lines)):
    if 'className="flex-1 w-full relative z-10"' in lines[i]:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    correct_code = """      <main className="max-w-7xl mx-auto px-8 py-16 relative">
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
              <div className="absolute -top-32 -right-32 w-96 h-96 bg-blue-100/40 rounded-full blur-3xl z-0 pointer-events-none"></div>
              <div className="absolute -bottom-32 left-1/2 w-96 h-96 bg-orange-50/40 rounded-full blur-3xl z-0 pointer-events-none"></div>
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
              </div>
              
"""
    new_lines = lines[:start_idx] + [correct_code] + lines[end_idx:]
    with open('src/App.jsx', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Patched successfully")
else:
    print("Could not find start or end index")
