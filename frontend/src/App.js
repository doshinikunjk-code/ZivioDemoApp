import { useState, useRef, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import ChatPanel from "@/components/ChatPanel";
import OrderPanel from "@/components/OrderPanel";
import CallModal from "@/components/CallModal";
import ContentScreens from "@/components/ContentScreens";
import AdminPanel from "@/components/AdminPanel";
import AnalyticsDashboard from "@/components/AnalyticsDashboard";
import CustomDemoBar from "@/components/CustomDemoBar";
import { Phone, Volume2, VolumeX, Radio } from "lucide-react";

const DESI_ROAD_LOGO = "https://desiroad.ca/wp-content/uploads/2016/10/DESI-ROAD-LOGO-1.jpg";

function ZivioApp() {
  const [activeScreen, setActiveScreen] = useState('demo');
  const [speakerOn, setSpeakerOn] = useState(true);
  const [showCallModal, setShowCallModal] = useState(false);
  const [orderItems, setOrderItems] = useState([]);
  const [orderConfirmed, setOrderConfirmed] = useState(false);
  const [orderData, setOrderData] = useState(null);
  const currentAudioRef = useRef(null);

  const toggleSpeaker = useCallback(() => {
    setSpeakerOn(prev => {
      if (prev && currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
      if (prev && window.speechSynthesis) window.speechSynthesis.cancel();
      return !prev;
    });
  }, []);

  const navItems = [
    { section: 'Presentation' },
    { id: 'problem', label: 'The Problem', color: 'red', icon: '😔' },
    { id: 'solution', label: 'The Solution', color: 'green', icon: '💡' },
    { section: 'Live Demo' },
    { id: 'demo', label: 'AI Ordering Demo', color: 'gold', icon: '💬' },
    { section: 'Business Case' },
    { id: 'features', label: 'All Features', color: 'green', icon: '⚡' },
    { id: 'compare', label: 'vs Uber Eats', color: 'red', icon: '⚖️' },
    { id: 'kitchen', label: 'Kitchen Alerts', color: 'gold', icon: '🔔' },
    { id: 'campaign', label: 'Daily Specials', color: 'gold', icon: '📢' },
    { id: 'pricing', label: 'Pricing', color: 'cream', icon: '💰' },
    { id: 'start', label: 'Get Started', color: 'green', icon: '✅' },
    { section: 'System' },
    { id: 'admin', label: 'Admin Panel', color: 'gold', icon: '⚙️' },
    { id: 'analytics', label: 'Analytics', color: 'green', icon: '📊' },
  ];

  return (
    <div className="zivio-app" data-testid="zivio-app">
      {/* TOPBAR */}
      <div className="topbar" data-testid="topbar">
        <div className="t-brand">
          <img className="t-logo" src={DESI_ROAD_LOGO} alt="Desi Road" onError={e => e.target.style.display = 'none'} />
          <div>
            <div className="t-name">ZIVIO AI</div>
            <div className="t-sub">AI Ordering System — Demo</div>
          </div>
        </div>
        <div className="t-tag">Desi Daru Desi Khana</div>
        <div className="t-right">
          <button className="tbtn green" data-testid="demo-call-btn" onClick={() => setShowCallModal(true)}>
            <Phone size={13} style={{ marginRight: 4 }} /> Demo Call
          </button>
          <button className="tbtn" data-testid="speaker-toggle" onClick={toggleSpeaker}>
            {speakerOn ? <><Volume2 size={13} style={{ marginRight: 4 }} /> Voice</> : <><VolumeX size={13} style={{ marginRight: 4 }} /> Muted</>}
          </button>
          <div className="t-live" data-testid="ai-status">
            <div className="t-dot"></div>
            <Radio size={11} style={{ marginRight: 3 }} /> AI Active
          </div>
        </div>
      </div>

      <div className="layout">
        {/* SIDEBAR */}
        <div className="sidebar" data-testid="sidebar">
          <div className="sb-brand">
            <div className="sb-brand-name">Desi Road Restaurant</div>
            <div className="sb-brand-tag">Elevated Indian Cuisine · Brampton</div>
          </div>
          <div className="sb-inner">
            {navItems.map((item, i) =>
              item.section ? (
                <div className="sb-sec" key={`sec-${i}`}>{item.section}</div>
              ) : (
                <button
                  key={item.id}
                  data-testid={`nav-${item.id}`}
                  className={`nb c-${item.color}${activeScreen === item.id ? ' on' : ''}`}
                  onClick={() => setActiveScreen(item.id)}
                >
                  <span className="ic">{item.icon}</span>{item.label}
                </button>
              )
            )}
          </div>
          <div className="sb-foot">
            <div className="gbox">
              <div className="gbox-t">🛡️ 30-Day Guarantee</div>
              <div className="gbox-b">More orders in Month 1 than the fee — or every dollar back.</div>
            </div>
          </div>
        </div>

        {/* CONTENT */}
        <div className="content" data-testid="content-area">
          {activeScreen === 'demo' && (
            <div className="screen show" data-testid="demo-screen">
              <div className="demo-header">
                <div className="ph-eyebrow">Live Demo — Try It Now</div>
                <div className="ph-h">Your customer. Your number.<br /><em>One AI. Every language.</em></div>
                <div className="ph-s">This is exactly what a customer experiences on WhatsApp or phone. Type in English, Punjabi, Hindi — or mix all three. The AI handles it all, remembers returning customers, and never misses an order.</div>
              </div>
              <CustomDemoBar />
              <div className="chat-wrap">
                <ChatPanel
                  speakerOn={speakerOn}
                  toggleSpeaker={toggleSpeaker}
                  currentAudioRef={currentAudioRef}
                  orderItems={orderItems}
                  setOrderItems={setOrderItems}
                  orderConfirmed={orderConfirmed}
                  setOrderConfirmed={setOrderConfirmed}
                  setOrderData={setOrderData}
                />
                <OrderPanel
                  orderItems={orderItems}
                  orderConfirmed={orderConfirmed}
                  setOrderConfirmed={setOrderConfirmed}
                  orderData={orderData}
                  setOrderData={setOrderData}
                  setOrderItems={setOrderItems}
                />
              </div>
            </div>
          )}
          {activeScreen !== 'demo' && activeScreen !== 'admin' && activeScreen !== 'analytics' && (
            <ContentScreens screen={activeScreen} onNavigate={setActiveScreen} />
          )}
          {activeScreen === 'admin' && <AdminPanel />}
          {activeScreen === 'analytics' && <AnalyticsDashboard />}
        </div>
      </div>

      {/* CALL MODAL */}
      {showCallModal && (
        <CallModal
          onClose={() => setShowCallModal(false)}
          speakerOn={speakerOn}
          currentAudioRef={currentAudioRef}
        />
      )}
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="*" element={<ZivioApp />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
