import { Card, Tag, TierBadge, AllocBar, StatBlock, Timeline } from '../components/ui'
import { Topbar } from '../components/layout'

const HOLDINGS = [
  { symbol: 'sTSLA', pct: '28%', value: '$146,776', color: '#3B82F6' },
  { symbol: 'sSPY', pct: '25%', value: '$131,050', color: '#6366F1' },
  { symbol: 'sGLD', pct: '12%', value: '$62,904', color: '#D4A853' },
  { symbol: 'sBTC', pct: '5%', value: '$26,210', color: '#F97316' },
  { symbol: 'USYC', pct: '30%', value: '$157,260', color: '#22C55E' },
]

const DECISIONS = [
  { tag: <Tag variant="positive">Rebalance</Tag>, title: '', description: 'sTSLA 33% → 28%, USYC 25% → 30%. Drift exceeded threshold.', time: '3m', active: true },
  { tag: <Tag variant="muted">Regime</Tag>, title: '', description: 'Risk-On confirmed. No action.', time: '1h', active: false },
  { tag: <Tag variant="accent">Rotation</Tag>, title: '', description: 'Out: Small Cap Mean Reversion. In: Cross-Sectional Momentum.', time: '6h', active: false },
  { tag: <Tag variant="muted">Skipped</Tag>, title: '', description: 'Calendar rebalance — cost > benefit. No action.', time: '12h', active: false },
]

