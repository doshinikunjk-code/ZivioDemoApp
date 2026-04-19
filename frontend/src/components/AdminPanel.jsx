import { useState, useEffect, useCallback } from 'react';
import { Save, Plus, Trash2, Send, TestTube, Loader2 } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';
const EL_DEFAULT_VOICE = 'mActWQg9kibLro6Z2ouY';

export default function AdminPanel() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [newItem, setNewItem] = useState({ name: '', price: '', category: 'main' });
  const [waStatus, setWaStatus] = useState(null);

  const fetchConfig = useCallback(async () => {
    try {
      const r = await fetch(`${API}/restaurant/default`);
      const data = await r.json();
      setConfig(data);
      const ws = await fetch(`${API}/whatsapp/status?restaurant_id=default`);
      setWaStatus(await ws.json());
    } catch { setMessage('Failed to load config'); }
    setLoading(false);
  }, []);

  useEffect(() => { fetchConfig(); }, [fetchConfig]);

  const updateField = (field, value) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  const addMenuItem = () => {
    if (!newItem.name || !newItem.price) return;
    const item = { name: newItem.name, price: parseFloat(newItem.price), category: newItem.category };
    setConfig(prev => ({ ...prev, menu: [...(prev.menu || []), item] }));
    setNewItem({ name: '', price: '', category: 'main' });
  };

  const removeMenuItem = (index) => {
    setConfig(prev => ({ ...prev, menu: prev.menu.filter((_, i) => i !== index) }));
  };

  const saveConfig = async () => {
    setSaving(true);
    setMessage('');
    try {
      const r = await fetch(`${API}/restaurant/default`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      if (r.ok) {
        setMessage('Configuration saved successfully!');
        setTimeout(() => setMessage(''), 3000);
      } else {
        setMessage('Failed to save');
      }
    } catch { setMessage('Error saving config'); }
    setSaving(false);
  };

  const testKitchenAlert = async () => {
    try {
      await fetch(`${API}/alerts/kitchen/test?restaurant_id=default`, { method: 'POST' });
      setMessage('Kitchen test alert sent!');
      setTimeout(() => setMessage(''), 3000);
    } catch { setMessage('Failed to send test alert'); }
  };

  const testReceptionAlert = async () => {
    try {
      await fetch(`${API}/alerts/reception/test?restaurant_id=default`, { method: 'POST' });
      setMessage('Reception test alert sent!');
      setTimeout(() => setMessage(''), 3000);
    } catch { setMessage('Failed to send test alert'); }
  };

  if (loading) return <div className="screen show" data-testid="admin-loading"><div className="ph-h">Loading configuration...</div></div>;
  if (!config) return <div className="screen show"><div className="ph-h">Failed to load</div></div>;

  return (
    <div className="screen show" data-testid="admin-panel">
      <div className="ph-eyebrow">Restaurant Configuration</div>
      <div className="ph-h">Customize <em>Your Restaurant</em></div>
      <div className="ph-s">Configure your restaurant details, menu, integrations, and alert numbers. Changes apply instantly to the AI ordering system.</div>

      {message && <div className="admin-msg" data-testid="admin-message">{message}</div>}

      {/* BASIC INFO */}
      <div className="admin-section">
        <div className="admin-section-title">Restaurant Details</div>
        <div className="admin-grid">
          <div className="admin-field">
            <label>Restaurant Name</label>
            <input data-testid="admin-name" value={config.name || ''} onChange={e => updateField('name', e.target.value)} />
          </div>
          <div className="admin-field">
            <label>Tagline</label>
            <input data-testid="admin-tagline" value={config.tagline || ''} onChange={e => updateField('tagline', e.target.value)} />
          </div>
          <div className="admin-field">
            <label>City</label>
            <input data-testid="admin-city" value={config.city || ''} onChange={e => updateField('city', e.target.value)} />
          </div>
          <div className="admin-field">
            <label>Phone Number</label>
            <input data-testid="admin-phone" value={config.phone || ''} onChange={e => updateField('phone', e.target.value)} />
          </div>
          <div className="admin-field full">
            <label>Location / Address</label>
            <input data-testid="admin-location" value={config.location || ''} onChange={e => updateField('location', e.target.value)} />
          </div>
          <div className="admin-field">
            <label>Business Hours</label>
            <input value={config.hours || ''} onChange={e => updateField('hours', e.target.value)} />
          </div>
          <div className="admin-field">
            <label>Logo URL</label>
            <input value={config.logo_url || ''} onChange={e => updateField('logo_url', e.target.value)} />
          </div>
          <div className="admin-field">
            <label>Brand Tagline</label>
            <input value={config.brand_tagline || ''} onChange={e => updateField('brand_tagline', e.target.value)} />
          </div>
          <div className="admin-field">
            <label>Monthly Price</label>
            <input value={config.monthly_price || ''} onChange={e => updateField('monthly_price', e.target.value)} />
          </div>
        </div>
      </div>

      {/* MENU */}
      <div className="admin-section">
        <div className="admin-section-title">Menu Items ({(config.menu || []).length})</div>
        <div className="admin-menu-list">
          {(config.menu || []).map((item, i) => (
            <div className="admin-menu-item" key={i} data-testid={`menu-item-${i}`}>
              <span className="ami-name">{item.name}</span>
              <span className="ami-price">${item.price?.toFixed(2)}</span>
              <span className="ami-cat">{item.category}</span>
              <button className="ami-del" onClick={() => removeMenuItem(i)} data-testid={`menu-del-${i}`}><Trash2 size={12} /></button>
            </div>
          ))}
        </div>
        <div className="admin-menu-add">
          <input placeholder="Item name" value={newItem.name} onChange={e => setNewItem(p => ({ ...p, name: e.target.value }))} data-testid="new-menu-name" />
          <input placeholder="Price" type="number" step="0.01" value={newItem.price} onChange={e => setNewItem(p => ({ ...p, price: e.target.value }))} data-testid="new-menu-price" />
          <select value={newItem.category} onChange={e => setNewItem(p => ({ ...p, category: e.target.value }))}>
            <option value="main">Main</option>
            <option value="starter">Starter</option>
            <option value="bread">Bread</option>
            <option value="drink">Drink</option>
            <option value="dessert">Dessert</option>
          </select>
          <button className="btn btn-gold admin-add-btn" onClick={addMenuItem} data-testid="add-menu-btn"><Plus size={14} /> Add</button>
        </div>
      </div>

      {/* SPECIAL */}
      <div className="admin-section">
        <div className="admin-section-title">Tonight's Special</div>
        <div className="admin-grid">
          <div className="admin-field">
            <label>Special Item</label>
            <input value={config.special_name || ''} onChange={e => updateField('special_name', e.target.value)} data-testid="admin-special" />
          </div>
          <div className="admin-field">
            <label>Description</label>
            <input value={config.special_desc || ''} onChange={e => updateField('special_desc', e.target.value)} />
          </div>
        </div>
      </div>

      {/* TWILIO */}
      <div className="admin-section">
        <div className="admin-section-title">
          WhatsApp Integration (Twilio)
          {waStatus && <span className={`admin-status-pill ${waStatus.configured ? 'active' : ''}`}>{waStatus.configured ? 'Connected' : 'Not Configured'}</span>}
        </div>
        <div className="admin-grid">
          <div className="admin-field">
            <label>Twilio Account SID</label>
            <input value={config.twilio_account_sid || ''} onChange={e => updateField('twilio_account_sid', e.target.value)} placeholder="ACxxxxxxxxxx" data-testid="admin-twilio-sid" />
          </div>
          <div className="admin-field">
            <label>Twilio Auth Token</label>
            <input type="password" value={config.twilio_auth_token || ''} onChange={e => updateField('twilio_auth_token', e.target.value)} placeholder="Your auth token" data-testid="admin-twilio-token" />
          </div>
          <div className="admin-field">
            <label>WhatsApp Number</label>
            <input value={config.twilio_whatsapp_number || ''} onChange={e => updateField('twilio_whatsapp_number', e.target.value)} placeholder="+14155238886" data-testid="admin-twilio-wa" />
          </div>
        </div>
      </div>

      {/* ALERTS */}
      <div className="admin-section">
        <div className="admin-section-title">Alert Numbers</div>
        <div className="admin-grid">
          <div className="admin-field">
            <label>Kitchen Phone (WhatsApp)</label>
            <input value={config.kitchen_phone || ''} onChange={e => updateField('kitchen_phone', e.target.value)} placeholder="+1234567890" data-testid="admin-kitchen-phone" />
          </div>
          <div className="admin-field">
            <label>Reception Phone (WhatsApp)</label>
            <input value={config.reception_phone || ''} onChange={e => updateField('reception_phone', e.target.value)} placeholder="+1234567890" data-testid="admin-reception-phone" />
          </div>
        </div>
        <div className="admin-test-btns">
          <button className="tbtn green" onClick={testKitchenAlert} data-testid="test-kitchen-btn"><TestTube size={12} /> Test Kitchen Alert</button>
          <button className="tbtn green" onClick={testReceptionAlert} data-testid="test-reception-btn"><TestTube size={12} /> Test Reception Alert</button>
        </div>
      </div>

      {/* VOICE CONFIGURATION */}
      <div className="admin-section">
        <div className="admin-section-title">Voice Configuration (ElevenLabs)</div>
        <div className="ph-s" style={{ marginBottom: 12, fontSize: 12, maxWidth: 'none' }}>Set different voice IDs per language. Default voice is used when no language-specific voice is set. To clone a Punjabi voice: go to elevenlabs.io → Voice Lab → Instant Clone → record 30 seconds of Punjabi speech.</div>
        <div className="admin-grid">
          <div className="admin-field">
            <label>Default Voice ID</label>
            <input value={EL_DEFAULT_VOICE} disabled style={{ opacity: 0.6 }} />
          </div>
          <div className="admin-field">
            <label>English Voice ID (optional)</label>
            <input value={(config.voice_ids || {}).en || ''} onChange={e => updateField('voice_ids', { ...(config.voice_ids || {}), en: e.target.value })} placeholder="Use default" data-testid="admin-voice-en" />
          </div>
          <div className="admin-field">
            <label>Hindi Voice ID (optional)</label>
            <input value={(config.voice_ids || {}).hi || ''} onChange={e => updateField('voice_ids', { ...(config.voice_ids || {}), hi: e.target.value })} placeholder="Use default" data-testid="admin-voice-hi" />
          </div>
          <div className="admin-field">
            <label>Punjabi Voice ID (optional)</label>
            <input value={(config.voice_ids || {}).pa || ''} onChange={e => updateField('voice_ids', { ...(config.voice_ids || {}), pa: e.target.value })} placeholder="Clone a Punjabi voice at elevenlabs.io" data-testid="admin-voice-pa" />
          </div>
        </div>
      </div>

      {/* GOOGLE REVIEWS */}
      <div className="admin-section">
        <div className="admin-section-title">Google Review Automation</div>
        <div className="admin-grid">
          <div className="admin-field">
            <label>Google Place ID</label>
            <input value={config.google_place_id || ''} onChange={e => updateField('google_place_id', e.target.value)} placeholder="ChIJ..." data-testid="admin-place-id" />
          </div>
          <div className="admin-field">
            <label>Google Review URL (or auto from Place ID)</label>
            <input value={config.google_review_url || ''} onChange={e => updateField('google_review_url', e.target.value)} placeholder="https://g.page/r/..." data-testid="admin-review-url" />
          </div>
        </div>
      </div>

      {/* SAVE */}
      <div className="admin-save-bar">
        <button className="btn btn-gold admin-save-btn" onClick={saveConfig} disabled={saving} data-testid="admin-save-btn">
          {saving ? <><Loader2 size={14} className="spin" /> Saving...</> : <><Save size={14} /> Save Configuration</>}
        </button>
      </div>
    </div>
  );
}
