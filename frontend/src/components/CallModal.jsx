import { useState, useRef, useCallback, useEffect } from 'react';
import { Mic, MicOff, PhoneOff, Phone } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

export default function CallModal({ onClose, speakerOn, currentAudioRef }) {
  const [status, setStatus] = useState('');
  const [statusColor, setStatusColor] = useState('var(--mu)');
  const [showRipple, setShowRipple] = useState(false);
  const [showLog, setShowLog] = useState(false);
  const [logs, setLogs] = useState([]);
  const [micOn, setMicOn] = useState(false);
  const [callIcon, setCallIcon] = useState('📱');
  const [connected, setConnected] = useState(false);

  const callHistoryRef = useRef([]);
  const recognitionRef = useRef(null);
  const isAISpeakingRef = useRef(false);
  const sessionIdRef = useRef('call_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8));

  const setCS = useCallback((msg, col) => {
    setStatus(msg);
    setStatusColor(col || 'var(--green)');
  }, []);

  const addLog = useCallback((text, role) => {
    setLogs(prev => [...prev, { text, role, id: Date.now() + Math.random() }]);
  }, []);

  const speak = useCallback(async (text) => {
    if (!speakerOn || !text) return;
    const clean = text.replace(/[\u{1F300}-\u{1FFFF}]/gu, '').replace(/[—]/g, ', ').replace(/[•\n]/g, ' ').replace(/  +/g, ' ').trim();
    if (!clean) return;
    // KILL all audio to prevent echo
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (currentAudioRef.current) { currentAudioRef.current.pause(); currentAudioRef.current.src = ''; currentAudioRef.current = null; }
    isAISpeakingRef.current = true;

    try {
      const r = await fetch(`${API}/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: clean })
      });
      if (!r.ok) throw new Error('TTS failed');
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      if (currentAudioRef.current) { currentAudioRef.current.pause(); currentAudioRef.current.src = ''; }
      if (window.speechSynthesis) window.speechSynthesis.cancel();
      const audio = new Audio(url);
      audio.playbackRate = 1.05;
      currentAudioRef.current = audio;
      audio.onended = () => { URL.revokeObjectURL(url); isAISpeakingRef.current = false; currentAudioRef.current = null; };
      audio.onerror = () => { isAISpeakingRef.current = false; currentAudioRef.current = null; };
      await audio.play();
    } catch {
      isAISpeakingRef.current = false;
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
        const utt = new SpeechSynthesisUtterance(clean);
        utt.rate = 1.0; utt.pitch = 0.95;
        utt.onend = () => { isAISpeakingRef.current = false; };
        window.speechSynthesis.speak(utt);
      }
    }
  }, [speakerOn, currentAudioRef]);

  const callSpeak = useCallback((text) => {
    addLog(text, 'ai');
    setShowRipple(true);
    setCS('Riya speaking...', 'var(--gold)');
    speak(text);
    setTimeout(() => {
      setShowRipple(false);
      if (connected) setCS('Tap mic to speak', 'var(--green)');
    }, 3500);
  }, [addLog, setCS, speak, connected]);

  const handleCallSpeech = useCallback(async (text) => {
    if (!text) return;
    addLog(text, 'caller');
    setCS('...', 'var(--mu)');
    callHistoryRef.current.push({ role: 'user', content: text });
    if (callHistoryRef.current.length > 16) callHistoryRef.current.splice(0, 2);

    try {
      const r = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionIdRef.current,
          message: text,
          is_call: true,
          lang: 'auto'
        })
      });
      const d = await r.json();
      if (d.reply) {
        callHistoryRef.current.push({ role: 'assistant', content: d.reply });
        callSpeak(d.reply);
      }
    } catch {
      setCS('Connection issue — try again', '#C03030');
    }
  }, [addLog, setCS, callSpeak]);

  const toggleMic = useCallback(() => {
    if (micOn) {
      try { recognitionRef.current?.stop(); } catch {}
      setMicOn(false);
      return;
    }

    if (isAISpeakingRef.current) {
      if (currentAudioRef.current) { currentAudioRef.current.pause(); currentAudioRef.current = null; }
      isAISpeakingRef.current = false;
    }

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      const t = window.prompt('Type what you want to say:');
      if (t) handleCallSpeech(t);
      return;
    }

    const rec = new SR();
    rec.lang = 'en-IN';
    rec.continuous = false;
    rec.interimResults = false;
    rec.onstart = () => {
      setMicOn(true);
      setCS('🎤 Listening...', '#FF8080');
      setCallIcon('🎤');
    };
    rec.onresult = (e) => {
      const t = e.results[0][0].transcript;
      const confidence = e.results[0][0].confidence;
      setMicOn(false);
      if (confidence >= 0.5 && t.trim().length > 0) {
        handleCallSpeech(t);
      }
    };
    rec.onerror = () => {
      setMicOn(false);
      const t = window.prompt('Mic unavailable — type:');
      if (t) handleCallSpeech(t);
    };
    rec.onend = () => setMicOn(false);

    recognitionRef.current = rec;
    rec.start();
  }, [micOn, currentAudioRef, handleCallSpeech, setCS]);

  const endCall = useCallback(() => {
    setMicOn(false);
    try { recognitionRef.current?.stop(); } catch {}
    if (currentAudioRef.current) { currentAudioRef.current.pause(); currentAudioRef.current = null; }
    onClose();
  }, [onClose, currentAudioRef]);

  useEffect(() => {
    let d = 0;
    setCallIcon('📱');
    setCS('Dialling (289) 499-1000...', 'var(--mu)');
    const dialInterval = setInterval(() => {
      d = (d + 1) % 4;
      setCS('Dialling (289) 499-1000' + '...'.slice(0, d + 1), 'var(--mu)');
    }, 400);

    const ringTimeout = setTimeout(() => {
      clearInterval(dialInterval);
      setCS('🔔 Ringing...', 'var(--gold)');
      setCallIcon('📳');
    }, 1800);

    const connectTimeout = setTimeout(() => {
      setCS('Connected — Riya answering', 'var(--green)');
      setShowLog(true);
      setCallIcon('🔊');
      setConnected(true);
      callSpeak('Hey, Desi Road! What can I get you today?');
    }, 3200);

    return () => {
      clearInterval(dialInterval);
      clearTimeout(ringTimeout);
      clearTimeout(connectTimeout);
    };
  }, []);

  return (
    <div className="call-modal" data-testid="call-modal" onClick={(e) => { if (e.target === e.currentTarget) endCall(); }}>
      <div className="call-box">
        <div className="call-icon">{callIcon}</div>
        <div className="call-title">Desi Road AI</div>
        <div className="call-subtitle">(437) 331-5615 · Powered by Zivio</div>
        <div className="call-status" style={{ color: statusColor }} data-testid="call-status">{status}</div>

        {showRipple && (
          <div className="call-ripple">
            {[0, 1, 2, 3, 4].map(i => <div key={i} className="call-ripple-bar" />)}
          </div>
        )}

        {showLog && (
          <div className="call-log" data-testid="call-log">
            {logs.map(l => (
              <div key={l.id} className={`call-log-entry ${l.role === 'ai' ? 'ai' : 'caller'}`}>
                <span className="label">{l.role === 'ai' ? 'RIYA — DESI ROAD' : 'YOU'}</span>
                {l.text}
              </div>
            ))}
          </div>
        )}

        <div className="call-buttons">
          <button
            className={`call-mic-btn${micOn ? ' active' : ''}`}
            data-testid="call-mic-btn"
            onClick={toggleMic}
          >
            {micOn ? <MicOff size={22} /> : <Mic size={22} />}
          </button>
          <button className="call-end-btn" data-testid="call-end-btn" onClick={endCall}>
            <PhoneOff size={18} />
          </button>
        </div>
        <div className="call-hint">Tap mic to speak · End to disconnect</div>
      </div>
    </div>
  );
}
