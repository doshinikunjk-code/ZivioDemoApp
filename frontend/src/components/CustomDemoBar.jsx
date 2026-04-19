import { useState, useCallback } from 'react';
import { Sparkles, ArrowRight, RotateCcw } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

export default function CustomDemoBar({ onApplied }) {
  const [name, setName] = useState('');
  const [applying, setApplying] = useState(false);
  const [applied, setApplied] = useState(false);

  const applyCustom = useCallback(async () => {
    if (!name.trim()) return;
    setApplying(true);
    try {
      await fetch(`${API}/restaurant/default`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim() })
      });
      setApplied(true);
      if (onApplied) onApplied(name.trim());
    } catch {}
    setApplying(false);
  }, [name, onApplied]);

  const resetToDefault = useCallback(async () => {
    setApplying(true);
    try {
      await fetch(`${API}/restaurant/default`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: "Desi Road Restaurant" })
      });
      setApplied(false);
      setName('');
      if (onApplied) onApplied("Desi Road Restaurant");
    } catch {}
    setApplying(false);
  }, [onApplied]);

  const handleKey = (e) => {
    if (e.key === 'Enter') applyCustom();
  };

  return (
    <div className="custom-demo-bar" data-testid="custom-demo-bar">
      {!applied ? (
        <>
          <div className="cdb-icon"><Sparkles size={16} /></div>
          <div className="cdb-text">
            <div className="cdb-title">Try with YOUR restaurant</div>
            <div className="cdb-desc">Enter your restaurant name — the AI adapts instantly</div>
          </div>
          <input
            className="cdb-input"
            data-testid="custom-restaurant-input"
            placeholder="Your restaurant name..."
            value={name}
            onChange={e => setName(e.target.value)}
            onKeyDown={handleKey}
          />
          <button
            className="cdb-btn"
            data-testid="apply-custom-btn"
            onClick={applyCustom}
            disabled={applying || !name.trim()}
          >
            {applying ? 'Applying...' : <><ArrowRight size={14} /> Try Now</>}
          </button>
        </>
      ) : (
        <>
          <div className="cdb-icon active"><Sparkles size={16} /></div>
          <div className="cdb-text">
            <div className="cdb-title cdb-active">Now demoing for: {name}</div>
            <div className="cdb-desc">The AI is now answering as your restaurant. Try chatting!</div>
          </div>
          <button className="cdb-reset" data-testid="reset-demo-btn" onClick={resetToDefault} disabled={applying}>
            <RotateCcw size={12} /> Reset to Desi Road
          </button>
        </>
      )}
    </div>
  );
}
