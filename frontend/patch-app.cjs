const fs = require('fs');
let lines = fs.readFileSync('src/App.jsx', 'utf8').split('\n');

// 1. Add fileInputRef and handleFileChange at the top of App
let appStart = lines.findIndex(l => l.includes('export default function App() {'));
let insertHooksIndex = appStart + 17; // after const [importing, setImporting] = useState(false);

const hooksCode = `
  const fileInputRef = React.useRef(null);
  const [importFileType, setImportFileType] = React.useState(null);

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setImporting(true);
    setImportError(null);
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
        const res = await fetch(\`http://localhost:8000/api/import/\${importFileType}\`, {
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
      setImportError(err.message || 'Failed to process import');
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = null;
    }
  };
`;

lines.splice(insertHooksIndex, 0, hooksCode);

// 2. Rewrite handleImport
let hiStart = lines.findIndex(l => l.includes('const handleImport = async (type) => {'));
let hiEnd = lines.findIndex((l, i) => i > hiStart && l.trim() === '};');

const newHandleImport = `  const handleImport = (type) => {
    setImportFileType(type);
    if (fileInputRef.current) {
      fileInputRef.current.value = null;
      fileInputRef.current.click();
    }
  };`;

lines.splice(hiStart, hiEnd - hiStart + 1, newHandleImport);

// 3. Update the buttons rendering and add the hidden file input
let btnIdx = lines.findIndex(l => l.includes("handleImport('pdf')"));
// We will replace the buttons with conditional rendering
const newButtons = `                      <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept={importFileType === 'pdf' ? '.pdf' : 'image/*'} />
                      <button onClick={() => setShowImportModal(true)} disabled={importing} className="bg-slate-900 text-white px-6 py-3 rounded-full text-sm font-medium hover:bg-slate-800 transition-all shadow-md">Paste Text</button>
                      
                      {monitoringMode === 'BOOKINGS' && (
                        <button onClick={() => handleImport('pdf')} disabled={importing} className="bg-[#F9F8F6] border border-slate-200 text-slate-800 px-6 py-3 rounded-full text-sm font-medium hover:bg-white transition-all shadow-sm">Upload PDF</button>
                      )}
                      
                      <button onClick={() => handleImport('image')} disabled={importing} className="bg-[#F9F8F6] border border-slate-200 text-slate-800 px-6 py-3 rounded-full text-sm font-medium hover:bg-white transition-all shadow-sm">Upload Image</button>

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
                      )}`;

lines.splice(btnIdx - 1, 3, newButtons); // replace lines 517, 518, 519 (or where they are now)

fs.writeFileSync('src/App.jsx', lines.join('\n'));
