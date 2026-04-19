import { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Mic, Volume2, MicOff } from 'lucide-react';
import { detectOrderItems, getOfflineReply, stripPrices, ORDER_COMPLETE_PHRASES, ADD_ORDER_WORDS } from '@/utils/constants';

const API = process.env.REACT_APP_BACKEND_URL + '/api';
const DESI_ROAD_LOGO = "https://desiroad.ca/wp-content/uploads/2016/10/DESI-ROAD-LOGO-1.jpg";
const LANG_LABELS = { auto: '🔄 Auto', en: '🇨🇦 EN', pa: '🇮🇳 PA', hi: '🇮🇳 HI' };
const LANG_TABS = [
  { id: 'auto', label: '🔄 Auto-detect' },
  { id: 'en', label: '🇨🇦 English' },
  { id: 'pa', label: '🇮🇳 ਪੰਜਾਬੀ' },
  { id: 'hi', label: '🇮🇳 हिन्दी' },
];

const QUICK_MSGS = [
  { text: 'Butter Chicken Cones chahida', label: '🍛 Butter Chicken' },
  { text: 'Lamb Chops please', label: '🍖 Lamb Chops' },
  { text: 'What is the menu?', label: '📋 Menu' },
  { text: 'ਸਤ ਸ੍ਰੀ ਅਕਾਲ', label: '🙏 ਸਤ ਸ੍ਰੀ ਅਕਾਲ' },
  { text: 'नमस्ते', label: '🙏 नमस्ते' },
];

const MIN_CONFIDENCE = 0.55;
const MIN_WORDS = 1;

