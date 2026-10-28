import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTripStore } from '../store/tripStore';

export default function RomeBuddyDrawer({
  isOpen,
  onClose,
  onOpen,
  trip,
  liveStatus = 'Not Started',
  liveMessages = [],
  chatMessages = [],
  onSendMessage,
  onClearChat,
  onExtractItinerary,
  onExtractBooking,
  isExtractingItinerary = false,
  isExtractingBooking = false
}) {
  const { addAlert } = useTripStore();
  const [inputText, setInputText] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [bookingStatus, setBookingStatus] = useState({});
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);
  const micStreamRef = useRef(null);

  const handleBuyTicket = async (eventId, title, venue, price, ticketUrl) => {
    setBookingStatus(prev => ({ ...prev, [eventId]: { status: 'booking' } }));
    try {
      const unitPrice = parseInt(String(price).replace(/[^0-9]/g, '')) || 350;
      const res = await fetch('http://localhost:8000/api/events/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event: {
            id: eventId,
            title: title || 'Live Indian Event',
            venue: venue || 'City Venue',
            unit_price: unitPrice,
            price: price || '₹350',
            ticket_url: ticketUrl || 'https://in.bookmyshow.com',
            city: trip?.destination || 'India',
            source: 'BookMyShow / Local City Concierge'
          },
          tickets: 2,
          attendee_name: 'Demo Traveler'
        })
      });
      const data = await res.json();
      if (data.success && data.booking) {
        setBookingStatus(prev => ({
          ...prev,
          [eventId]: { status: 'confirmed', ref: data.booking.booking_reference }
        }));
        if (addAlert) {
          addAlert({
            id: `alert-${Date.now()}`,
            title: "Event Pass Confirmed",
            change: {
              type: "BOOKING_CONFIRMED",
              description: `Reserved 2 passes for ${title} (${data.booking.booking_reference})`
            },
            severity: "LOW",
            timestamp: new Date().toISOString()
          });
        }
      } else {
        setBookingStatus(prev => ({ ...prev, [eventId]: { status: 'failed' } }));
      }
    } catch (err) {
      console.error("Booking error:", err);
      setBookingStatus(prev => ({ ...prev, [eventId]: { status: 'failed' } }));
    }
  };

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      setTimeout(() => inputRef.current?.focus(), 200);
    }
  }, [isOpen, chatMessages, isThinking]);

  // Voice recognition handling
  const stopVoiceRecording = () => {
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach(track => {
        try { track.stop(); } catch (e) {}
      });
      micStreamRef.current = null;
    }
    if (recognitionRef.current) {
      recognitionRef.current.onresult = null;
      recognitionRef.current.onerror = null;
      recognitionRef.current.onend = null;
      try { recognitionRef.current.stop(); } catch (e) {}
      recognitionRef.current = null;
    }
    setIsListening(false);
  };

  const startVoiceRecording = async () => {
    stopVoiceRecording();

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micStreamRef.current = stream;

      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      let baseText = inputText ? inputText.trim() + ' ' : '';

      recognition.onresult = (event) => {
        let finalChunk = '';
        let interimChunk = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const item = event.results[i];
          if (item.isFinal) {
            finalChunk += item[0].transcript;
          } else {
            interimChunk += item[0].transcript;
          }
        }
        if (finalChunk) {
          baseText += finalChunk + ' ';
          setInputText(baseText + interimChunk);
        } else {
          setInputText(baseText + interimChunk);
        }
      };

      recognition.onerror = (event) => {
        console.warn("Rome Buddy voice error:", event.error);
        if (event.error !== 'no-speech') {
          stopVoiceRecording();
        }
      };

      recognition.onend = () => {
        stopVoiceRecording();
      };

      recognition.start();
      setIsListening(true);
    } catch (err) {
      console.error("Microphone access error:", err);
      alert("Could not access microphone. Please allow microphone permissions in your browser.");
      stopVoiceRecording();
    }
  };

  const toggleVoiceRecording = () => {
    if (isListening) {
      stopVoiceRecording();
    } else {
      startVoiceRecording();
    }
  };

  useEffect(() => {
    return () => {
      stopVoiceRecording();
    };
  }, []);

  const handleSend = async (textToSend) => {
    const text = (textToSend || inputText).trim();
    if (!text || isThinking) return;

    if (isListening) {
      stopVoiceRecording();
    }

    setInputText('');
    setIsThinking(true);

    try {
      await onSendMessage(text);
    } catch (err) {
      console.error("Error sending message to Rome Buddy:", err);
    } finally {
      setIsThinking(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickPrompts = trip ? [
    {
      icon: "🗺️",
      title: "Suggest Day Itinerary",
      desc: "Full day schedule covering top scenic spots and optimal timings",
      query: `Can you suggest a complete day itinerary plan in ${trip.destination || 'this destination'} covering top scenic spots and timings?`
    },
    {
      icon: "🎟️",
      title: "Suggest Live Events to Attend",
      desc: "Verified local concerts, festivals, and comedy shows with booking links",
      query: `Suggest me live events and shows to attend in ${trip.destination || 'Mumbai'}`
    },
    {
      icon: "🍽️",
      title: "Best Local Food Nearby",
      desc: "Authentic regional specialties, street food stalls, and iconic eateries",
      query: `What are the best authentic local dishes and restaurants around ${trip.destination || 'here'}?`
    },
    {
      icon: "📍",
      title: "What's My Next Stop?",
      desc: "Inspect your current scheduled itinerary stop, arrival timing, and status",
      query: "What is my next scheduled stop and timing?"
    },
    {
      icon: "✨",
      title: "Hidden Gems & Viewpoints",
      desc: "Offbeat heritage spots and picturesque locations avoided by crowds",
      query: `What are must-see hidden gems and scenic viewpoints in ${trip.destination || 'this city'}?`
    },
    {
      icon: "🛡️",
      title: "How Does ROAM Protect Me?",
      desc: "Learn how the autonomous AI monitors delays and dynamically reschedules",
      query: "How does ROAM monitor disruptions and reschedule my trip automatically?"
    }
  ] : [
    {
      icon: "🎟️",
      title: "Suggest Live Events to Attend",
      desc: "Live BookMyShow & Google Events with authentic ticket purchase links",
      query: "Suggest me events to attend in Mumbai"
    },
    {
      icon: "🗺️",
      title: "Suggest Day Itinerary in India",
      desc: "Custom day plan with landmarks, cultural stops, and realistic timings",
      query: "Can you suggest or give a day itinerary plan covering top scenic spots and timings in India?"
    },
    {
      icon: "🍽️",
      title: "Famous Regional Food & Street Eats",
      desc: "Discover must-eat biryanis, chats, sweets, and iconic local cafes",
      query: "What are famous local food specialties and must-visit food spots you recommend in India?"
    },
    {
      icon: "✨",
      title: "Top Cultural Attractions & Heritage",
      desc: "Explore historic palaces, beaches, hill stations, and heritage centers",
      query: "What top travel destinations and hidden cultural gems in India should I explore?"
    },
    {
      icon: "🛡️",
      title: "How ROAM Monitoring Works",
      desc: "Autonomous disruption agent that monitors flight/train delays 24/7",
      query: "How does ROAM autonomously monitor flight/train delays and reschedule itineraries?"
    }
  ];

  // Heuristic to detect whether an assistant message is an itinerary response to an itinerary request
  const isItineraryResponse = (msg, index, messages) => {
    if (!msg || msg.role !== 'assistant' || !msg.content) return false;

    // 1. Look back for the preceding user query to ensure user asked for an itinerary / day plan
    let precedingUserText = '';
    for (let i = index - 1; i >= 0; i--) {
      if (messages[i]?.role === 'user') {
        precedingUserText = messages[i].content || '';
        break;
      }
    }

    const userAskedItinerary = /(?:suggest|give|gime|provide|create|make|show|plan|build|share|recommend|draft|write).*(?:itinerar|itenar|itenerar|itinary|day plan|tour plan|trip plan|schedule|stops)/i.test(precedingUserText) ||
      /(?:itinerar|itenar|itenerar|itinary).*(?:suggest|give|gime|plan|spots|day|trip|recommend|schedule)/i.test(precedingUserText) ||
      /\b(?:day plan|trip plan|tour plan|itinerary|itenary|itenerary)\b/i.test(precedingUserText);

    // 2. Check if the assistant message content represents an itinerary with schedule/stops/details
    const content = msg.content;
    const hasItineraryWord = /(?:itinerar|itenar|itenerar|trip plan|day plan|tour plan)/i.test(content);
    const hasTimeSchedule = /\b\d{1,2}:\d{2}\b/.test(content) ||
      /\|\s*Time/i.test(content) ||
      /\b(?:Stop\s*\d+|Day\s*\d+)\b/i.test(content);

    // ONLY AND ONLY when both the user asked for an itinerary/plan AND the assistant gave an itinerary
    return Boolean(userAskedItinerary && (hasItineraryWord || hasTimeSchedule));
  };

  const parseBoldText = (text) => {
    if (!text || typeof text !== 'string') return text || '';
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part && part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  const parseInlineElements = (text) => {
    if (!text || typeof text !== 'string') return text || '';

    // Match markdown links [Label](url)
    const linkRegex = /\[(.*?)\]\((.*?)\)/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = linkRegex.exec(text)) !== null) {
      const matchIndex = match.index;
      if (matchIndex > lastIndex) {
        parts.push(parseBoldText(text.substring(lastIndex, matchIndex)));
      }

      const label = match[1];
      const url = match[2];

      if (url.startsWith('book:')) {
        const rawPayload = url.replace('book:', '');
        const segments = rawPayload.split(':::');
        const evId = segments[0] || 'evt-gen';
        const evTitle = segments[1] || label.replace(/[🎟️\s]/g, '');
        const evVenue = segments[2] || 'Local Venue';
        const evPrice = segments[3] || '₹350';
        const evTicketUrl = segments[4] || 'https://in.bookmyshow.com';

        const currentStatus = bookingStatus[evId];

        if (currentStatus?.status === 'confirmed') {
          parts.push(
            <span
              key={`booked-${matchIndex}`}
              className="inline-flex items-center gap-1.5 bg-emerald-100 text-emerald-900 border border-emerald-300 text-[11px] font-bold px-3 py-1 rounded-full shadow-xs my-0.5"
            >
              <span>✓ Pass Reserved</span>
              <span className="font-mono text-[10px] text-emerald-700">({currentStatus.ref})</span>
            </span>
          );
        } else if (currentStatus?.status === 'booking') {
          parts.push(
            <span
              key={`booking-${matchIndex}`}
              className="inline-flex items-center gap-1.5 bg-slate-100 text-slate-700 text-[11px] font-bold px-3 py-1 rounded-full border border-slate-200 my-0.5"
            >
              <span className="w-2.5 h-2.5 border-2 border-slate-700 border-t-transparent rounded-full animate-spin inline-block" />
              <span>Reserving...</span>
            </span>
          );
        } else {
          parts.push(
            <button
              key={`btn-book-${matchIndex}`}
              type="button"
              onClick={() => handleBuyTicket(evId, evTitle, evVenue, evPrice, evTicketUrl)}
              className="inline-flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white text-[11px] font-bold px-3.5 py-1.5 rounded-full shadow-xs active:scale-95 transition-all my-0.5 cursor-pointer"
            >
              <span>🎟️ Buy Ticket</span>
            </button>
          );
        }
      } else if (url.startsWith('http://') || url.startsWith('https://')) {
        let cleanUrl = url;
        // Fix bare bookmyshow URL so it never opens a blank page in user browser
        if (cleanUrl.includes('bookmyshow.com/explore/events') && !cleanUrl.includes('explore/events-')) {
          const contextLow = `${text || ''} ${trip?.destination || ''}`.toLowerCase();
          let slug = 'mumbai';
          if (contextLow.includes('delhi')) slug = 'national-capital-region-ncr';
          else if (contextLow.includes('mumbai') || contextLow.includes('bombay')) slug = 'mumbai';
          else if (contextLow.includes('bangalore') || contextLow.includes('bengaluru') || contextLow.includes('karnataka')) slug = 'bengaluru';
          else if (contextLow.includes('jaipur') || contextLow.includes('rajasthan')) slug = 'jaipur';
          else if (contextLow.includes('hyderabad') || contextLow.includes('telangana')) slug = 'hyderabad';
          else if (contextLow.includes('goa') || contextLow.includes('panaji')) slug = 'goa';
          else if (contextLow.includes('chennai') || contextLow.includes('madras')) slug = 'chennai';
          else if (contextLow.includes('kolkata') || contextLow.includes('calcutta')) slug = 'kolkata';
          else if (contextLow.includes('pune')) slug = 'pune';
          else if (contextLow.includes('ahmedabad') || contextLow.includes('gujarat')) slug = 'ahmedabad';
          else if (contextLow.includes('chandigarh') || contextLow.includes('punjab')) slug = 'chandigarh';
          cleanUrl = `https://in.bookmyshow.com/explore/events-${slug}`;
        }
        parts.push(
          <a
            key={`link-${matchIndex}`}
            href={cleanUrl}
            target="_blank"
            rel="noopener noreferrer"
            title="Open verified booking website in a new tab"
            className="inline-flex items-center gap-1.5 bg-amber-50 hover:bg-amber-100 text-amber-950 border border-amber-300/80 text-[11px] font-bold px-3 py-1 rounded-full shadow-xs active:scale-95 transition-all my-0.5 group cursor-pointer"
          >
            <span>{label.replace(/↗/g, '').trim()}</span>
            <span className="text-[12px] font-extrabold text-amber-700 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform">
              ↗
            </span>
          </a>
        );
      } else {
        parts.push(
          <span key={`txt-${matchIndex}`} className="font-medium text-indigo-700">
            {label}
          </span>
        );
      }

      lastIndex = linkRegex.lastIndex;
    }

    if (lastIndex < text.length) {
      parts.push(parseBoldText(text.substring(lastIndex)));
    }

    return parts;
  };

  // Helper to format assistant messages with markdown-like styling & responsive tables
  const renderFormattedContent = (content) => {
    if (!content) return null;
    const lines = content.split('\n');
    const elements = [];
    let currentTable = null;

    lines.forEach((line, idx) => {
      const trimmed = line.trim();

      // Check if line is part of a markdown table (e.g. | Time | Stop | ...)
      if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
        const cells = trimmed
          .split('|')
          .slice(1, -1)
          .map(c => c.trim());
        
        const isDivider = cells.every(c => /^[-:\s]+$/.test(c));

        if (!currentTable) {
          currentTable = { headers: cells, rows: [] };
        } else if (isDivider) {
          // divider row between thead and tbody
        } else {
          currentTable.rows.push(cells);
        }
        return;
      }

      // Flush table if non-table line encountered
      if (currentTable) {
        elements.push(renderTableBlock(currentTable, `tbl-${idx}`));
        currentTable = null;
      }

      if (!trimmed) {
        elements.push(<div key={`blank-${idx}`} className="h-1" />);
        return;
      }

      // Bullet point line
      if (trimmed.startsWith('•') || trimmed.startsWith('-') || trimmed.startsWith('*')) {
        const cleanText = trimmed.replace(/^[\s•\-\*]+/, '');
        elements.push(
          <div key={`bullet-${idx}`} className="flex items-start gap-2 pl-1 py-0.5">
            <span className="text-amber-600 font-bold mt-0.5">•</span>
            <div className="flex-1 flex flex-wrap items-center gap-1.5">{parseInlineElements(cleanText)}</div>
          </div>
        );
        return;
      }

      elements.push(
        <div key={`p-${idx}`} className="flex flex-wrap items-center gap-1.5 py-0.5">
          {parseInlineElements(trimmed)}
        </div>
      );
    });

    if (currentTable) {
      elements.push(renderTableBlock(currentTable, 'tbl-end'));
    }

    return <div className="space-y-1.5">{elements}</div>;
  };

  const renderTableBlock = (table, key) => (
    <div key={key} className="overflow-x-auto my-2 rounded-xl border border-slate-200/90 bg-white shadow-2xs">
      <table className="min-w-full text-xs divide-y divide-slate-200">
        {table.headers && (
          <thead className="bg-slate-100/80">
            <tr>
              {table.headers.map((h, i) => (
                <th key={i} className="px-2.5 py-1.5 text-left font-bold text-slate-800 tracking-wider">
                  {parseBoldText(h || '')}
                </th>
              ))}
            </tr>
          </thead>
        )}
        <tbody className="divide-y divide-slate-100">
          {table.rows.map((row, rIdx) => (
            <tr key={rIdx} className={rIdx % 2 === 0 ? 'bg-transparent' : 'bg-slate-50/50'}>
              {row.map((cell, cIdx) => (
                <td key={cIdx} className="px-2.5 py-1.5 text-slate-700 align-top">
                  {parseBoldText(cell || '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  const totalStops = trip?.days?.reduce((acc, d) => acc + (d.stops?.length || 0), 0) || 0;

  return (
    <>
      {/* 1. FLOATING CIRCULAR ACTION BUTTON WITH SPLINE & STITCH FLOATING LEVITATION PHYSICS */}
      <AnimatePresence>
        {!isOpen && (
          <div className="fixed bottom-6 right-6 z-50 select-none">
            {/* Dynamic Ground Levitation Shadow (Spline 3D ground occlusion effect) */}
            <motion.div
              animate={{
                scale: [1, 0.76, 1],
                opacity: [0.35, 0.16, 0.35],
                y: [0, 4, 0]
              }}
              transition={{
                duration: 3.6,
                repeat: Infinity,
                ease: "easeInOut"
              }}
              className="absolute -bottom-3 left-1/2 -translate-x-1/2 w-14 h-4 bg-slate-900/40 rounded-full blur-md pointer-events-none"
            />

            {/* Continuous Spline 3D Harmonic Levitation Container */}
            <motion.div
              animate={{
                y: [0, -10, 0],
                rotate: [0, 1.5, -1.5, 0]
              }}
              transition={{
                duration: 3.6,
                repeat: Infinity,
                ease: "easeInOut"
              }}
              whileHover={{
                scale: 1.12,
                y: -14,
                transition: { duration: 0.25, ease: "easeOut" }
              }}
              whileTap={{
                scale: 0.92,
                transition: { duration: 0.1 }
              }}
              className="relative group cursor-pointer"
            >
              {/* Stitch-style Concentric Audio/Radar Signal Rings */}
              <span className="absolute -inset-1.5 rounded-full border-2 border-emerald-400/50 animate-ping opacity-60 pointer-events-none" />
              <span className="absolute -inset-3 rounded-full border border-slate-900/10 pointer-events-none animate-pulse" />

              {/* Glowing Ambient Backdrop Aura */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-amber-400/20 via-orange-400/20 to-emerald-400/20 blur-lg group-hover:blur-xl transition-all duration-300" />

              {/* The Circular Floating Button */}
              <button
                type="button"
                onClick={onOpen}
                className="relative w-16 h-16 sm:w-[68px] sm:h-[68px] rounded-full bg-white shadow-[0_16px_36px_-6px_rgba(0,0,0,0.24),0_6px_16px_rgba(0,0,0,0.08),inset_0_1px_1px_rgba(255,255,255,1)] border-2 border-slate-200/90 hover:border-slate-800 transition-colors duration-300 flex items-center justify-center overflow-hidden focus:outline-none focus:ring-4 focus:ring-slate-900/15"
                aria-label="Open Rome Buddy"
              >
                {/* Spline-style Light Sheen Sweep Effect */}
                <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/60 to-transparent pointer-events-none z-10" />

                {/* The User-Provided RB Monogram Circular Image */}
                <img
                  src="/rome_buddy_logo.png"
                  alt="Rome Buddy Logo"
                  className="w-full h-full object-contain p-2 select-none pointer-events-none transition-transform duration-300 group-hover:scale-108 group-hover:rotate-3"
                  draggable={false}
                />

                {/* Active Online Beacon Dot on Perimeter */}
                <span className="absolute top-1 right-1 flex h-3 w-3 z-20">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-80" />
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500 border-2 border-white" />
                </span>
              </button>

              {/* Floating Tooltip Bubble on Hover (Stitch micro-badge) */}
              <div className="absolute -top-10 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none transform group-hover:-translate-y-1">
                <div className="bg-slate-900/95 text-white text-[11px] font-bold uppercase tracking-wider px-3 py-1 rounded-full shadow-xl border border-slate-700/80 backdrop-blur-md flex items-center gap-1.5 whitespace-nowrap">
                  <span>Rome Buddy</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* 2. FLOATING DRAWER PANEL */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 35, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 35, scale: 0.96 }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
            className="fixed bottom-4 right-4 sm:right-6 z-50 w-[calc(100vw-2rem)] sm:w-[440px] md:w-[470px] h-[670px] max-h-[88vh] bg-white/95 backdrop-blur-2xl rounded-[2.5rem] shadow-2xl border border-slate-200/90 flex flex-col overflow-hidden ring-1 ring-black/5"
            role="dialog"
            aria-label="Rome Buddy Travel Companion"
          >
            {/* Top Header */}
            <div className="p-5 border-b border-slate-100/90 bg-[#F9F8F6]/80 flex flex-col gap-2.5 flex-shrink-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <div className="w-11 h-11 rounded-full bg-white border border-slate-200/90 shadow-md ring-2 ring-white flex items-center justify-center overflow-hidden">
                      <img src="/rome_buddy_logo.png" alt="Rome Buddy" className="w-full h-full object-contain p-1" />
                    </div>
                    <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full border-2 border-white" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="font-serif font-bold text-lg text-slate-900 leading-tight">Rome Buddy</h2>
                      <span className="bg-emerald-50 text-emerald-700 border border-emerald-200/80 text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full">
                        Online
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 font-medium">Personal AI Travel Companion</p>
                  </div>
                </div>

                {/* Actions: Clear & Close */}
                <div className="flex items-center gap-1">
                  {chatMessages.length > 0 && (
                    <button
                      type="button"
                      onClick={onClearChat}
                      className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-200/50 rounded-full transition-colors"
                      title="Clear chat history"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={onClose}
                    className="p-2 text-slate-400 hover:text-slate-800 hover:bg-slate-200/50 rounded-full transition-colors"
                    title="Close Rome Buddy"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Context Indicator */}
              {trip ? (
                <div className="flex items-center justify-between px-3 py-1.5 bg-white/90 rounded-xl text-xs text-slate-700 border border-slate-200/70 shadow-xs">
                  <div className="flex items-center gap-1.5 truncate">
                    <span className="text-amber-600 font-bold">📍</span>
                    <span className="font-semibold text-slate-900 truncate">{trip.name || trip.destination}</span>
                    <span className="text-slate-400 font-normal">({totalStops} stops)</span>
                  </div>
                  <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                    Trip Context
                  </span>
                </div>
              ) : (
                <div className="flex items-center justify-between px-3 py-1.5 bg-amber-50/70 rounded-xl text-xs text-amber-950 border border-amber-200/50 shadow-xs">
                  <div className="flex items-center gap-1.5 truncate">
                    <span>🌍</span>
                    <span className="font-medium truncate">General Travel & Food Discovery</span>
                  </div>
                  <span className="text-[10px] uppercase font-bold tracking-wider text-amber-700 bg-amber-100/70 px-2 py-0.5 rounded-md">
                    Explore Mode
                  </span>
                </div>
              )}
            </div>

            {/* Live messages alert inside drawer if any */}
            {liveMessages.length > 0 && (
              <div className="px-5 py-2.5 bg-blue-50/70 border-b border-blue-100 text-xs text-blue-900 flex items-center justify-between flex-shrink-0">
                <div className="flex items-center gap-2 truncate">
                  <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse flex-shrink-0" />
                  <span className="font-medium truncate">{liveMessages[0]}</span>
                </div>
                <span className="text-[10px] uppercase font-bold tracking-wider text-blue-700 bg-blue-100/70 px-2 py-0.5 rounded-md flex-shrink-0 ml-2">
                  {liveStatus}
                </span>
              </div>
            )}

            {/* Messages Stream Area */}
            <div className="flex-1 p-5 overflow-y-auto space-y-4">
              {/* Welcoming Greeting */}
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-white border border-slate-200/90 shadow-xs flex items-center justify-center flex-shrink-0 mt-0.5 overflow-hidden">
                  <img src="/rome_buddy_logo.png" alt="Rome Buddy" className="w-full h-full object-contain p-1" />
                </div>
                <div className="bg-[#F7F5F0] border border-slate-200/80 text-slate-800 rounded-3xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed max-w-[88%] shadow-xs">
                  <p className="font-serif font-bold text-slate-900 mb-1">Ciao & Welcome! 👋</p>
                  <p className="text-slate-700">
                    I’m <strong>Rome Buddy</strong>, your AI travel companion on ROAM.
                    {trip
                      ? ` I’m fully synced with your journey to ${trip.destination || 'your destination'}. Ask me about your schedule, opening hours, local dishes, or hidden spots!`
                      : " Ask me anything about destination ideas, must-eat local food, packing tips, or how ROAM protects you against disruptions!"}
                  </p>
                </div>
              </div>

              {/* Vertical Suggestions List directly below Welcoming Greeting */}
              {chatMessages.length === 0 && (
                <div className="pl-11 pr-1 pt-1 space-y-2.5 animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
                    <span>Suggestions — Click to Ask:</span>
                  </div>
                  <div className="space-y-2">
                    {quickPrompts.map((p, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handleSend(p.query)}
                        disabled={isThinking}
                        className="w-full text-left p-3.5 rounded-2xl bg-white hover:bg-amber-50/90 border border-slate-200/90 hover:border-amber-300 text-slate-800 hover:text-amber-950 transition-all shadow-2xs hover:shadow-md flex items-center justify-between group active:scale-[0.99] cursor-pointer"
                      >
                        <div className="flex items-center gap-3 pr-2 min-w-0">
                          <span className="text-xl p-2 rounded-xl bg-slate-50 border border-slate-100 group-hover:bg-amber-100/70 group-hover:border-amber-200 transition-colors flex-shrink-0">
                            {p.icon}
                          </span>
                          <div className="min-w-0">
                            <div className="text-xs font-bold text-slate-900 group-hover:text-amber-950 truncate">
                              {p.title}
                            </div>
                            <div className="text-[11px] text-slate-500 font-light truncate">
                              {p.desc}
                            </div>
                          </div>
                        </div>
                        <span className="text-slate-400 group-hover:text-amber-700 text-sm font-bold pl-1 group-hover:translate-x-1 transition-all flex-shrink-0">
                          &rarr;
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Chat History */}
              {chatMessages.map((msg, idx) => {
                const isUser = msg.role === 'user';
                const isItinerary = !isUser && isItineraryResponse(msg, idx, chatMessages);
                return (
                  <div key={idx} className={`flex items-start gap-2.5 ${isUser ? 'justify-end' : 'justify-start'}`}>
                    {!isUser && (
                      <div className="w-8 h-8 rounded-full bg-white border border-slate-200/90 shadow-xs flex items-center justify-center flex-shrink-0 mt-0.5 overflow-hidden">
                        <img src="/rome_buddy_logo.png" alt="Rome Buddy" className="w-full h-full object-contain p-1" />
                      </div>
                    )}
                    <div
                      className={`text-sm px-4 py-3 rounded-2xl max-w-[85%] leading-relaxed ${
                        isUser
                          ? 'bg-slate-900 text-white rounded-br-sm shadow-sm'
                          : 'bg-[#F7F5F0] border border-slate-200/80 text-slate-800 rounded-tl-sm shadow-xs'
                      }`}
                    >
                      {isUser ? msg.content : renderFormattedContent(msg.content)}

                      {/* Agentic Itinerary Action: ONLY AND ONLY after giving an itinerary */}
                      {isItinerary && (
                        <div className="mt-3 pt-2.5 border-t border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                          <div className="flex items-center gap-1.5 text-[11px] text-slate-600 font-medium">
                            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse flex-shrink-0" />
                            <span>Itinerary ready to extract & save</span>
                          </div>
                          <button
                            type="button"
                            onClick={() => onExtractItinerary && onExtractItinerary(msg.content)}
                            disabled={isExtractingItinerary}
                            className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-full text-xs font-bold tracking-wider uppercase transition-all shadow-md hover:shadow-lg active:scale-95 disabled:opacity-50 cursor-pointer self-start sm:self-auto group"
                            title="Structure this itinerary and save it to Explore Trips"
                          >
                            <svg className="w-3.5 h-3.5 text-amber-400 fill-current group-hover:scale-110 transition-transform" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
                            </svg>
                            <span>{isExtractingItinerary ? 'Structuring Itinerary...' : 'Extract Itinerary'}</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Thinking Indicator */}
              {isThinking && (
                <div className="flex items-start gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-white border border-slate-200/90 shadow-xs flex items-center justify-center flex-shrink-0 mt-0.5 overflow-hidden animate-pulse">
                    <img src="/rome_buddy_logo.png" alt="Rome Buddy" className="w-full h-full object-contain p-1" />
                  </div>
                  <div className="bg-[#F7F5F0] border border-slate-200/80 text-slate-500 rounded-2xl rounded-tl-sm px-4 py-3 text-xs flex items-center gap-2 shadow-xs">
                    <span className="font-medium">Rome Buddy is thinking</span>
                    <span className="flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                    </span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Voice Listening Feedback Banner */}
            {isListening && (
              <div className="px-5 py-2 bg-red-50 border-t border-red-200 flex items-center justify-between text-xs text-red-700 animate-pulse flex-shrink-0">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-600 animate-ping" />
                  <span className="font-bold">Listening to you...</span>
                  <span className="text-red-500">Speak your question clearly</span>
                </div>
                <button
                  type="button"
                  onClick={stopVoiceRecording}
                  className="text-[11px] font-bold uppercase tracking-wider text-red-800 hover:underline"
                >
                  Done Speaking
                </button>
              </div>
            )}

            {/* Input Bar */}
            <div className="p-4 bg-white/95 border-t border-slate-100 flex items-center gap-2 flex-shrink-0">
              {/* Voice Record Button */}
              <button
                type="button"
                onClick={toggleVoiceRecording}
                disabled={isThinking}
                title={isListening ? "Stop voice recording" : "Speak to Rome Buddy"}
                className={`p-3 rounded-full border transition-all flex items-center justify-center flex-shrink-0 ${
                  isListening
                    ? 'bg-red-500 text-white border-red-600 shadow-md animate-pulse ring-4 ring-red-100'
                    : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100 hover:text-slate-900 shadow-xs'
                }`}
                aria-label="Voice input"
              >
                <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                </svg>
              </button>

              {/* Text Input */}
              <input
                ref={inputRef}
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isThinking}
                placeholder={isListening ? "Listening... (or type here)" : "Ask Rome Buddy anything (e.g. food, tips)..."}
                className="flex-1 text-sm px-4 py-3 bg-[#F9F8F6] border border-slate-200 rounded-full focus:outline-none focus:ring-2 focus:ring-slate-300 focus:bg-white transition-all shadow-inner text-slate-800 placeholder-slate-400"
              />

              {/* Send Button */}
              <button
                type="button"
                onClick={() => handleSend()}
                disabled={!inputText.trim() || isThinking}
                className="p-3 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-slate-900 text-white rounded-full transition-all shadow-md active:scale-95 flex items-center justify-center flex-shrink-0"
                title="Send message"
                aria-label="Send message"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
