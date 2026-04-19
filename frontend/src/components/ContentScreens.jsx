import { BUSINESS_TEMPLATES } from '@/utils/businessTemplates';

export default function ContentScreens({ screen, onNavigate, businessType }) {
  const t = BUSINESS_TEMPLATES[businessType || 'restaurant'];
  if (!t) return null;
  const p = t.presentation;
  const name = t.config.name;

  const screens = {
    problem: <ProblemScreen p={p.problem} name={name} onNavigate={onNavigate} />,
    solution: <SolutionScreen p={p.solution} name={name} onNavigate={onNavigate} />,
    features: <FeaturesScreen features={p.features} name={name} price={p.pricing.amount} />,
    compare: <CompareScreen compare={p.compare} name={name} />,
    kitchen: <AlertsScreen name={name} type={businessType} />,
    campaign: <CampaignScreen name={name} type={businessType} />,
    pricing: <PricingScreen pricing={p.pricing} name={name} config={t.config} />,
    start: <StartScreen name={name} onNavigate={onNavigate} />,
  };
  return <div className="screen show" data-testid={`screen-${screen}`}>{screens[screen] || null}</div>;
}

function ProblemScreen({ p, name, onNavigate }) {
  return (
    <>
      <div className="ph-eyebrow">{p.eyebrow}</div>
      <div className="ph-h">{name} {p.title[0]}<br /><em>{p.title[1]}</em></div>
      <div className="ph-s">{p.desc}</div>
      <div className="stats">
        {p.stats.map((s, i) => (
          <div className={`stat ${s.color}`} key={i}><div className="sv">{s.value}</div><div className="sl">{s.label}</div></div>
        ))}
      </div>
      <div className="sd">What is happening right now</div>
      <div className="flow">
        {p.flows.map((f, i) => <FlowItem key={i} icon={f.icon} num={f.num} title={f.title} desc={f.desc} />)}
      </div>
      <div className="btn-row"><button className="btn btn-gold" data-testid="see-solution-btn" onClick={() => onNavigate('solution')}>See the solution →</button></div>
    </>
  );
}

function SolutionScreen({ p, name, onNavigate }) {
  return (
    <>
      <div className="ph-eyebrow">{p.eyebrow}</div>
      <div className="ph-h">{p.title[0]}<br /><em>{p.title[1]}</em></div>
      <div className="ph-s">{p.desc}</div>
      <div className="stats">
        {p.stats.map((s, i) => (
          <div className={`stat ${s.color}`} key={i}><div className="sv">{s.value}</div><div className="sl">{s.label}</div></div>
        ))}
      </div>
      <div className="sd">How it works at {name}</div>
      <div className="flow">
        {p.flows.map((f, i) => <FlowItem key={i} icon={f.icon} num={f.num} title={f.title} desc={f.desc} />)}
      </div>
      <div className="btn-row"><button className="btn btn-gold" data-testid="see-demo-btn" onClick={() => onNavigate('demo')}>See it live →</button></div>
    </>
  );
}

