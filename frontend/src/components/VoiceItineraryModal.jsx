import React, { useState, useEffect, useRef } from 'react';

export default function VoiceItineraryModal({ isOpen, onClose, onSubmitItinerary }) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimText, setInterimText] = useState('');
  const [statusMessage, setStatusMessage] = useState('Click Start Recording and describe your trip.');
  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const streamRef = useRef(null);
  const recognitionRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const isRecordingRef = useRef(false);

  // Sync ref with state
  useEffect(() => {
    isRecordingRef.current = isRecording;
  }, [isRecording]);

  // Clean up all tracks and recognition on unmount or close
  const cleanupMicrophone = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        try {
          track.stop();
        } catch (e) {
          console.error('Error stopping track:', e);
        }
      });
      streamRef.current = null;
    }

    if (recognitionRef.current) {
      recognitionRef.current.onresult = null;
      recognitionRef.current.onerror = null;
      recognitionRef.current.onend = null;
      try {
        recognitionRef.current.abort();
      } catch (e) {}
      recognitionRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {}
      mediaRecorderRef.current = null;
    }

    setIsRecording(false);
  };

  useEffect(() => {
    if (!isOpen) {
      cleanupMicrophone();
      setInterimText('');
      setErrorMessage('');
      setStatusMessage('Click Start Recording and describe your trip.');
    }
    return () => {
      cleanupMicrophone();
    };
  }, [isOpen]);

  const handleStartRecording = async () => {
    setErrorMessage('');
    setInterimText('');
    setStatusMessage('Requesting microphone permission...');

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;

    try {
      // 1. Explicitly acquire user media only after user clicked start
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // 2. Set up MediaRecorder for backup transcription
      audioChunksRef.current = [];
      try {
        const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        mr.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) audioChunksRef.current.push(e.data);
        };
        mediaRecorderRef.current = mr;
        mr.start();
      } catch (mrErr) {
        console.warn('MediaRecorder not available or mimeType unsupported:', mrErr);
      }

      // 3. Set up SpeechRecognition if available
      if (SpeechRec) {
        const recognition = new SpeechRec();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
          setIsRecording(true);
          setStatusMessage('Listening... Speak your itinerary naturally.');
        };

        recognition.onresult = (event) => {
          let currentInterim = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const transcriptSegment = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              setTranscript((prev) => {
                const trimmed = prev.trim();
                return trimmed ? `${trimmed} ${transcriptSegment.trim()}` : transcriptSegment.trim();
              });
            } else {
              currentInterim += transcriptSegment;
            }
          }
          setInterimText(currentInterim);
        };

        recognition.onerror = (event) => {
          console.warn('SpeechRecognition error:', event.error);
          if (event.error === 'not-allowed') {
            setErrorMessage('Microphone access denied. Please grant permission in your browser.');
            handleStopRecording();
          } else if (event.error === 'network') {
            setErrorMessage('Speech service network error.');
          }
        };

        recognition.onend = () => {
          // If still marked as recording, restart it if browser ended early
          if (isRecordingRef.current && recognitionRef.current) {
            try {
              recognition.start();
            } catch (e) {}
          }
        };

        recognitionRef.current = recognition;
        recognition.start();
      } else {
        // Fallback for browsers without Web Speech API
        setIsRecording(true);
        setStatusMessage('Recording audio... (live speech-to-text not supported in this browser, will transcribe on Stop)');
      }
    } catch (err) {
      console.error('Microphone error:', err);
      cleanupMicrophone();
      setErrorMessage('Could not access microphone: ' + (err.message || 'Permission denied'));
      setStatusMessage('Microphone access error.');
    }
  };

  const handleStopRecording = async () => {
    setStatusMessage('Stopping recording...');

    // Finalize interim text
    if (interimText.trim()) {
      setTranscript((prev) => {
        const trimmed = prev.trim();
        return trimmed ? `${trimmed} ${interimText.trim()}` : interimText.trim();
      });
      setInterimText('');
    }

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;

    // Stop recognition
    if (recognitionRef.current) {
      recognitionRef.current.onend = null;
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      recognitionRef.current = null;
    }

    // Stop MediaRecorder and handle fallback if needed
    const wasFallback = !SpeechRec;
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      const mr = mediaRecorderRef.current;
      mr.onstop = async () => {
        if (wasFallback && audioChunksRef.current.length > 0) {
          setStatusMessage('Transcribing audio via backend...');
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const fd = new FormData();
          fd.append('file', audioBlob, 'voice_recording.webm');
          try {
            const res = await fetch('http://localhost:8000/api/voice/transcribe', {
              method: 'POST',
              body: fd
            });
            const data = await res.json();
            if (data.success && data.text) {
              setTranscript((prev) => {
                const trimmed = prev.trim();
                return trimmed ? `${trimmed} ${data.text.trim()}` : data.text.trim();
              });
              setStatusMessage('Transcription complete. You can review and edit below.');
            } else {
              setErrorMessage('Failed to transcribe audio.');
              setStatusMessage('Transcription failed.');
            }
          } catch (e) {
            setErrorMessage('Network error while transcribing audio.');
            setStatusMessage('Error transcribing audio.');
          }
        }
      };
      try {
        mr.stop();
      } catch (e) {}
      mediaRecorderRef.current = null;
    }

    // Release microphone tracks immediately so browser mic indicator turns off
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        try {
          track.stop();
        } catch (e) {}
      });
      streamRef.current = null;
    }

    setIsRecording(false);
    if (!wasFallback) {
      setStatusMessage('Recording stopped. You can edit the text before creating the itinerary.');
    }
  };

  const handleCreateItinerary = async () => {
    if (isRecording) {
      await handleStopRecording();
    }

    const finalText = (transcript + (interimText ? ' ' + interimText : '')).trim();
    if (!finalText) {
      setErrorMessage('Please record or type an itinerary before creating.');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmitItinerary(finalText);
      cleanupMicrophone();
      onClose();
    } catch (err) {
      setErrorMessage('Failed to create itinerary: ' + (err.message || 'Server error'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    cleanupMicrophone();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
      <div 
        className="bg-[#FAF9F6] border border-slate-200/80 rounded-3xl shadow-2xl p-6 md:p-8 max-w-2xl w-full relative flex flex-col max-h-[90vh] overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-labelledby="voice-modal-title"
      >
        {/* Top Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-200/60 mb-6">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${isRecording ? 'bg-red-500 animate-ping' : 'bg-slate-400'}`} />
            <div>
              <h2 id="voice-modal-title" className="font-serif font-bold text-2xl text-slate-900">
                Voice Itinerary
              </h2>
              <p className="text-xs text-slate-500 uppercase tracking-widest font-sans mt-0.5">
                Describe your journey by voice
              </p>
            </div>
          </div>
          <button 
            onClick={handleClose}
            className="w-9 h-9 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 hover:text-slate-800 flex items-center justify-center transition-colors text-lg"
            aria-label="Close"
          >
            &times;
          </button>
        </div>

        {/* Live Status Banner */}
        <div className="mb-4 flex items-center justify-between p-3 bg-white rounded-2xl border border-slate-100 shadow-sm">
          <div className="flex items-center gap-2.5">
            {isRecording ? (
              <span className="flex h-3 w-3 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
              </span>
            ) : (
              <span className="w-2.5 h-2.5 rounded-full bg-slate-300"></span>
            )}
            <span className={`text-xs font-bold uppercase tracking-wider ${isRecording ? 'text-red-600' : 'text-slate-600'}`}>
              {statusMessage}
            </span>
          </div>
          
          {isRecording && (
            <span className="text-[11px] bg-red-50 text-red-600 font-bold px-2.5 py-1 rounded-full border border-red-200 animate-pulse">
              LIVE
            </span>
          )}
        </div>

        {/* Live Transcription / Editable Text Area */}
        <div className="flex-1 flex flex-col mb-6 min-h-[220px]">
          <label className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2 block">
            Transcription (Live & Editable)
          </label>
          <div className="relative flex-1 flex flex-col">
            <textarea
              value={transcript + (interimText ? ' ' + interimText : '')}
              onChange={(e) => {
                setTranscript(e.target.value);
                setInterimText('');
              }}
              placeholder="Your live words will appear here as you speak. You can also edit, correct spelling, or type directly into this box..."
              className="w-full flex-1 min-h-[180px] p-4 bg-white border border-slate-200 rounded-2xl font-serif text-base text-slate-800 placeholder:font-sans placeholder:text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-300 resize-none shadow-inner"
            />
          </div>
          {errorMessage && (
            <p className="text-xs font-medium text-red-600 mt-2">{errorMessage}</p>
          )}
        </div>

        {/* Controls */}
        <div className="pt-4 border-t border-slate-200/60 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            {!isRecording ? (
              <button
                onClick={handleStartRecording}
                disabled={isSubmitting}
                className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-bold tracking-wider text-xs uppercase rounded-full shadow-md transition-all flex items-center gap-2"
              >
                <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                </svg>
                {transcript ? 'Resume Recording' : 'Start Recording'}
              </button>
            ) : (
              <button
                onClick={handleStopRecording}
                className="px-6 py-3 bg-slate-900 hover:bg-slate-800 text-white font-bold tracking-wider text-xs uppercase rounded-full shadow-md transition-all flex items-center gap-2 border border-slate-700 animate-pulse"
              >
                <span className="w-2.5 h-2.5 rounded-sm bg-red-500"></span>
                Stop Recording
              </button>
            )}

            {transcript && (
              <button
                onClick={() => { setTranscript(''); setInterimText(''); }}
                disabled={isRecording || isSubmitting}
                className="px-4 py-2 text-xs font-medium text-slate-500 hover:text-slate-800 transition-colors"
              >
                Clear Text
              </button>
            )}
          </div>

          <div className="flex items-center gap-3 ml-auto">
            <button
              onClick={handleClose}
              disabled={isSubmitting}
              className="px-5 py-3 border border-slate-200 text-slate-600 hover:bg-slate-100 rounded-full text-xs font-bold uppercase tracking-wider transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateItinerary}
              disabled={isSubmitting || (!transcript.trim() && !interimText.trim())}
              className="px-6 py-3 bg-slate-900 hover:bg-slate-800 text-white font-bold tracking-wider text-xs uppercase rounded-full shadow-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  Structuring...
                </>
              ) : (
                'Create Itinerary &rarr;'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
