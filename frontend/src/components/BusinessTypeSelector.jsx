import { useState, useCallback } from 'react';
import { Loader2, Check } from 'lucide-react';
import { BUSINESS_TYPE_LIST } from '@/utils/businessTemplates';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

export default function BusinessTypeSelector({ onApplied, activeType }) {
  const [applying, setApplying] = useState(null);

  const applyTemplate = useCallback(async (template) => {
    setApplying(template.type);
    try {
      await fetch(`${API}/restaurant/default`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(template.config)
      });
      if (onApplied) onApplied(template.type);
    } catch (e) {
      console.error('Template apply error:', e);
    }
    setApplying(null);
  }, [onApplied]);

  return (
    <div className="screen show" data-testid="business-type-selector">
      <div className="ph-eyebrow">Business Templates</div>
      <div className="ph-h">One click. <em>Their business.</em></div>
      <div className="ph-s">Select a business type below — the entire demo instantly transforms with their industry, services, pricing, and presentation. Walk into any business pitch-ready.</div>

      <div className="bts-grid" data-testid="bts-grid">
        {BUSINESS_TYPE_LIST.map(t => (
          <button
            key={t.type}
            className={`bts-card${activeType === t.type ? ' active' : ''}`}
            data-testid={`bts-${t.type}`}
            onClick={() => applyTemplate(t)}
            disabled={applying !== null}
          >
            <div className="bts-icon">{t.icon}</div>
            <div className="bts-label">{t.label}</div>
            <div className="bts-name">{t.config.name}</div>
            {applying === t.type && <div className="bts-loading"><Loader2 size={16} className="spin" /></div>}
            {activeType === t.type && applying !== t.type && <div className="bts-active"><Check size={14} /> Active</div>}
          </button>
        ))}
      </div>

      {activeType && (
        <div className="bts-hint">
          Demo is now configured for <strong>{BUSINESS_TYPE_LIST.find(t => t.type === activeType)?.label}</strong>. Navigate to any screen to see the tailored presentation.
        </div>
      )}
    </div>
  );
}
