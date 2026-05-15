import { Topbar } from '../components/layout'
import { Card, Tag, TierBadge } from '../components/ui'

const STRATEGIES = [
  { name: 'Mean Reversion Pairs', status: 'Live' as const, statusVariant: 'positive' as const, ref: 'Gatev, Goetzmann & Rouwenhorst (2006) · Review of Financial Studies', tags: ['TR', '2 vaults'], sharpe: '1.28', cagr: '12.1%', maxDD: '−11.8%', corrSPY: '0.08' },
  { name: 'Risk Parity', status: 'Live' as const, statusVariant: 'positive' as const, ref: 'Asness, Frazzini & Pedersen (2012) · Financial Analysts Journal', tags: ['PM', '4 vaults'], sharpe: '1.56', cagr: '9.8%', maxDD: '−7.4%', corrSPY: '0.31' },
  { name: 'Trend Following CTA', status: 'Live' as const, statusVariant: 'positive' as const, ref: 'Moskowitz, Ooi & Pedersen (2012) · Journal of Financial Economics', tags: ['TR', '2 vaults'], sharpe: '1.14', cagr: '15.2%', maxDD: '−18.3%', corrSPY: '−0.12' },
  { name: 'Kelly Criterion Sizing', status: 'Live' as const, statusVariant: 'positive' as const, ref: 'Thorp (2006) · Kelly Capital Growth Investment Criterion', tags: ['RM', '3 vaults'], sharpe: '1.88', cagr: '22.1%', maxDD: '−19.7%', corrSPY: '0.55' },
]

const PAPERS = [
  { title: 'Returns to Buying Winners and Selling Losers', authors: 'Jegadeesh, Titman', year: '1993', venue: 'J. Finance', category: 'PM', citations: '12,847', strategies: '1 live', curator: 'Dan' },
  { title: 'Pairs Trading: Relative-Value Rule', authors: 'Gatev, Goetzmann, Rouwenhorst', year: '2006', venue: 'Rev. Fin. Studies', category: 'TR', citations: '4,218', strategies: '1 live', curator: 'Dan' },
  { title: 'Leverage Aversion and Risk Parity', authors: 'Asness, Frazzini, Pedersen', year: '2012', venue: 'FAJ', category: 'PM', citations: '2,891', strategies: '1 live', curator: 'Dan' },
]

