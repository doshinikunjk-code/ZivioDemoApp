export default function ContentScreens({ screen, onNavigate }) {
  const screens = {
    problem: <ProblemScreen onNavigate={onNavigate} />,
    solution: <SolutionScreen onNavigate={onNavigate} />,
    features: <FeaturesScreen />,
    compare: <CompareScreen />,
    kitchen: <KitchenScreen />,
    campaign: <CampaignScreen />,
    pricing: <PricingScreen />,
    start: <StartScreen onNavigate={onNavigate} />,
  };
  return <div className="screen show" data-testid={`screen-${screen}`}>{screens[screen] || null}</div>;
}

function ProblemScreen({ onNavigate }) {
  return (
    <>
      <div className="ph-eyebrow">Step 1 — The Opportunity</div>
      <div className="ph-h">Desi Road is losing orders<br /><em>every single night.</em></div>
      <div className="ph-s">When the phone rings at 10pm and the kitchen is busy. When a Punjabi customer WhatsApps and gets no reply until morning. Every missed contact is a lost table — and lost revenue that never comes back.</div>
      <div className="stats">
        <div className="stat red"><div className="sv">73%</div><div className="sl">Never call back if nobody answers first time</div></div>
        <div className="stat gold"><div className="sv">10pm</div><div className="sl">Peak hour when orders are lost to voicemail</div></div>
        <div className="stat red"><div className="sv">30%</div><div className="sl">Commission Uber Eats takes per order, forever</div></div>
        <div className="stat gold"><div className="sv">$0</div><div className="sl">Revenue from Punjabi customers who got no reply</div></div>
      </div>
      <div className="sd">What is happening right now at Desi Road</div>
      <div className="flow">
        <FlowItem icon="📞" title="Phone rings at 10pm" desc="Staff are busy. Nobody answers. Customer calls a different restaurant." />
        <FlowItem icon="💬" title="WhatsApp at 9pm — no reply" desc="Sits unread overnight. Customer orders Uber Eats — Uber keeps 30%." />
        <FlowItem icon="🗣️" title="Punjabi customer messages" desc="No Punjabi-speaking staff at that hour. Customer never hears back." />
        <FlowItem icon="🔄" title="Regular customer orders every Friday" desc="Has to repeat his full order every single time. No recognition." />
      </div>
      <div className="btn-row"><button className="btn btn-gold" data-testid="see-solution-btn" onClick={() => onNavigate('solution')}>See what Zivio does →</button></div>
    </>
  );
}

function SolutionScreen({ onNavigate }) {
  return (
    <>
      <div className="ph-eyebrow">Step 2 — The Solution</div>
      <div className="ph-h">Every order. Every language.<br /><em>Every hour.</em></div>
      <div className="ph-s">Your existing WhatsApp number and phone line — completely unchanged. Zivio AI handles everything silently behind it, 24 hours a day.</div>
      <div className="stats">
        <div className="stat green"><div className="sv">24/7</div><div className="sl">Orders taken — midnight, Sunday, Diwali, Christmas</div></div>
        <div className="stat gold"><div className="sv">3</div><div className="sl">Languages — English, Punjabi, Hindi — auto-detected</div></div>
        <div className="stat green"><div className="sv">20+</div><div className="sl">Simultaneous conversations handled at once</div></div>
        <div className="stat gold"><div className="sv">$0</div><div className="sl">Commission per order — flat fee only, forever</div></div>
      </div>
      <div className="sd">How it works at Desi Road</div>
      <div className="flow">
        <FlowItem num="1" title="Customer contacts Desi Road — same number as always" desc="WhatsApp or phone on (289) 499-1000. Nothing changes for the customer." />
        <FlowItem num="2" title="AI detects language and responds instantly" desc="Punjabi → Punjabi. Hindi → Hindi. English → English. Mixed → matched naturally." />
        <FlowItem num="3" title="Takes the full order and confirms" desc="Remembers returning customers. Family can add items freely." />
        <FlowItem num="4" title="Order goes to kitchen instantly" desc="Full formatted ticket sent to kitchen phone or receipt printer." />
        <FlowItem num="5" title="Customer arrives — pays — you keep 100%" desc="No app. No website. No commission. Zero." />
      </div>
      <div className="btn-row"><button className="btn btn-gold" data-testid="see-demo-btn" onClick={() => onNavigate('demo')}>See it live →</button></div>
    </>
  );
}

