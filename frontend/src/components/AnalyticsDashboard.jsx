import { useState, useEffect, useCallback } from 'react';
import { TrendingUp, MessageSquare, ShoppingCart, Star, Bell, Globe, RefreshCw } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

export default function AnalyticsDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = useCallback(async () => {
    try {
      const r = await fetch(`${API}/analytics/summary?restaurant_id=default`);
      const d = await r.json();
      setData(d);
    } catch (e) {
      console.error('Analytics fetch error:', e);
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchAnalytics(); }, [fetchAnalytics]);

  if (loading) return <div className="screen show"><div className="ph-h">Loading analytics...</div></div>;

  return (
    <div className="screen show" data-testid="analytics-dashboard">
      <div className="ph-eyebrow">Performance Dashboard</div>
      <div className="ph-h">Real-Time <em>Analytics</em></div>
      <div className="ph-s">Track orders, conversations, alerts, and revenue across your AI ordering system.</div>

      <button className="tbtn" onClick={() => { setLoading(true); fetchAnalytics(); }} style={{ marginBottom: 20 }} data-testid="refresh-analytics">
        <RefreshCw size={12} style={{ marginRight: 4 }} /> Refresh
      </button>

      {/* STAT CARDS */}
      <div className="stats" data-testid="analytics-stats">
        <StatCard value={data?.total_orders || 0} label="Total Orders" color="green" icon={<ShoppingCart size={18} />} />
        <StatCard value={data?.conversations || 0} label="AI Conversations" color="gold" icon={<MessageSquare size={18} />} />
        <StatCard value={`$${data?.revenue_estimate || 0}`} label="Est. Revenue" color="green" icon={<TrendingUp size={18} />} />
        <StatCard value={data?.messages || 0} label="Messages Exchanged" color="gold" icon={<Globe size={18} />} />
      </div>

      <div className="analytics-grid">
        {/* SECONDARY STATS */}
        <div className="analytics-card" data-testid="secondary-stats">
          <div className="analytics-card-title">System Activity</div>
          <div className="analytics-rows">
            <AnalyticsRow label="WhatsApp Messages Sent" value={data?.whatsapp_sent || 0} icon={<MessageSquare size={14} />} />
            <AnalyticsRow label="Kitchen Alerts Sent" value={data?.kitchen_alerts || 0} icon={<Bell size={14} />} />
            <AnalyticsRow label="Review Requests Sent" value={data?.reviews_requested || 0} icon={<Star size={14} />} />
          </div>
        </div>

        {/* ORDERS BY LANGUAGE */}
        <div className="analytics-card" data-testid="orders-by-language">
          <div className="analytics-card-title">Orders by Language</div>
          {data?.orders_by_language && Object.keys(data.orders_by_language).length > 0 ? (
            <div className="analytics-rows">
              {Object.entries(data.orders_by_language).map(([lang, count]) => (
                <AnalyticsRow key={lang} label={langLabel(lang)} value={count} />
              ))}
            </div>
          ) : (
            <div className="analytics-empty">No orders yet — start taking orders to see language breakdown</div>
          )}
        </div>
      </div>

      {/* RECENT ORDERS */}
      <div className="analytics-card full-width" data-testid="recent-orders">
        <div className="analytics-card-title">Recent Orders</div>
        {data?.recent_orders && data.recent_orders.length > 0 ? (
          <table className="ct">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Items</th>
                <th>Language</th>
                <th>Status</th>
                <th>Kitchen</th>
                <th>Review</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_orders.map((order, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 700, color: 'var(--gold)' }}>{order.id}</td>
                  <td>{(order.items || []).join(', ')}</td>
                  <td>{langLabel(order.language)}</td>
                  <td className={order.status === 'confirmed' ? 'yes' : ''}>{order.status}</td>
                  <td className={order.kitchen_alerted ? 'yes' : 'no'}>{order.kitchen_alerted ? 'Sent' : 'Pending'}</td>
                  <td className={order.review_requested ? 'yes' : 'no'}>{order.review_requested ? 'Sent' : '—'}</td>
                  <td style={{ fontSize: 11, color: 'var(--mu)' }}>{order.created_at ? new Date(order.created_at).toLocaleString() : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="analytics-empty">No orders yet. Orders placed through the demo will appear here.</div>
        )}
      </div>
    </div>
  );
}

function StatCard({ value, label, color, icon }) {
  return (
    <div className={`stat ${color}`} data-testid={`stat-${label.replace(/\s/g, '-').toLowerCase()}`}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, color: 'var(--mu)' }}>{icon}</div>
      <div className="sv">{value}</div>
      <div className="sl">{label}</div>
    </div>
  );
}

function AnalyticsRow({ label, value, icon }) {
  return (
    <div className="analytics-row">
      <span className="analytics-row-label">{icon && <span style={{ marginRight: 6 }}>{icon}</span>}{label}</span>
      <span className="analytics-row-value">{value}</span>
    </div>
  );
}

function langLabel(lang) {
  const map = { en: 'English', pa: 'Punjabi', hi: 'Hindi', auto: 'Auto-detect' };
  return map[lang] || lang || 'Auto';
}
