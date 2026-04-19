import { useState, useRef, useCallback, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import ChatPanel from "@/components/ChatPanel";
import OrderPanel from "@/components/OrderPanel";
import CallModal from "@/components/CallModal";
import ContentScreens from "@/components/ContentScreens";
import AdminPanel from "@/components/AdminPanel";
import AnalyticsDashboard from "@/components/AnalyticsDashboard";
import CustomDemoBar from "@/components/CustomDemoBar";
import BusinessTypeSelector from "@/components/BusinessTypeSelector";
import { BUSINESS_TEMPLATES } from "@/utils/businessTemplates";
import { Phone, Volume2, VolumeX, Radio } from "lucide-react";

const DESI_ROAD_LOGO = "https://desiroad.ca/wp-content/uploads/2016/10/DESI-ROAD-LOGO-1.jpg";

function ZivioApp() {
  const [activeScreen, setActiveScreen] = useState('demo');
  const [speakerOn, setSpeakerOn] = useState(true);
  const [showCallModal, setShowCallModal] = useState(false);
  const [orderItems, setOrderItems] = useState([]);
  const [orderConfirmed, setOrderConfirmed] = useState(false);
  const [orderData, setOrderData] = useState(null);
  const [businessType, setBusinessType] = useState('restaurant');
  const currentAudioRef = useRef(null);

  const bt = BUSINESS_TEMPLATES[businessType] || BUSINESS_TEMPLATES.restaurant;

  // Apply per-template theme (CSS custom properties) to :root so everything re-skins at once
  useEffect(() => {
    const root = document.documentElement;
    const theme = bt.theme || {};
    const touched = Object.keys(theme);
    touched.forEach(k => root.style.setProperty(k, theme[k]));
    return () => {
      // Reset so next template doesn't inherit stale overrides
      touched.forEach(k => root.style.removeProperty(k));
    };
  }, [bt]);

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

  const handleTemplateApplied = useCallback((type) => {
    setBusinessType(type);
    setOrderItems([]);
    setOrderConfirmed(false);
    setOrderData(null);
    setActiveScreen('demo');
  }, []);

  const navItems = [
    { section: 'Presentation' },
    { id: 'problem', label: 'The Problem', color: 'red', icon: '😔' },
    { id: 'solution', label: 'The Solution', color: 'green', icon: '💡' },
    { section: 'Live Demo' },
    { id: 'demo', label: 'AI Demo', color: 'gold', icon: '💬' },
    { section: 'Business Case' },
    { id: 'features', label: 'All Features', color: 'green', icon: '⚡' },
    { id: 'compare', label: 'vs Alternatives', color: 'red', icon: '⚖️' },
    { id: 'kitchen', label: 'Team Alerts', color: 'gold', icon: '🔔' },
    { id: 'campaign', label: 'Campaigns', color: 'gold', icon: '📢' },
    { id: 'pricing', label: 'Pricing', color: 'cream', icon: '💰' },
    { id: 'start', label: 'Get Started', color: 'green', icon: '✅' },
    { section: 'System' },
    { id: 'templates', label: 'Business Templates', color: 'gold', icon: '🏢' },
    { id: 'admin', label: 'Admin Panel', color: 'gold', icon: '⚙️' },
    { id: 'analytics', label: 'Analytics', color: 'green', icon: '📊' },
  ];

  return (
    <div className="zivio-app" data-testid="zivio-app">
      {/* TOPBAR */}
      <div className="topbar" data-testid="topbar">
        <div className="t-brand">
          <img className="t-logo" src={bt.config.logo_url || DESI_ROAD_LOGO} alt="" onError={e => e.target.style.display = 'none'} />
          <div>
            <div className="t-name">ZIVIO AI</div>
            <div className="t-sub">{bt.label} — Demo</div>
          </div>
        </div>
        <div className="t-tag">{bt.config.brand_tagline}</div>
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
            <div className="sb-brand-name">{bt.config.name}</div>
            <div className="sb-brand-tag">{bt.config.tagline} · {bt.config.city}</div>
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
              <div className="gbox-t">30-Day Guarantee</div>
              <div className="gbox-b">More value in Month 1 than the fee — or every dollar back.</div>
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
                <div className="ph-s">This is exactly what a customer experiences on WhatsApp or phone. Type in English, Punjabi, Hindi — or mix all three.</div>
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
                  businessConfig={bt.config}
                  businessQuickMsgs={bt.quickMsgs}
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
          {activeScreen === 'templates' && (
            <BusinessTypeSelector onApplied={handleTemplateApplied} activeType={businessType} />
          )}
          {activeScreen === 'admin' && <AdminPanel />}
          {activeScreen === 'analytics' && <AnalyticsDashboard />}
          {!['demo', 'templates', 'admin', 'analytics'].includes(activeScreen) && (
            <ContentScreens screen={activeScreen} onNavigate={setActiveScreen} businessType={businessType} />
          )}
        </div>
      </div>

      {showCallModal && (
        <CallModal onClose={() => setShowCallModal(false)} speakerOn={speakerOn} currentAudioRef={currentAudioRef} businessConfig={bt.config} />
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