function FeaturesScreen() {
  const features = [
    { icon: '📞', title: '24/7 Phone Ordering', desc: 'AI voice answers in 2 rings. Takes full order, confirms. Even at 2am.', tag: 'Voice AI' },
    { icon: '💬', title: 'WhatsApp Ordering', desc: 'On your existing number. Customers text the same number they always have.', tag: 'Existing Number' },
    { icon: '🗣️', title: '3 Languages Auto-detect', desc: 'English, Punjabi, Hindi + code-switching. Auto-detected on every message.', tag: 'Brampton-ready' },
    { icon: '🧠', title: 'Customer Memory', desc: '"Welcome back Raj ji! Same as usual?" One-tap reorder after 3rd visit.', tag: 'Loyalty' },
    { icon: '📦', title: 'Add to Existing Order', desc: 'Customer calls back within 60 mins — AI knows their order and adds items.', tag: 'Smart Orders' },
    { icon: '🔔', title: 'Kitchen Alerts Instant', desc: 'Every confirmed order to kitchen WhatsApp or receipt printer in 3 seconds.', tag: 'Kitchen' },
    { icon: '✅', title: 'Order Ready Notification', desc: 'Food ready → AI messages customer instantly. Zero wait frustration.', tag: 'Zero Wait' },
    { icon: '📢', title: 'Daily Special Campaigns', desc: '11am every day: AI broadcasts today\'s special to 300+ subscribers.', tag: 'Marketing' },
    { icon: '⭐', title: 'Google Review Automation', desc: 'Happy customer → review request. Unhappy → owner alert before complaint.', tag: 'Reputation' },
  ];
  return (
    <>
      <div className="ph-eyebrow">Complete Feature Set</div>
      <div className="ph-h">Everything included.<br /><em>One flat price. Forever.</em></div>
      <div className="ph-s">Every feature below is in your $799/month. No per-order fees. No commissions. No hidden charges.</div>
      <div className="fg">
        {features.map((f, i) => (
          <div className="fc" key={i} data-testid={`feature-card-${i}`}>
            <div className="fc-icon">{f.icon}</div>
            <div className="fc-title">{f.title}</div>
            <div className="fc-desc">{f.desc}</div>
            <div className="fc-tag">{f.tag}</div>
          </div>
        ))}
      </div>
    </>
  );
}

