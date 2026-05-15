import { Card } from '../components/ui'

const RISK_PROFILES = [
  { letter: 'C', name: 'Conservative', desc: 'Capital preservation', vol: '5–8%', maxDD: '10%', usyc: '40–60%', selected: false },
  { letter: 'M', name: 'Moderate', desc: 'Balanced growth', vol: '10–15%', maxDD: '20%', usyc: '20–40%', selected: true },
  { letter: 'A', name: 'Aggressive', desc: 'Growth-focused', vol: '20–30%', maxDD: '35%', usyc: '5–15%', selected: false },
  { letter: 'H', name: 'Hyper-Risky', desc: 'Maximum growth', vol: '30%+', maxDD: '50%', usyc: '0–5%', selected: false },
]

export default function Onboarding() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '20px 40px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--glass-border)' }}>
        <div className="flex items-center gap-3">
          <div style={{ width: 28, height: 28, borderRadius: 7, background: 'linear-gradient(135deg, var(--accent), #B8892E)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg viewBox="0 0 16 16" fill="none" width="16" height="16"><path d="M8 1L14 5v6l-6 4-6-4V5l6-4z" stroke="#09090B" strokeWidth="1.5"/><circle cx="8" cy="8" r="2.5" stroke="#09090B" strokeWidth="1.5"/></svg>
          </div>
          <span style={{ fontWeight: 700, letterSpacing: '-0.02em' }}>Archimedes</span>
        </div>
        <div className="flex items-center gap-5">
          <a href="/explore" className="caption">Explore</a>
          <a href="/strategies" className="caption">Strategies</a>
        </div>
      </div>

      <div className="text-center mb-8 fade-up fade-up-1" style={{ textAlign: 'center', padding: '80px 40px 48px', maxWidth: 680, margin: '0 auto' }}>
        <h1 className="serif" style={{ fontSize: '3.8rem', letterSpacing: '-0.04em', lineHeight: 1.05, marginBottom: 20 }}>
          Your portfolio,<br />grounded in <em style={{ fontStyle: 'italic', color: 'var(--accent)' }}>research</em>
        </h1>
        <p className="body" style={{ fontSize: '1.05rem', maxWidth: 480, margin: '0 auto' }}>
          AI-managed portfolios backed by published academic research. Every decision verifiable. Every strategy traceable to a paper.
        </p>
      </div>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 40px' }} className="grid g-3 mb-8 fade-up fade-up-2">
        {[
          { letter: 'P', bg: 'var(--surface-3)', color: 'var(--text-2)', title: 'Paper-Grounded', desc: 'Every strategy traces to peer-reviewed research. No vibes, no black boxes.' },
          { letter: 'A', bg: 'var(--accent-muted)', color: 'var(--accent)', title: 'Autonomous', desc: 'Regime detection, strategy rotation, rebalancing — all handled by the agent.' },
          { letter: 'V', bg: 'rgba(34,197,94,0.1)', color: 'var(--positive)', title: 'Verifiable', desc: 'Every reasoning trace hashed to Arc. Verify any decision on-chain.' },
        ].map((f) => (
          <div key={f.letter} style={{ textAlign: 'center', padding: '32px 24px', background: 'var(--glass)', border: '1px solid var(--glass-border)', borderRadius: 'var(--radius-lg)' }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, margin: '0 auto 16px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem', fontWeight: 700, background: f.bg, color: f.color }}>{f.letter}</div>
            <h4 style={{ color: 'var(--text-1)', textTransform: 'none', letterSpacing: 0, marginBottom: 12 }}>{f.title}</h4>
            <div className="body" style={{ fontSize: '0.82rem' }}>{f.desc}</div>
          </div>
        ))}
      </div>

      <div style={{ maxWidth: 440, margin: '0 auto', padding: '0 40px' }} className="mb-8 fade-up fade-up-3">
        <Card variant="elevated" className="text-center" style={{ padding: 36 }}>
          <h2 className="serif mb-3" style={{ fontSize: '1.6rem' }}>Connect Your Wallet</h2>
          <p className="body mb-6" style={{ fontSize: '0.85rem' }}>Non-custodial — you always control your keys.</p>
          <div className="flex-col gap-3" style={{ maxWidth: 300, margin: '0 auto' }}>
            {[
              { letter: 'C', bg: 'var(--accent)', color: 'var(--canvas)', label: 'Create with Circle' },
              { letter: 'M', bg: '#F97316', color: 'white', label: 'MetaMask' },
              { letter: 'W', bg: '#3B82F6', color: 'white', label: 'WalletConnect' },
            ].map((w) => (
              <button key={w.letter} style={{ display: 'flex', alignItems: 'center', gap: 12, width: '100%', padding: '14px 20px', background: 'var(--surface-2)', border: '1px solid var(--glass-border)', borderRadius: 'var(--radius-sm)', color: 'var(--text-1)', fontSize: '0.9rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s' }}>
                <div style={{ width: 32, height: 32, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, background: w.bg, color: w.color }}>{w.letter}</div>
                {w.label}
              </button>
            ))}
          </div>
          <div className="caption mt-5">Testnet only — no real funds at risk.</div>
        </Card>
      </div>

      <div className="text-center mb-6 fade-up fade-up-4" style={{ textAlign: 'center' }}>
        <h2 className="serif mb-3" style={{ fontSize: '1.6rem' }}>Choose Your Risk Profile</h2>
        <p className="body" style={{ fontSize: '0.85rem', maxWidth: 480, margin: '0 auto' }}>Determines which strategies and weights the AI uses.</p>
      </div>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 40px' }} className="grid g-4 mb-8 fade-up fade-up-5">
        {RISK_PROFILES.map((p) => (
          <div key={p.letter} className={`risk-option${p.selected ? ' selected' : ''}`}>
            <div className="label mb-3" style={{ fontSize: '1.8rem', color: p.selected ? 'var(--accent)' : 'var(--text-2)', textTransform: 'none', letterSpacing: 0 }}>{p.letter}</div>
            <div style={{ fontWeight: 700, marginBottom: 4 }}>{p.name}</div>
            <div className="caption mb-5">{p.desc}</div>
            <div className="flex justify-between caption mb-1"><span>Vol</span><span>{p.vol}</span></div>
            <div className="flex justify-between caption mb-1"><span>Max DD</span><span>{p.maxDD}</span></div>
            <div className="flex justify-between caption"><span>USYC</span><span>{p.usyc}</span></div>
            {p.selected && <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid rgba(212,168,83,0.2)' }}><span className="caption accent" style={{ fontWeight: 600 }}>Selected</span></div>}
          </div>
        ))}
      </div>

      <div style={{ maxWidth: 440, margin: '0 auto', padding: '0 40px' }} className="mb-8">
        <Card variant="elevated" className="text-center" style={{ padding: 36 }}>
          <h2 className="serif mb-3" style={{ fontSize: '1.6rem' }}>Initial Deposit</h2>
          <p className="body mb-5" style={{ fontSize: '0.85rem' }}>The AI agent will construct your portfolio based on your risk profile.</p>
          <div className="field" style={{ maxWidth: 280, margin: '0 auto' }}>
            <input type="text" defaultValue="1,000" style={{ fontSize: '1.4rem', fontWeight: 700, textAlign: 'center' }} />
          </div>
          <button className="btn btn-primary btn-lg" style={{ marginTop: 12 }}>Build My Portfolio</button>
          <div className="caption mt-5">Non-custodial · Withdraw anytime · Full reasoning traces</div>
        </Card>
      </div>

      <div className="grid g-4 text-center" style={{ maxWidth: 600, margin: '0 auto', padding: '0 40px' }}>
        <div><div className="stat-sm accent">247</div><div className="caption mt-4">On-chain traces</div></div>
        <div><div className="stat-sm positive">$2.4M</div><div className="caption mt-4">Total AUM</div></div>
        <div><div className="stat-sm">1.82</div><div className="caption mt-4">Avg Sharpe</div></div>
        <div><div className="stat-sm" style={{ color: 'var(--info)' }}>8</div><div className="caption mt-4">Curated papers</div></div>
      </div>

      <div style={{ padding: 40, textAlign: 'center', borderTop: '1px solid var(--glass-border)', marginTop: 64 }}>
        <div className="caption">Built for Agora Agents Hackathon · Canteen × Circle × Arc · May 2026</div>
        <div className="caption mt-4" style={{ color: 'var(--text-4)' }}>
          <a href="/explore">Marketplace</a> · <a href="/strategies">Strategies</a> · <a href="/reasoning">Traces</a>
        </div>
      </div>
    </div>
  )
}