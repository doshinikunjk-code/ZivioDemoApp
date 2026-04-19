import { useCallback } from 'react';
import { ShoppingCart, Check, Bell } from 'lucide-react';

export default function OrderPanel({
  orderItems, orderConfirmed, setOrderConfirmed, orderData, setOrderData, setOrderItems
}) {
  const saveOrder = useCallback((items) => {
    const data = { items, time: Date.now(), id: 'DR-' + Math.floor(2800 + Math.random() * 99) };
    try { localStorage.setItem('desi_road_last_order', JSON.stringify(data)); } catch {}
    return data;
  }, []);

  const confirmOrder = useCallback(() => {
    if (orderItems.length === 0) return;
    setOrderConfirmed(true);
    const data = saveOrder([...orderItems]);
    setOrderData(data);
  }, [orderItems, setOrderConfirmed, saveOrder, setOrderData]);

  return (
    <div className="order-panel" data-testid="order-panel">
      <div className="op-head">
        <div className="op-title">Current Order</div>
        <div className={`op-status${orderConfirmed ? ' active' : ''}`} data-testid="order-status">
          {orderConfirmed ? <>
            <Check size={10} style={{ marginRight: 3 }} /> Confirmed
          </> : 'Waiting'}
        </div>
      </div>

      <div className="op-body" data-testid="order-body">
        {orderItems.length === 0 ? (
          <div className="op-empty">
            <div className="op-empty-icon"><ShoppingCart size={28} strokeWidth={1.5} /></div>
            <div>Your order will appear here as you chat</div>
          </div>
        ) : (
          orderItems.map((item, i) => (
            <div className="order-item" key={i} data-testid={`order-item-${i}`}>
              <div className="oi-name">{item}</div>
              <div className="oi-qty">x1</div>
            </div>
          ))
        )}
      </div>

      {/* TICKET */}
      {orderConfirmed && orderData && (
        <div className="ticket-wrap" data-testid="order-ticket">
          <div className="t-hd">
            <div>
              <div className="t-title">Order {orderData.id} — Desi Road</div>
              <div className="t-sub-info">Pickup · Est ready in ~20 mins · 185 Fletchers Creek Blvd</div>
            </div>
            <span className="t-badge">⏳ Preparing</span>
          </div>
          <div className="t-items">
            {orderData.items.map((item, i) => <div key={i}>• {item}</div>)}
          </div>
          <div className="t-k">
            <Bell size={13} /> <strong>Kitchen alert sent instantly</strong>
          </div>
        </div>
      )}

      {/* CONFIRM BUTTON */}
      {orderItems.length > 0 && !orderConfirmed && (
        <div className="op-footer" data-testid="order-footer">
          <button className="op-confirm" data-testid="confirm-order-btn" onClick={confirmOrder}>
            <Check size={14} style={{ marginRight: 4 }} /> Confirm Order
          </button>
        </div>
      )}
    </div>
  );
}
