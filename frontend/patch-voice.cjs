const fs = require('fs');
let lines = fs.readFileSync('src/App.jsx', 'utf8').split('\n');

let start = lines.findIndex(l => l.includes('const VoiceButton = () => {'));
let end = lines.findIndex((l, i) => i > start && l.trim() === '};');

const newVoiceButton = `const VoiceButton = ({ onTranscribed, disabled }) => {
  const [recording, setRecording] = React.useState(false);
  const [statusText, setStatusText] = React.useState('Voice');
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
          setStatusText('Structuring...');

          const fd = new FormData();
          fd.append('file', audioBlob, 'recording.webm');

          try {
            const res = await fetch('http://localhost:8000/api/voice/transcribe', {
              method: 'POST',
              body: fd
            });
            const data = await res.json();
            if (data.success || data.text) {
              setStatusText('Ready');
              onTranscribed(data.text);
              setTimeout(() => setStatusText('Voice'), 2000);
            } else {
              setStatusText('Error');
              setTimeout(() => setStatusText('Voice'), 2000);
            }
          } catch (e) {
            setStatusText('Network Error');
            setTimeout(() => setStatusText('Voice'), 2000);
          }
        };
        mediaRecorder.current.start();
        setRecording(true);
        setStatusText('Listening...');
      } catch (e) {
        setStatusText('Mic Denied');
        setTimeout(() => setStatusText('Voice'), 2000);
      }
    }
  };

  return (
    <button 
      onClick={toggleRecording} 
      disabled={disabled || (statusText !== 'Voice' && statusText !== 'Listening...' && statusText !== 'Ready')} 
      className={\`bg-[#F9F8F6] border border-slate-200 px-6 py-3 rounded-full text-sm font-medium transition-all shadow-sm \${recording ? 'bg-red-500 text-white border-red-500 hover:bg-red-600' : 'text-slate-800 hover:bg-white'}\`}
    >
      {recording ? (statusText === 'Listening...' ? 'Stop Recording' : statusText) : statusText}
    </button>
  );
};`;

lines.splice(start, end - start + 1, newVoiceButton);
fs.writeFileSync('src/App.jsx', lines.join('\n'));