function FeaturesScreen({ features, name, price }) {
  return (
    <>
      <div className="ph-eyebrow">Complete Feature Set</div>
      <div className="ph-h">Everything included.<br /><em>One flat price. Forever.</em></div>
      <div className="ph-s">Every feature below is in your {price}/month. No hidden charges. No per-transaction fees.</div>
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

function CompareScreen({ compare, name }) {
  return (
    <>
      <div className="ph-eyebrow">The Honest Numbers</div>
      <div className="ph-h">See how Zivio compares<br /><em>to the alternatives.</em></div>
      <table className="ct" data-testid="compare-table">
        <thead><tr><th>Feature</th>{compare.competitors.map((c, i) => <th key={i}>{c}</th>)}<th>Zivio</th></tr></thead>
        <tbody>
          {compare.rows.map((r, i) => (
            <tr key={i} className={i === compare.rows.length - 1 ? 'hl' : ''}>
              <td>{r[0]}</td>
              <td className="no">{r[1]}</td>
              <td className="no">{r[2]}</td>
              <td className="yes">{r[3]}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

function AlertsScreen({ name, type }) {
  const isService = ['dentist', 'doctor', 'trades'].includes(type);
  return (
    <>
      <div className="ph-eyebrow">{isService ? 'Team Alert System' : 'Kitchen Alert System'}</div>
      <div className="ph-h">Every {isService ? 'booking' : 'order'} to your team<br /><em>in under 3 seconds.</em></div>
      <div className="ph-s">The moment a {isService ? 'patient confirms' : 'customer confirms'}, your team receives a full alert. Zero manual entry.</div>
      <div className="flow">
        <FlowItem icon="📱" title="WhatsApp to team phone" desc="Full details instantly. Clear and unambiguous." />
        <FlowItem icon="✅" title={isService ? 'Confirmation sent to patient' : 'Ready notification to customer'} desc={`AI messages: "Your ${isService ? 'appointment' : 'order'} at ${name} is confirmed!"`} />
        <FlowItem icon="📋" title="Full log" desc={`Every ${isService ? 'booking' : 'order'} stored — time, details, language, returning flag.`} />
      </div>
    </>
  );
}

function CampaignScreen({ name, type }) {
  const isService = ['dentist', 'doctor', 'pharmacy'].includes(type);
  return (
    <>
      <div className="ph-eyebrow">{isService ? 'Patient Outreach' : 'Daily Campaigns'}</div>
      <div className="ph-h">One message.<br /><em>{isService ? '300 patients. 40 bookings.' : '300 customers. 40 orders.'}</em></div>
      <div className="ph-s">Zivio broadcasts your {isService ? 'health reminders and specials' : 'daily specials'} to your full subscriber list — in all 3 languages.</div>
      <div className="stats">
        <div className="stat gold"><div className="sv">284</div><div className="sl">Subscribers receiving the broadcast</div></div>
        <div className="stat green"><div className="sv">47</div><div className="sl">{isService ? 'Bookings from one broadcast' : 'Orders from one broadcast'}</div></div>
        <div className="stat gold"><div className="sv">$1,034</div><div className="sl">Revenue from a single message</div></div>
        <div className="stat green"><div className="sv">$7.10</div><div className="sl">Total cost for that broadcast</div></div>
      </div>
    </>
  );
}

function PricingScreen({ pricing, name, config }) {
  return (
    <>
      <div className="ph-eyebrow">Pricing & Guarantee</div>
      <div className="ph-h">One price. Everything.<br /><em>Zero risk.</em></div>
      <div className="price-card" data-testid="pricing-card">
        <div className="price-amount">{pricing.amount}</div>
        <div className="price-period">{pricing.period}</div>
        <ul className="price-items">
          <li>Full setup and configuration — included free</li>
          <li>WhatsApp on {name}'s existing number</li>
          <li>24/7 AI agent on {config.phone}</li>
          <li>English + Punjabi + Hindi + auto-detect</li>
          <li>Customer memory + returning recognition</li>
          <li>Team alert system</li>
          <li>Campaign broadcasts</li>
          <li>Google review automation</li>
          <li>Zero commission — flat fee forever</li>
        </ul>
      </div>
      <div className="guarantee" data-testid="guarantee-section">
        <div className="guarantee-title">The Zivio 30-Day Guarantee</div>
        <p style={{ fontSize: 13, color: 'var(--mu)', lineHeight: 1.6 }}>If Zivio doesn't generate more in value than {pricing.amount} in your first 30 days — full refund. No questions. First month is free anyway.</p>
      </div>
    </>
  );
}

function StartScreen({ name, onNavigate }) {
  return (
    <>
      <div className="ph-eyebrow">Let's Get Started</div>
      <div className="ph-h">{name} goes live<br /><em>in 5 days.</em></div>
      <div className="ph-s">No payment. No technical work from you. We handle everything.</div>
      <div className="flow">
        <FlowItem num="1" title="Today — Handshake. Zero payment." desc="We need: your phone number, service list, and 1 hour this week." />
        <FlowItem num="2" title="Day 1–2 — We build your system" desc="Services configured in 3 languages. WhatsApp connected. Alerts ready." />
        <FlowItem num="3" title="Day 3 — Live test together" desc="Test in Punjabi. Call the number. Confirm an alert. Staff briefed in 10 minutes." />
        <FlowItem num="4" title="Day 5 — Go live." desc="Every missed call, every message — answered. 24/7." />
        <FlowItem num="5" title="Day 30 — Pay only if it worked." desc="Full refund if the numbers don't justify the price." />
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