export default function StrategyExplorer() {
  return (
    <>
      <Topbar label="Strategy Library" />
      <div className="page">
        <div className="mb-7 fade-up fade-up-1" style={{ maxWidth: 640 }}>
          <h2 className="serif mb-3" style={{ fontSize: '2rem' }}>Paper-Grounded Strategies</h2>
          <p className="body">Every strategy traces back to published academic research. Methodology extracted by AI, validated by human curators, backtested against real data.</p>
        </div>

        <div className="flex items-center gap-3 mb-6 fade-up fade-up-2">
          <Tag variant="accent">All (8)</Tag>
          <Tag variant="muted">Live (5)</Tag>
          <Tag variant="muted">Validated (2)</Tag>
          <Tag variant="muted">Candidate (1)</Tag>
        </div>

        <Card variant="elevated" className="mb-7 fade-up fade-up-3" style={{ borderColor: 'rgba(212,168,83,0.12)' }}>
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="flex items-center gap-4 mb-2">
                <h3 style={{ fontSize: '1.2rem' }}>Cross-Sectional Momentum</h3>
                <Tag variant="positive">Live</Tag>
                <Tag variant="accent">In 3 vaults</Tag>
              </div>
              <div className="body">Buy top-decile 12-month performers, sell bottom decile. Monthly rebalance.</div>
            </div>
            <button className="btn btn-outline btn-sm">Full Passport →</button>
          </div>

          <div className="grid g-3" style={{ gap: 16 }}>
            <Card variant="flat" style={{ padding: 20 }}>
              <div className="label mb-4">Source Paper</div>
              <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 4, lineHeight: 1.4 }}>"Returns to Buying Winners and Selling Losers"</div>
              <div className="caption mb-4">Jegadeesh & Titman (1993) · Journal of Finance</div>
              <div className="flex gap-2 mb-4"><Tag variant="muted">q-fin.PM</Tag><Tag variant="muted">q-fin.TR</Tag></div>
              <div className="caption">arXiv: <span className="mono" style={{ color: 'var(--info)' }}>9301001</span></div>
              <div className="caption">Citations: 12,847</div>
              <div className="caption">Curator: <span className="mono" style={{ color: 'var(--info)' }}>Dan</span></div>
            </Card>

            <Card variant="flat" style={{ padding: 20 }}>
              <div className="label mb-4">Backtest Results</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div><div className="caption">Sharpe</div><div style={{ fontWeight: 700, fontSize: '1.1rem' }}>1.42</div></div>
                <div><div className="caption">CAGR</div><div className="positive" style={{ fontWeight: 700, fontSize: '1.1rem' }}>18.4%</div></div>
                <div><div className="caption">Max DD</div><div className="negative" style={{ fontWeight: 700, fontSize: '1.1rem' }}>−14.2%</div></div>
                <div><div className="caption">Win Rate</div><div style={{ fontWeight: 700, fontSize: '1.1rem' }}>58.3%</div></div>
                <div><div className="caption">Calmar</div><div style={{ fontWeight: 700, fontSize: '1.1rem' }}>1.30</div></div>
                <div><div className="caption">Corr SPY</div><div style={{ fontWeight: 700, fontSize: '1.1rem' }}>0.42</div></div>
              </div>
              <div className="divider" style={{ margin: '12px 0 8px' }} />
              <div className="caption">Paper claimed: <strong>1.65</strong></div>
              <div className="caption">Backtest: <strong>1.42</strong> <span className="positive">(86% ✓)</span></div>
            </Card>

            <Card variant="flat" style={{ padding: 20 }}>
              <div className="label mb-4">On-Chain Provenance</div>
              <div className="caption mb-3">Strategy ID<br /><span className="mono" style={{ color: 'var(--info)', wordBreak: 'break-all' }}>0x8a4f2e…c3b1</span></div>
              <div className="caption mb-3">Methodology Hash<br /><span className="mono" style={{ color: 'var(--text-2)', wordBreak: 'break-all' }}>0x7f3d1a…e2c4</span></div>
              <div className="caption mb-3">Registration Tx<br /><a className="mono" style={{ color: 'var(--info)' }} href="#">0x9b2c4e…d1f7</a></div>
              <div className="caption mb-4">Extraction: claude-3.5-sonnet</div>
              <div className="verify-panel" style={{ padding: 10, borderRadius: 'var(--radius-sm)' }}>
                <div className="verify-badge" style={{ fontSize: '0.82rem' }}>
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5"/><path d="M5 8l2 2 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
                  Hash Verified
                </div>
              </div>
            </Card>
          </div>

          <div style={{ height: 100, background: 'var(--surface-2)', borderRadius: 'var(--radius-sm)', overflow: 'hidden', marginTop: 20, position: 'relative' }}>
            <svg width="100%" height="100%" viewBox="0 0 900 100" preserveAspectRatio="none">
              <defs><linearGradient id="eqG" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#22C55E" stopOpacity="0.1"/><stop offset="100%" stopColor="#22C55E" stopOpacity="0"/></linearGradient></defs>
              <path d="M0,85 C50,83 100,78 150,72 S250,62 300,55 S400,42 450,36 S550,25 600,20 S700,14 800,10 S870,8 900,6" stroke="var(--positive)" fill="none" strokeWidth="1.2"/>
              <path d="M0,85 C50,83 100,78 150,72 S250,62 300,55 S400,42 450,36 S550,25 600,20 S700,14 800,10 S870,8 900,6 V100 H0 Z" fill="url(#eqG)"/>
            </svg>
            <div className="caption" style={{ position: 'absolute', top: 8, left: 12, color: 'var(--text-4)' }}>Equity Curve · 2015–2026 Walk-Forward OOS</div>
          </div>
        </Card>

        <div className="grid g-2 mb-7">
          {STRATEGIES.map((s, i) => (
            <Card key={s.name} className={`fade-up fade-up-${i < 2 ? 4 : 5}`}>
              <div className="flex items-center gap-3 mb-4">
                <h3>{s.name}</h3>
                <Tag variant={s.statusVariant}>{s.status}</Tag>
              </div>
              <div className="caption mb-4">{s.ref}</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginBottom: 12 }}>
                <div><div className="caption">Sharpe</div><div style={{ fontWeight: 700 }}>{s.sharpe}</div></div>
                <div><div className="caption">CAGR</div><div className="positive" style={{ fontWeight: 700 }}>{s.cagr}</div></div>
                <div><div className="caption">Max DD</div><div className="negative" style={{ fontWeight: 700 }}>{s.maxDD}</div></div>
                <div><div className="caption">Corr SPY</div><div style={{ fontWeight: 700 }}>{s.corrSPY}</div></div>
              </div>
              <div className="flex gap-2">{s.tags.map((t, j) => <Tag key={j} variant={j === 1 ? 'accent' : 'muted'}>{t}</Tag>)}</div>
            </Card>
          ))}
        </div>

        <div>
          <div className="label mb-5">Paper Corpus</div>
          <div className="caption mb-5">8 papers curated · 12 candidate papers queued</div>
          <div className="table-container">
            <table>
              <thead>
                <tr><th>Paper</th><th>Authors</th><th>Year</th><th>Venue</th><th>Categories</th><th className="text-right">Citations</th><th>Strategies</th><th>Curator</th></tr>
              </thead>
              <tbody>
                {PAPERS.map((p) => (
                  <tr key={p.title}>
                    <td style={{ fontWeight: 500 }}>{p.title}</td>
                    <td className="caption">{p.authors}</td>
                    <td>{p.year}</td>
                    <td className="caption">{p.venue}</td>
                    <td><Tag variant="muted">{p.category}</Tag></td>
                    <td className="text-right">{p.citations}</td>
                    <td><Tag variant="positive">{p.strategies}</Tag></td>
                    <td className="mono caption" style={{ color: 'var(--info)' }}>{p.curator}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  )
}