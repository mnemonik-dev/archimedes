import { Topbar } from '../components/layout'
import { Card, Tag, AllocBar, StatBlock } from '../components/ui'

const ECOSYSTEM_STATS = [
  { label: 'Ecosystem AUM', value: '$2.4M', sub: '+12.3% this week', subClass: 'positive' },
  { label: 'Active Vaults', value: '18', sub: '12 verified · 6 community' },
  { label: 'On-Chain Traces', value: '247', sub: 'All verifiable', subClass: 'accent' },
  { label: 'Avg Sharpe (T1)', value: '1.82', sub: '+0.14 vs benchmark', subClass: 'positive' },
]

const SYNTHETIC_ASSETS = [
  { symbol: 'sTSLA', name: 'Synthetic Tesla', price: '$287.42', change: '+3.21%', changeClass: 'positive', color: '#3B82F6', letter: 'T' },
  { symbol: 'sSPY', name: 'Synthetic S&P 500', price: '$532.18', change: '+0.87%', changeClass: 'positive', color: '#6366F1', letter: 'S' },
  { symbol: 'sGLD', name: 'Synthetic Gold', price: '$2,341', change: '−0.32%', changeClass: 'negative', color: '#D4A853', letter: 'G' },
  { symbol: 'sBTC', name: 'Synthetic Bitcoin', price: '$67,842', change: '+2.14%', changeClass: 'positive', color: '#F97316', letter: 'B' },
  { symbol: 'USYC', name: 'Circle Yield', price: '$1.0012', change: '4.82% APY', changeClass: '', color: '#22C55E', letter: 'Y' },
]

const VAULTS = [
  { rank: 1, name: 'Momentum Alpha', ticker: 'vMOMENTUM', tier: 'verified' as const, aum: '$524,200', return30d: '+12.3%', returnClass: 'positive', sharpe: '1.84', maxDD: '−8.2%', fees: '1.5% + 20%', segs: [{ width: '28%', color: '#3B82F6' }, { width: '25%', color: '#6366F1' }, { width: '12%', color: '#D4A853' }, { width: '5%', color: '#F97316' }, { width: '30%', color: '#22C55E' }] },
  { rank: 2, name: 'Yield Optimizer', ticker: 'vYIELD', tier: 'verified' as const, aum: '$312,800', return30d: '+8.1%', returnClass: 'positive', sharpe: '2.12', maxDD: '−4.1%', fees: '1.0% + 15%', segs: [{ width: '55%', color: '#22C55E' }, { width: '20%', color: '#6366F1' }, { width: '15%', color: '#D4A853' }, { width: '10%', color: '#3B82F6' }] },
  { rank: 3, name: 'DeFi Degen', ticker: 'vDEGEN', tier: 'community' as const, aum: '$87,400', return30d: '+18.7%', returnClass: 'positive', sharpe: '0.94', maxDD: '−22.1%', fees: '2.0% + 25%', segs: [{ width: '60%', color: '#F97316' }, { width: '25%', color: '#3B82F6' }, { width: '15%', color: '#22C55E' }] },
  { rank: 4, name: 'Safe Haven', ticker: 'vSAFE', tier: 'community' as const, aum: '$145,600', return30d: '+5.2%', returnClass: 'positive', sharpe: '1.54', maxDD: '−3.8%', fees: '0.5% + 10%', segs: [{ width: '60%', color: '#22C55E' }, { width: '25%', color: '#D4A853' }, { width: '15%', color: '#6366F1' }] },
  { rank: 5, name: 'Multi-Factor Quant', ticker: 'vMFQ', tier: 'verified' as const, aum: '$298,100', return30d: '+9.8%', returnClass: 'positive', sharpe: '1.67', maxDD: '−11.4%', fees: '1.5% + 20%', segs: [{ width: '35%', color: '#3B82F6' }, { width: '25%', color: '#6366F1' }, { width: '20%', color: '#D4A853' }, { width: '20%', color: '#22C55E' }] },
]

