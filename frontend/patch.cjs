const fs = require('fs');
let lines = fs.readFileSync('src/App.jsx', 'utf8').split('\n');
let newLines = [];

for (let i = 0; i < lines.length; i++) {
  if (i === 451) {
    newLines.push('            <div ');
    newLines.push('              className="flex flex-col md:flex-row gap-16 items-center mb-24 relative"');
    newLines.push('              onMouseEnter={() => {');
    newLines.push('                const playPromise = videoRef.current?.play();');
    newLines.push('                if (playPromise !== undefined) {');
    newLines.push('                  playPromise.catch(() => {});');
    newLines.push('                }');
    newLines.push('              }}');
    newLines.push('              onMouseLeave={() => {');
    newLines.push('                videoRef.current?.pause();');
    newLines.push('              }}');
    newLines.push('            >');
    newLines.push('              <div className="absolute -top-32 -right-32 w-96 h-96 bg-blue-100/40 rounded-full blur-3xl z-0 pointer-events-none"></div>');
    newLines.push('              <div className="absolute -bottom-32 left-1/2 w-96 h-96 bg-orange-50/40 rounded-full blur-3xl z-0 pointer-events-none"></div>');
    newLines.push('              <div className="absolute inset-0 overflow-hidden pointer-events-none z-[1] rounded-[2rem]">');
    newLines.push('                <video ');
    newLines.push('                  ref={videoRef}');
    newLines.push('                  src="/Untitled_Scene_09-27_18_15_21_20260927234837.mp4"');
    newLines.push('                  autoPlay={false}');
    newLines.push('                  muted');
    newLines.push('                  playsInline');
    newLines.push('                  loop');
    newLines.push('                  preload="metadata"');
    newLines.push('                  className="w-full h-full object-cover"');
    newLines.push('                />');
    newLines.push('              </div>');
  } else if (i === 452 || i === 453) {
    // Skip original blur divs
    continue;
  } else {
    newLines.push(lines[i]);
  }
}

fs.writeFileSync('src/App.jsx', newLines.join('\n'));
