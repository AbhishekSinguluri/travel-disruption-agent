const fs = require('fs');
let content = fs.readFileSync('src/App.jsx', 'utf8');
content = content.replace(
  `        const res = await fetch('http://localhost:8000/api/bookings/extract', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ type: 'text', text: importText })
        });`,
  `        const fd = new FormData();
        fd.append('text', importText);
        const res = await fetch('http://localhost:8000/api/bookings/extract', {
          method: 'POST',
          body: fd
        });`
);
fs.writeFileSync('src/App.jsx', content);
console.log("Patched successfully");