const ACTIVITY = [
  { tag: <Tag variant="positive">Rebalance</Tag>, title: 'Momentum Alpha', desc: 'Reduced sTSLA 33% → 28%, shifted to USYC. Drift threshold exceeded. Cost-benefit: +$294 net.', time: '3 min ago', active: true },
  { tag: <Tag variant="muted">Regime</Tag>, title: 'Global Detection', desc: 'Regime confirmed Risk-On. VIX 14.2, positive equity momentum, tight credit spreads. No action.', time: '1 hr ago', active: false },
  { tag: <Tag variant="accent">Rotation</Tag>, title: 'Multi-Factor Quant', desc: 'Rotated out "Mean Reversion Small Cap" (Sharpe 0.38) → "Cross-Sectional Momentum" (Sharpe 1.42, correlation 0.12).', time: '4 hrs ago', active: false },
]

export default function Marketplace() {
  return (
    <>
      <Topbar label="Marketplace" />
      <div className="page">
        <div className="grid g-4 mb-7 fade-up fade-up-1">
          {ECOSYSTEM_STATS.map((s) => (
            <div key={s.label}>
              <div className="label mb-2">{s.label}</div>
              <div className="stat">{s.value}</div>
              <div className={`caption mt-4 ${s.subClass || ''}`}>{s.sub}</div>
            </div>
          ))}
        </div>

        <div className="divider" />

        <div className="mb-7 fade-up fade-up-2">
          <div className="flex items-center justify-between mb-5">
            <div className="label">Synthetic Assets</div>
            <span className="caption">Oracle updated 12s ago</span>
          </div>
          <div className="grid g-5">
            {SYNTHETIC_ASSETS.map((a) => (
              <div key={a.symbol} className="card-flat" style={{ padding: 20 }}>
                <div className="flex items-center gap-3 mb-3">
                  <div className="asset-dot" style={{ background: a.color }}>{a.letter}</div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.88rem' }}>{a.symbol}</div>
                    <div className="caption">{a.name}</div>
                  </div>
                </div>
                <div style={{ fontSize: '1.3rem', fontWeight: 700, letterSpacing: '-0.02em' }}>{a.price}</div>
                <div className={`caption ${a.changeClass}`}>{a.change}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="fade-up fade-up-3">
          <div className="flex items-center justify-between mb-5">
            <div className="label">Vault Leaderboard</div>
            <div className="flex gap-2">
              <Tag variant="accent">All</Tag>
              <Tag variant="muted">Verified</Tag>
              <Tag variant="muted">Community</Tag>
            </div>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th style={{ width: 32 }}>#</th>
                  <th>Vault</th>
                  <th>Tier</th>
                  <th className="text-right">AUM</th>
                  <th className="text-right">30d Return</th>
                  <th className="text-right">Sharpe</th>
                  <th className="text-right">Max DD</th>
                  <th>Allocation</th>
                  <th className="text-right">Fees</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {VAULTS.map((v) => (
                  <tr key={v.rank} className="pointer">
                    <td style={{ fontWeight: 700, color: v.rank === 1 ? 'var(--accent)' : 'var(--text-3)' }}>{v.rank}</td>
                    <td>
                      <div><span style={{ fontWeight: 600 }}>{v.name}</span></div>
                      <div className="mono caption">{v.ticker}</div>
                    </td>
                    <td><span className={`tier tier-${v.tier}`}>{v.tier === 'verified' ? 'Verified' : 'Community'}</span></td>
                    <td className="text-right" style={{ fontWeight: 600 }}>{v.aum}</td>
                    <td className={`text-right ${v.returnClass}`} style={{ fontWeight: 600 }}>{v.return30d}</td>
                    <td className="text-right" style={{ fontWeight: 600 }}>{v.sharpe}</td>
                    <td className="text-right negative">{v.maxDD}</td>
                    <td>
                      <AllocBar segs={v.segs} style={{ width: 100 }} />
                    </td>
                    <td className="text-right caption">{v.fees}</td>
                    <td><button className={`btn ${v.tier === 'verified' ? 'btn-primary' : 'btn-outline'} btn-sm`}>Invest</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-6 fade-up fade-up-4">
          <div className="flex items-center justify-between mb-5">
            <div className="label">Agent Activity</div>
            <a href="/reasoning" className="caption accent">All traces →</a>
          </div>
          <div className="timeline">
            {ACTIVITY.map((a, i) => (
              <div key={i} className={`tl-item${a.active ? ' active' : ''}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">{a.tag}<span style={{ fontWeight: 600, fontSize: '0.88rem' }}>{a.title}</span></div>
                  <span className="caption">{a.time}</span>
                </div>
                <div className="body">{a.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}