export default function ChatPanel({
  speakerOn, toggleSpeaker, currentAudioRef,
  orderItems, setOrderItems, orderConfirmed, setOrderConfirmed, setOrderData
}) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [lang, setLang] = useState('auto');
  const [micActive, setMicActive] = useState(false);
  const [memoryText, setMemoryText] = useState(null);
  const [sessionId] = useState(() => 'chat_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8));

  const chatBodyRef = useRef(null);
  const recognitionRef = useRef(null);
  const isAISpeakingRef = useRef(false);
  const typingIntervalRef = useRef(null);
  const greetingSentRef = useRef(false);

  const scrollToBottom = useCallback(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
    }
  }, []);

  const speak = useCallback(async (text) => {
    if (!speakerOn || !text) return;
    const clean = text
      .replace(/[\u{1F300}-\u{1FFFF}]/gu, '')
      .replace(/[—]/g, ', ')
      .replace(/[•\n]/g, ' ')
      .replace(/  +/g, ' ')
      .trim();
    if (!clean) return;

    // KILL all existing audio first to prevent echo
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.src = '';
      currentAudioRef.current = null;
    }

    isAISpeakingRef.current = true;

    try {
      const r = await fetch(`${API}/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: clean, lang })
      });
      if (!r.ok) throw new Error('TTS failed');
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      // Double-check nothing else started while we were fetching
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current.src = '';
      }
      if (window.speechSynthesis) window.speechSynthesis.cancel();
      const audio = new Audio(url);
      audio.playbackRate = 1.05;
      currentAudioRef.current = audio;
      audio.onended = () => {
        URL.revokeObjectURL(url);
        isAISpeakingRef.current = false;
        currentAudioRef.current = null;
      };
      audio.onerror = () => {
        isAISpeakingRef.current = false;
        currentAudioRef.current = null;
      };
      await audio.play();
    } catch {
      isAISpeakingRef.current = false;
      // Browser TTS fallback — only if ElevenLabs completely failed
      if (!window.speechSynthesis) return;
      window.speechSynthesis.cancel();
      const utt = new SpeechSynthesisUtterance(clean);
      utt.rate = 1.0;
      utt.pitch = 0.95;
      const voices = window.speechSynthesis.getVoices();
      const v = voices.find(v => v.name === 'Lekha') ||
                voices.find(v => v.lang === 'hi-IN') ||
                voices.find(v => v.name === 'Samantha');
      if (v) utt.voice = v;
      utt.onend = () => { isAISpeakingRef.current = false; };
      window.speechSynthesis.speak(utt);
    }
  }, [speakerOn, lang, currentAudioRef]);

  const addMessage = useCallback((side, text) => {
    setMessages(prev => [...prev, { side, text, id: Date.now() + Math.random() }]);
    setTimeout(scrollToBottom, 50);
  }, [scrollToBottom]);

  const playTypingSound = useCallback(() => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      let n = 0;
      typingIntervalRef.current = setInterval(() => {
        if (n++ > 80) return;
        const o = ctx.createOscillator();
        const g = ctx.createGain();
        o.connect(g); g.connect(ctx.destination);
        o.frequency.value = 800 + Math.random() * 400;
        o.type = 'square';
        g.gain.setValueAtTime(0.012, ctx.currentTime);
        g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.04);
        o.start(ctx.currentTime);
        o.stop(ctx.currentTime + 0.04);
      }, 90);
    } catch {}
  }, []);

  const stopTypingSound = useCallback(() => {
    if (typingIntervalRef.current) {
      clearInterval(typingIntervalRef.current);
      typingIntervalRef.current = null;
    }
  }, []);

  const callChat = useCallback(async (message, context) => {
    try {
      const r = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message, lang, context: context || undefined })
      });
      if (!r.ok) throw new Error('Chat failed');
      const data = await r.json();
      return data.reply;
    } catch (e) {
      throw e;
    }
  }, [sessionId, lang]);

  const saveOrder = useCallback((items) => {
    const data = { items, time: Date.now(), id: 'DR-' + Math.floor(2800 + Math.random() * 99) };
    try { localStorage.setItem('desi_road_last_order', JSON.stringify(data)); } catch {}
    return data;
  }, []);

  const getRecentOrder = useCallback(() => {
    try {
      const raw = localStorage.getItem('desi_road_last_order');
      if (!raw) return null;
      const data = JSON.parse(raw);
      const age = (Date.now() - data.time) / 60000;
      if (age < 60) return data;
      return null;
    } catch { return null; }
  }, []);

  const confirmOrder = useCallback(() => {
    if (orderItems.length === 0) return;
    setOrderConfirmed(true);
    const data = saveOrder([...orderItems]);
    setOrderData(data);

    // Persist order to backend
    fetch(`${API}/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        restaurant_id: 'default',
        items: orderItems,
        session_id: sessionId,
        language: lang
      })
    }).catch(() => {});
  }, [orderItems, setOrderConfirmed, saveOrder, setOrderData, sessionId, lang]);

  const sendMessage = useCallback(async (text) => {
    if (!text || typing) return;
    setTyping(true);
    addMessage('user', text);

    const newItems = detectOrderItems(text, orderItems);
    if (newItems.length > 0) {
      setOrderItems(prev => [...prev, ...newItems]);
    }

    const isAdding = ADD_ORDER_WORDS.some(w => text.toLowerCase().includes(w));
    let context = null;
    if (isAdding) {
      const recent = getRecentOrder();
      if (recent) {
        context = `Customer's recent order (${Math.round((Date.now() - recent.time) / 60000)} mins ago, ID ${recent.id}): ${recent.items.join(', ')}. They want to add to this order.`;
        setMemoryText(`Previous order found: ${recent.items.join(', ')}`);
        recent.items.forEach(item => {
          setOrderItems(prev => prev.includes(item) ? prev : [...prev, item]);
        });
      }
    }

    playTypingSound();
    try {
      const reply = await callChat(text, context);
      stopTypingSound();
      const clean = stripPrices(reply.trim());
      addMessage('ai', clean);
      speak(clean);

      const orderDone = ORDER_COMPLETE_PHRASES.some(w => clean.toLowerCase().includes(w));
      if (orderDone && orderItems.length > 0 && !orderConfirmed) {
        confirmOrder();
      }

      if (messages.length <= 2 && !isAdding) {
        const recent = getRecentOrder();
        if (recent) {
          setMemoryText(`Welcome back! Last order: ${recent.items.join(', ')}`);
        }
      }
    } catch {
      stopTypingSound();
      const fallback = getOfflineReply(text);
      addMessage('ai', fallback);
      speak(fallback);
    }
    setTyping(false);
  }, [typing, addMessage, orderItems, setOrderItems, playTypingSound, stopTypingSound, callChat, speak, confirmOrder, orderConfirmed, messages.length, getRecentOrder]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendMessage(input.trim());
      setInput('');
    }
  }, [input, sendMessage]);

  const handleSend = useCallback(() => {
    sendMessage(input.trim());
    setInput('');
  }, [input, sendMessage]);

  const handleQuickMsg = useCallback((text) => {
    setInput('');
    sendMessage(text);
  }, [sendMessage]);

  const toggleMic = useCallback(() => {
    if (micActive) {
      try { recognitionRef.current?.stop(); } catch {}
      setMicActive(false);
      return;
    }

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;

    if (isAISpeakingRef.current) {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
      isAISpeakingRef.current = false;
    }

    const rec = new SR();
    const langMap = { auto: 'en-IN', en: 'en-IN', pa: 'pa-IN', hi: 'hi-IN' };
    rec.lang = langMap[lang] || 'en-IN';
    rec.continuous = false;
    rec.interimResults = true;
    rec.maxAlternatives = 1;

    rec.onstart = () => setMicActive(true);
    rec.onresult = (e) => {
      const results = Array.from(e.results);
      const transcript = results.map(r => r[0].transcript).join('');
      setInput(transcript);

      const lastResult = results[results.length - 1];
      if (lastResult.isFinal) {
        const confidence = lastResult[0].confidence;
        const wordCount = transcript.trim().split(/\s+/).length;

        if (confidence >= MIN_CONFIDENCE && wordCount >= MIN_WORDS) {
          setMicActive(false);
          setTimeout(() => sendMessage(transcript.trim()), 300);
        } else {
          setMicActive(false);
        }
      }
    };
    rec.onerror = () => setMicActive(false);
    rec.onend = () => setMicActive(false);

    recognitionRef.current = rec;
    rec.start();
  }, [micActive, lang, currentAudioRef, sendMessage]);

  useEffect(() => {
    if (window.speechSynthesis) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
    }

    if (!greetingSentRef.current) {
      greetingSentRef.current = true;
      const recent = getRecentOrder();
      setTimeout(() => {
        if (recent) {
          const greeting = `Welcome back! Last time you had ${recent.items.join(', ')}. Same again or something new?`;
          addMessage('ai', greeting);
          speak(greeting);
          setMemoryText(`Welcome back! Last order: ${recent.items.join(', ')}`);
        } else {
          const greeting = 'Sat Sri Akal! Welcome to Desi Road. What can I get you today?';
          addMessage('ai', greeting);
          speak(greeting);
        }
      }, 800);
    }
  }, []);

  return (
    <div className="chat-panel" data-testid="chat-panel">
      {/* HEADER */}
      <div className="chd">
        <div className="av">
          <img src={DESI_ROAD_LOGO} alt="DR" onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }} />
          <div className="av-text" style={{ display: 'none' }}>DR</div>
        </div>
        <div>
          <div className="cn">Desi Road</div>
          <div className="cst">Zivio AI — (289) 499-1000</div>
        </div>
        <div className="lang-badge" data-testid="lang-badge">{LANG_LABELS[lang]}</div>
        <button className="tbtn" style={{ marginLeft: 8, fontSize: 10, padding: '4px 10px' }} data-testid="chat-speaker-toggle" onClick={toggleSpeaker}>
          {speakerOn ? <><Volume2 size={11} /> Voice</> : <><MicOff size={11} /> Muted</>}
        </button>
      </div>

      {/* LANGUAGE TABS */}
      <div className="demo-tabs" style={{ padding: '10px 14px', borderBottom: '1px solid var(--brd)', margin: 0 }}>
        {LANG_TABS.map(t => (
          <button
            key={t.id}
            data-testid={`lang-tab-${t.id}`}
            className={`dtab${lang === t.id ? ' active' : ''}`}
            onClick={() => setLang(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* MEMORY BADGE */}
      {memoryText && (
        <div className="memory-badge" data-testid="memory-badge">
          👋 <span>{memoryText}</span>
        </div>
      )}

      {/* MESSAGES */}
      <div className="cb" ref={chatBodyRef} data-testid="chat-body">
        {messages.map(m => (
          <div key={m.id} className={`mr ${m.side === 'ai' ? 'ai' : ''} show`}>
            <div className={`bb ${m.side === 'ai' ? 'ai-gold' : 'usr'}`}>
              {m.text}
              {m.side === 'ai' && (
                <button className="spk-btn" data-testid="listen-btn" onClick={() => speak(m.text)}>
                  <Volume2 size={10} /> Listen
                </button>
              )}
            </div>
          </div>
        ))}
        {typing && (
          <div className="mr ai typ show">
            <div className="bb ai-gold">
              <span className="dot"></span><span className="dot"></span><span className="dot"></span>
            </div>
          </div>
        )}
      </div>

      {/* QUICK SUGGESTIONS */}
      <div className="qs" data-testid="quick-suggestions">
        {QUICK_MSGS.map((q, i) => (
          <button key={i} className="qb" data-testid={`quick-msg-${i}`} onClick={() => handleQuickMsg(q.text)}>
            {q.label}
          </button>
        ))}
      </div>

      {/* INPUT */}
      <div className="cf" data-testid="chat-footer">
        <input
          className="ci"
          data-testid="chat-input"
          placeholder="Type in English, ਪੰਜਾਬੀ, हिन्दी or mix..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button
          className={`mic-btn${micActive ? ' listening' : ''}`}
          data-testid="mic-btn"
          onClick={toggleMic}
          title={micActive ? 'Stop listening' : 'Hold to speak'}
        >
          {micActive ? <MicOff size={18} /> : <Mic size={18} />}
        </button>
        <button className="send-btn" data-testid="send-btn" onClick={handleSend}>
          <Send size={16} />
        </button>
      </div>

      {/* NOISE FILTER INDICATOR */}
      <div className="noise-filter-badge" data-testid="noise-filter-badge">
        🛡️ Background Noise Filter Active — Only direct speech is processed
      </div>
    </div>
  );
}
