import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

frontend_src = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\frontend\src"

# Update App.jsx to include the Voice Button and Import UI
app_jsx_path = f"{frontend_src}/App.jsx"
with open(app_jsx_path, 'r', encoding='utf-8') as f:
    app_jsx = f.read()

voice_component = """
const VoiceButton = () => {
    const [recording, setRecording] = useState(false);
    const [statusText, setStatusText] = useState('Idle');
    const mediaRecorder = React.useRef(null);
    const audioChunks = React.useRef([]);

    const toggleRecording = async () => {
        if (recording) {
            mediaRecorder.current.stop();
            setRecording(false);
            setStatusText('Processing...');
        } else {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
                mediaRecorder.current.ondataavailable = e => { if (e.data.size > 0) audioChunks.current.push(e.data); };
                mediaRecorder.current.onstop = async () => {
                    const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' });
                    audioChunks.current = [];
                    setStatusText('Understanding...');
                    
                    const fd = new FormData();
                    fd.append('file', audioBlob, 'recording.webm');
                    
                    try {
                        const token = (await supabase?.auth.getSession())?.data?.session?.access_token;
                        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
                        const res = await fetch('http://localhost:8000/api/voice/transcribe', {
                            method: 'POST',
                            headers,
                            body: fd
                        });
                        const data = await res.json();
                        if (data.success) {
                            setStatusText(`You: "${data.text}"`);
                            
                            // Send to intent endpoint
                            const iRes = await fetch('http://localhost:8000/api/voice/intent', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json', ...headers },
                                body: JSON.stringify({text: data.text})
                            });
                            const intentData = await iRes.json();
                            setStatusText(`AI: "Got it. You're reporting: ${intentData.intent}"`);
                        } else {
                            setStatusText(`Error: ${data.error}`);
                        }
                    } catch(e) {
                        setStatusText('Network error');
                    }
                };
                mediaRecorder.current.start();
                setRecording(true);
                setStatusText('🔴 Listening...');
            } catch(e) {
                setStatusText('Microphone permission denied.');
            }
        }
    };

    return (
        <div className="mt-4 p-4 bg-gray-100 rounded text-center border">
            <p className="text-sm text-gray-700 mb-2 font-semibold h-10">{statusText}</p>
            <button 
                onClick={toggleRecording} 
                className={`p-3 rounded-full text-white ${recording ? 'bg-red-500 animate-pulse' : 'bg-blue-600 hover:bg-blue-700'}`}
                title="Ask your travel assistant"
            >
                🎤
            </button>
        </div>
    );
};
"""

import_ui = """
  const [importing, setImporting] = useState(false);
  const handleImport = async (type) => {
      setImporting(true);
      const token = (await supabase?.auth.getSession())?.data?.session?.access_token;
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      try {
          if (type === 'text') {
              const text = prompt("Paste your itinerary text here:");
              if (!text) { setImporting(false); return; }
              const res = await fetch('http://localhost:8000/api/import/text', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json', ...headers },
                  body: JSON.stringify({ text })
              });
              alert("Import successful! (Check console)");
              console.log(await res.json());
          }
      } catch(e) {
          alert("Import failed.");
      }
      setImporting(false);
  };
"""

app_jsx = app_jsx.replace("import React, { useEffect, useState } from 'react';", "import React, { useEffect, useState } from 'react';\n" + voice_component)

app_jsx = app_jsx.replace("const renderTrips = () => (\n", import_ui + "const renderTrips = () => (\n")

app_jsx = app_jsx.replace(
    '<h1 className="text-3xl font-bold">My Trips</h1>',
    '<h1 className="text-3xl font-bold">My Trips</h1>\n            <div className="flex gap-2"><button onClick={() => handleImport(\'text\')} disabled={importing} className="bg-blue-600 text-white px-3 py-1 text-sm rounded">Import Text</button></div>'
)

app_jsx = app_jsx.replace(
    '</button>\n              )}',
    '</button>\n              )}\n              <VoiceButton />'
)

write_file(app_jsx_path, app_jsx)
