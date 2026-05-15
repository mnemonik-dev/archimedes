import { Topbar } from '../components/layout'
import { Card, Tag, StatBlock } from '../components/ui'

const HOLDINGS = [
  { name: 'Momentum Alpha', ticker: 'vMOMENTUM', tier: 'verified' as const, balance: '476.23', value: '$4,990.84', weight: '38.9%', pnl: '+$490.84', pnlClass: 'positive', change24h: '+1.8%', changeClass: 'positive' },
  { name: 'Yield Optimizer', ticker: 'vYIELD', tier: 'verified' as const, balance: '290.15', value: '$3,201.46', weight: '24.9%', pnl: '+$201.46', pnlClass: 'positive', change24h: '+0.4%', changeClass: 'positive' },
  { name: 'DeFi Degen', ticker: 'vDEGEN', tier: 'community' as const, balance: '122.80', value: '$2,170.30', weight: '16.9%', pnl: '+$370.30', pnlClass: 'positive', change24h: '−2.1%', changeClass: 'negative' },
  { name: 'USDC', ticker: '', label: 'Unallocated', tier: null, balance: '1,240.00', value: '$1,240.00', weight: '9.7%', pnl: '—', pnlClass: '', change24h: '—', changeClass: '' },
  { name: 'USYC', ticker: '', label: 'Circle Yield', tier: 'yield' as const, balance: '1,238.40', value: '$1,240.00', weight: '9.7%', pnl: '+$48.20', pnlClass: 'positive', change24h: '+0.01%', changeClass: 'positive' },
]

const ACTIVITY = [
  { desc: 'Deposited 1,000 USDC → vMOMENTUM', sub: 'Received 95.42 vMOMENTUM', value: '$1,000', time: '2h ago' },
  { desc: 'Swapped 500 USDC → USYC', sub: 'Via AMM · 0.3% fee', value: '499.25 USYC', time: '5h ago' },
  { desc: 'Added liquidity — USDC/sBTC pool', sub: '500 USDC + 0.0074 sBTC · Earned $3.20', value: '$1,000', time: '1d ago' },
]

export default function PortfolioDashboard() {
  return (
    <>
      <Topbar label="My Portfolio" />
      <div className="page">
        <div className="mb-7 fade-up fade-up-1" style={{ padding: 'var(--space-7) 0 var(--space-6)', borderBottom: '1px solid var(--glass-border)' }}>
          <div className="label mb-3">Total Portfolio Value</div>
          <div style={{ fontFamily: 'var(--sans)', fontSize: '3.5rem', fontWeight: 700, letterSpacing: '-0.04em', lineHeight: 1 }}>$12,842.60</div>
          <div className="flex items-center gap-4 mt-4">
            <span className="positive" style={{ fontSize: '1.05rem', fontWeight: 600 }}>+$1,342.60 (+11.7%)</span>
            <span className="caption">since May 13</span>
          </div>
        </div>

        <div className="grid g-4 mb-7 fade-up fade-up-2">
          <StatBlock label="Vault Positions" value={<span className="stat-sm">3</span>} sub="Across 3 vaults" size="sm" />
          <StatBlock label="Unallocated" value={<span className="stat-sm mono">$1,240</span>} sub="USDC ready to invest" size="sm" />
          <StatBlock label="Yield Earned" value={<span className="stat-sm" style={{ color: 'var(--positive)' }}>$48.20</span>} sub="USYC · 4.82% APY" size="sm" />
          <StatBlock label="LP Fees" value={<span className="stat-sm" style={{ color: 'var(--positive)' }}>$12.40</span>} sub="From 2 pools" size="sm" />
        </div>

        <Card className="mb-7 fade-up fade-up-3">
          <div className="flex items-center justify-between mb-5">
            <div className="label">Portfolio Value</div>
            <div className="flex gap-2">
              {['1D', '1W', '1M', 'All'].map((p, i) => (
                <Tag key={p} variant={i === 2 ? 'accent' : 'muted'} className="pointer">{p}</Tag>
              ))}
            </div>
          </div>
          <div style={{ height: 220, background: 'var(--surface-2)', borderRadius: 'var(--radius-sm)', overflow: 'hidden' }}>
            <svg width="100%" height="100%" viewBox="0 0 800 220" preserveAspectRatio="none">
              <defs><linearGradient id="pGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#D4A853" stopOpacity="0.15"/><stop offset="100%" stopColor="#D4A853" stopOpacity="0"/></linearGradient></defs>
              <line x1="0" y1="55" x2="800" y2="55" stroke="rgba(255,255,255,0.03)" strokeWidth="0.5"/>
              <line x1="0" y1="110" x2="800" y2="110" stroke="rgba(255,255,255,0.03)" strokeWidth="0.5"/>
              <line x1="0" y1="165" x2="800" y2="165" stroke="rgba(255,255,255,0.03)" strokeWidth="0.5"/>
              <path d="M0,190 C50,188 100,182 150,175 S250,160 300,150 S400,130 450,118 S550,95 600,80 S700,55 800,40" stroke="var(--accent)" fill="none" strokeWidth="1.5"/>
              <path d="M0,190 C50,188 100,182 150,175 S250,160 300,150 S400,130 450,118 S550,95 600,80 S700,55 800,40 V220 H0 Z" fill="url(#pGrad)"/>
            </svg>
          </div>
        </Card>

        <div className="fade-up fade-up-4">
          <div className="label mb-5">Holdings</div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Asset</th><th>Type</th><th className="text-right">Balance</th><th className="text-right">Value</th><th className="text-right">Weight</th><th className="text-right">PnL</th><th className="text-right">24h</th>
                </tr>
              </thead>
              <tbody>
                {HOLDINGS.map((h) => (
                  <tr key={h.name} className="pointer">
                    <td>
                      <div style={{ fontWeight: 600 }}>{h.name}</div>
                      {h.ticker && <div className="mono caption">{h.ticker}</div>}
                      {h.label && <div className="caption">{h.label}</div>}
                    </td>
                    <td>
                      {h.tier === 'verified' && <span className="tier tier-verified">Verified</span>}
                      {h.tier === 'community' && <span className="tier tier-community">Community</span>}
                      {h.tier === 'yield' && <Tag variant="positive">Yield</Tag>}
                      {!h.tier && <Tag variant="muted">Stable</Tag>}
                    </td>
                    <td className="text-right mono">{h.balance}</td>
                    <td className="text-right" style={{ fontWeight: 600 }}>{h.value}</td>
                    <td className="text-right">{h.weight}</td>
                    <td className={`text-right ${h.pnlClass}`} style={{ fontWeight: 600 }}>{h.pnl}</td>
                    <td className={`text-right ${h.changeClass}`}>{h.change24h}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-6 fade-up fade-up-5">
          <div className="label mb-5">Recent Activity</div>
          <div className="flex-col gap-3">
            {ACTIVITY.map((a, i) => (
              <div key={i} className="card-flat flex items-center justify-between" style={{ padding: '14px 20px' }}>
                <div><div style={{ fontWeight: 500, fontSize: '0.88rem' }}>{a.desc}</div><div className="caption">{a.sub}</div></div>
                <div className="text-right"><div style={{ fontWeight: 600 }}>{a.value}</div><div className="caption">{a.time}</div></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}