function CompareScreen() {
  const rows = [
    ['Monthly fee', '$0', '$0', '$799 flat', true],
    ['Commission per order', '25–35%', '25–30%', '0%', true],
    ['$35 order — you keep', '~$24', '~$25', '$35.00', true],
    ['You own the customer', '✗', '✗', '✓', true],
    ['Punjabi / Hindi support', '✗', '✗', '✓', true],
    ['Returning customer memory', '✗', '✗', '✓', true],
    ['24/7 phone ordering', '✗', '✗', '✓', true],
    ['Break-even at', '—', '—', '~27 orders/month', true, true],
  ];
  return (
    <>
      <div className="ph-eyebrow">The Honest Numbers</div>
      <div className="ph-h">Uber Eats is taking<br /><em>thousands from Desi Road.</em></div>
      <div className="ph-s">Every month. Every order. Silently. The commission math is brutal.</div>
      <table className="ct" data-testid="compare-table">
        <thead><tr><th>Feature</th><th>Uber Eats</th><th>DoorDash</th><th>Zivio ✓</th></tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className={r[5] ? 'hl' : ''}>
              <td>{r[0]}</td>
              <td className={!r[3] ? '' : 'no'}>{r[1]}</td>
              <td className={!r[3] ? '' : 'no'}>{r[2]}</td>
              <td className="yes">{r[3] === true ? r[3] : r[3]}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

function KitchenScreen() {
  return (
    <>
      <div className="ph-eyebrow">Kitchen Alert System</div>
      <div className="ph-h">Every order to the kitchen<br /><em>in under 3 seconds.</em></div>
      <div className="ph-s">The moment a customer confirms, the kitchen receives a fully formatted ticket. Zero manual entry. Zero missed orders.</div>
      <div className="flow">
        <FlowItem icon="📱" title="WhatsApp to kitchen phone" desc="Full ticket instantly. Clear, unambiguous, no errors." />
        <FlowItem icon="🖨️" title="Bluetooth receipt printer" desc="$45 one-time hardware. Order prints automatically." />
        <FlowItem icon="✅" title="Order ready → customer alert" desc='AI messages customer: "Your order is ready at Desi Road!"' />
        <FlowItem icon="📋" title="Full order log" desc="Every order stored — time, items, language, returning flag." />
      </div>
    </>
  );
}

function CampaignScreen() {
  return (
    <>
      <div className="ph-eyebrow">Daily Special Campaigns</div>
      <div className="ph-h">One message.<br /><em>300 customers. 40 orders.</em></div>
      <div className="ph-s">Every day at 11am, Zivio broadcasts Desi Road's daily special to the full subscriber list — in all 3 languages simultaneously.</div>
      <div className="stats">
        <div className="stat gold"><div className="sv">284</div><div className="sl">Subscribers receiving the broadcast</div></div>
        <div className="stat green"><div className="sv">47</div><div className="sl">Orders in 2 hours of one broadcast</div></div>
        <div className="stat gold"><div className="sv">$1,034</div><div className="sl">Revenue from a single automated message</div></div>
        <div className="stat green"><div className="sv">$7.10</div><div className="sl">Total cost for that broadcast</div></div>
      </div>
    </>
  );
}

function PricingScreen() {
  return (
    <>
      <div className="ph-eyebrow">Pricing & Guarantee</div>
      <div className="ph-h">One price. Everything.<br /><em>Zero risk.</em></div>
      <div className="price-card" data-testid="pricing-card">
        <div className="price-amount">$799</div>
        <div className="price-period">/month CAD · First month completely free · No contract</div>
        <ul className="price-items">
          <li>Full setup and configuration — included free</li>
          <li>WhatsApp on Desi Road's existing number</li>
          <li>24/7 phone voice agent on (289) 499-1000</li>
          <li>English + Punjabi + Hindi + code-switching</li>
          <li>Customer memory + returning customer recognition</li>
          <li>Add-to-existing-order within 60 minutes</li>
          <li>Kitchen alert system</li>
          <li>Daily special campaigns</li>
          <li>Google review automation</li>
          <li>Commission per order — $0 forever</li>
        </ul>
      </div>
      <div className="guarantee" data-testid="guarantee-section">
        <div className="guarantee-title">🛡️ The Zivio 30-Day Guarantee</div>
        <p style={{ fontSize: 13, color: 'var(--mu)', lineHeight: 1.6 }}>If Zivio does not generate more in recovered orders and saved commission than $799 in your first 30 days — we refund every dollar. No questions. The first month is free anyway. We take all the risk.</p>
      </div>
    </>
  );
}

function StartScreen({ onNavigate }) {
  return (
    <>
      <div className="ph-eyebrow">Let's Get Started</div>
      <div className="ph-h">Desi Road goes live<br /><em>in 5 days.</em></div>
      <div className="ph-s">No payment. No technical work from you or your team. Nik handles everything.</div>
      <div className="flow">
        <FlowItem num="1" title="Today — Handshake. Zero payment." desc="Nik needs: your WhatsApp number, a copy of your menu, and 1 hour this week." />
        <FlowItem num="2" title="Day 1–2 — Nik builds the full system" desc="Menu configured in 3 languages. WhatsApp connected. Phone set up. Kitchen alerts ready." />
        <FlowItem num="3" title="Day 3 — Live test together at Desi Road" desc="Order in Punjabi. Call the number. Confirm a kitchen alert. Staff briefed in 10 minutes." />
        <FlowItem num="4" title="Day 5 — Go live. Orders start." desc="Every missed call, every WhatsApp at 10pm, every Punjabi customer — answered." />
        <FlowItem num="5" title="Day 30 — Review results. Pay only if it worked." desc="If the numbers don't justify $799 — full refund, no argument." />
      </div>
      <div className="btn-row"><button className="btn btn-gold" data-testid="try-demo-btn" onClick={() => onNavigate('demo')}>Try the Demo →</button></div>
    </>
  );
}

function FlowItem({ icon, num, title, desc }) {
  return (
    <div className="fs">
      <div className="fn">{num || icon}</div>
      <div>
        <div className="ft">{title}</div>
        <div className="fd">{desc}</div>
      </div>
    </div>
  );
}