export default function VaultDetail() {
  return (
    <>
      <Topbar label="" />
      <div className="page">
        <div className="flex items-center justify-between mb-7 fade-up fade-up-1">
          <div>
            <div className="flex items-center gap-4 mb-3">
              <h1 className="serif" style={{ fontSize: '2.2rem' }}>Momentum Alpha</h1>
              <TierBadge tier="verified" />
            </div>
            <p className="body" style={{ maxWidth: 560 }}>AI-managed portfolio constructed from cross-sectional momentum and trend-following strategies extracted from peer-reviewed research. Autonomous rebalancing with on-chain provenance.</p>
          </div>
          <div className="flex gap-3">
            <button className="btn btn-primary btn-lg">Invest</button>
            <button className="btn btn-outline">Buy on AMM</button>
          </div>
        </div>

        <div className="grid g-3 mb-7 fade-up fade-up-2" style={{ gridTemplateColumns: 'repeat(6, 1fr)' }}>
          <StatBlock label="AUM" value={<span className="stat-sm">$524.2K</span>} sub={<span className="positive">+$42.1K this week</span>} size="sm" />
          <StatBlock label="30-Day Return" value={<span className="stat-sm positive">+12.3%</span>} sub="vs SPY +4.2%" size="sm" />
          <StatBlock label="Sharpe Ratio" value={<span className="stat-sm">1.84</span>} size="sm" />
          <StatBlock label="Max Drawdown" value={<span className="stat-sm negative">−8.2%</span>} sub="Target: −20%" size="sm" />
          <StatBlock label="Share Price" value={<span className="stat-sm mono">$10.48</span>} size="sm" />
          <StatBlock label="Traces" value={<span className="stat-sm accent">42</span>} sub={<span className="accent">On-chain verified</span>} size="sm" />
        </div>

        <div className="tabs">
          {['Overview', 'Performance', 'Decisions', 'Strategies', 'Chat'].map((t, i) => (
            <button key={t} className={`tab${i === 0 ? ' active' : ''}`}>{t}</button>
          ))}
        </div>

        <div className="grid g-2" style={{ gridTemplateColumns: '1fr 380px' }}>
          <div className="flex-col gap-5">
            <Card className="fade-up fade-up-3">
              <div className="flex items-center justify-between mb-5">
                <div className="label">Current Holdings</div>
                <span className="caption">Rebalanced 3 min ago</span>
              </div>
              <AllocBar segs={HOLDINGS.map(h => ({ width: h.pct, color: h.color }))} height={6} className="mb-5" />
              <div className="flex-col">
                {HOLDINGS.map((h, i) => (
                  <div key={h.symbol} className="flex items-center justify-between" style={{ padding: '10px 0', borderBottom: i < HOLDINGS.length - 1 ? '1px solid var(--glass-border)' : 'none' }}>
                    <div className="flex items-center gap-3">
                      <span style={{ width: 10, height: 10, borderRadius: 2, background: h.color }} />
                      <span style={{ fontWeight: 500 }}>{h.symbol}</span>
                    </div>
                    <div className="flex items-center gap-5">
                      <span className="caption">{h.pct}</span>
                      <span style={{ fontWeight: 600 }}>{h.value}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="fade-up fade-up-4">
              <div className="flex items-center justify-between mb-5">
                <div className="label">NAV Performance</div>
                <div className="flex gap-2">
                  {['1W', '1M', '3M', 'All'].map((p, i) => (
                    <Tag key={p} variant={i === 1 ? 'accent' : 'muted'} className="pointer">{p}</Tag>
                  ))}
                </div>
              </div>
              <div style={{ height: 200, background: 'var(--surface-2)', borderRadius: 'var(--radius-sm)', overflow: 'hidden', position: 'relative' }}>
                <svg width="100%" height="100%" viewBox="0 0 600 200" preserveAspectRatio="none">
                  <defs><linearGradient id="navGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#D4A853" stopOpacity="0.15"/><stop offset="100%" stopColor="#D4A853" stopOpacity="0"/></linearGradient></defs>
                  <line x1="0" y1="50" x2="600" y2="50" stroke="rgba(255,255,255,0.03)" strokeWidth="0.5"/>
                  <line x1="0" y1="100" x2="600" y2="100" stroke="rgba(255,255,255,0.03)" strokeWidth="0.5"/>
                  <line x1="0" y1="150" x2="600" y2="150" stroke="rgba(255,255,255,0.03)" strokeWidth="0.5"/>
                  <path d="M0,170 C40,168 80,160 120,150 S200,130 240,118 S320,100 360,88 S440,70 480,60 S560,42 600,32" stroke="var(--accent)" fill="none" strokeWidth="1.5"/>
                  <path d="M0,170 C40,168 80,160 120,150 S200,130 240,118 S320,100 360,88 S440,70 480,60 S560,42 600,32 V200 H0 Z" fill="url(#navGrad)"/>
                  <path d="M0,170 C50,169 100,167 150,165 S250,162 300,158 S400,150 450,146 S550,140 600,136" stroke="var(--text-4)" fill="none" strokeWidth="1" strokeDasharray="3"/>
                </svg>
                <div style={{ position: 'absolute', bottom: 10, right: 14, display: 'flex', gap: 16 }}>
                  <span className="caption flex items-center gap-2"><span style={{ width: 12, height: 1.5, background: 'var(--accent)', borderRadius: 1 }} />NAV</span>
                  <span className="caption flex items-center gap-2"><span style={{ width: 12, height: 1, background: 'var(--text-4)' }} />SPY</span>
                </div>
              </div>
            </Card>

            <Card className="fade-up fade-up-5">
              <div className="label mb-5">Vault Details</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 24px' }}>
                {[
                  ['Risk Profile', 'Moderate'], ['Target Volatility', '10–15%'], ['USYC Floor', '20%'],
                  ['Management Fee', '1.50% annual'], ['Performance Fee', '20% above HWM'],
                  ['Active Strategies', '4 of 5'], ['Contract', <span key="c" className="mono" style={{ fontSize: '0.82rem', color: 'var(--info)' }}>0x7a3F…b2C1</span>],
                ].map(([k, v]) => (
                  <div key={String(k)}><div className="caption">{k}</div><div style={{ fontWeight: 500, fontSize: '0.88rem' }}>{v}</div></div>
                ))}
              </div>
            </Card>
          </div>

          <div className="flex-col gap-5">
            <Card variant="elevated" className="fade-up fade-up-2" style={{ borderColor: 'rgba(212,168,83,0.15)' }}>
              <div className="label mb-5">Invest</div>
              <div className="field">
                <label>Deposit USDC</label>
                <div style={{ position: 'relative' }}>
                  <input type="text" defaultValue="1,000.00" style={{ fontSize: '1.2rem', fontWeight: 600, paddingRight: 70 }} />
                  <span style={{ position: 'absolute', right: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-4)', fontSize: '0.82rem', fontWeight: 500 }}>USDC</span>
                </div>
              </div>
              <div className="card-flat" style={{ padding: 14, marginBottom: 20 }}>
                <div className="flex justify-between caption mb-2"><span>You receive</span><span style={{ color: 'var(--text-1)', fontWeight: 600 }}>≈ 95.42 vMOMENTUM</span></div>
                <div className="flex justify-between caption mb-2"><span>Share price</span><span>$10.48</span></div>
                <div className="flex justify-between caption"><span>Gas</span><span className="positive">~$0.01 Paymaster</span></div>
              </div>
              <button className="btn btn-primary w-full btn-lg">Deposit</button>
              <div className="caption text-center mt-4">Non-custodial · Withdraw anytime</div>
            </Card>

            <Card className="fade-up fade-up-3">
              <div className="flex items-center justify-between mb-5">
                <div className="label">Agent Decisions</div>
                <a href="/reasoning" className="caption accent">All →</a>
              </div>
              <Timeline items={DECISIONS.map(d => ({ ...d, title: d.title || 'Vault' }))} />
            </Card>

            <Card className="fade-up fade-up-4" style={{ padding: 0, overflow: 'hidden' }}>
              <div className="flex items-center justify-between" style={{ padding: '16px 20px', borderBottom: '1px solid var(--glass-border)' }}>
                <div className="label" style={{ margin: 0 }}>Vault Chat</div>
                <span className="caption">12 online</span>
              </div>
              <div style={{ border: 'none', borderRadius: 0, height: 320, display: 'flex', flexDirection: 'column' }}>
                <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                  {[
                    { ai: true, name: 'Archimedes', msg: 'Rebalanced: sTSLA 33% → 28%, USYC 25% → 30%. Trigger: drift 6.2% > 5.0%. Cost-benefit: +$294 net.', time: '10:32 AM' },
                    { ai: false, name: '0x4e8A…c2F1', msg: '@archimedes why reduce TSLA? Earnings next week and momentum looks strong', time: '10:35 AM' },
                    { ai: true, name: 'Archimedes', msg: 'This is a drift correction, not a directional call. sTSLA appreciated 8.3% in 5 days → overweight to 33%. Pre-earnings, tighter sizing limits event risk. Post-earnings, if momentum strengthens, may re-increase. Confidence: 0.78.', time: '10:35 AM' },
                  ].map((m, i) => (
                    <div key={i} className="msg">
                      <div className={`msg-avatar${m.ai ? ' ai' : ''}`}>{m.ai ? 'A' : m.name.slice(0, 2)}</div>
                      <div className="msg-body">
                        <div className={`sender${m.ai ? ' ai-name' : ''}`} style={{ fontWeight: 600, fontSize: '0.72rem', marginBottom: 3, color: m.ai ? 'var(--accent)' : 'var(--text-3)' }}>{m.name}</div>
                        <div>{m.msg}</div>
                        {m.time && <div className="caption" style={{ fontSize: '0.65rem', color: 'var(--text-4)', marginTop: 4 }}>{m.time}</div>}
                      </div>
                    </div>
                  ))}
                </div>
                <div style={{ display: 'flex', gap: 'var(--space-2)', padding: 'var(--space-3) var(--space-4)', borderTop: '1px solid var(--glass-border)', background: 'var(--surface-1)' }}>
                  <input type="text" placeholder="Ask @archimedes or message the community…" style={{ flex: 1 }} />
                  <button className="btn btn-primary btn-sm">Send</button>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </>
  )
}