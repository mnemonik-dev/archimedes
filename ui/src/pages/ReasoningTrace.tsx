import { Topbar } from '../components/layout'
import React from 'react'
import { Card, Tag, VerifyPanel, AllocBar } from '../components/ui'

const BEFORE_AFTER = [
  { asset: 'sTSLA', before: '33.2%', after: '28.0%', delta: '−5.2%', deltaClass: 'negative', highlight: false },
  { asset: 'sSPY', before: '25.0%', after: '25.0%', delta: '—', deltaClass: '', highlight: false },
  { asset: 'sGLD', before: '12.0%', after: '12.0%', delta: '—', deltaClass: '', highlight: false },
  { asset: 'sBTC', before: '5.0%', after: '5.0%', delta: '—', deltaClass: '', highlight: false },
  { asset: 'USYC', before: '24.8%', after: '30.0%', delta: '+5.2%', deltaClass: 'positive', highlight: true },
]

const TOOL_CALLS = [
  { method: 'GET', variant: 'muted' as const, name: 'market_data.vix', result: '14.2', time: '48ms' },
  { method: 'GET', variant: 'muted' as const, name: 'market_data.sp500_ma', result: 'above_both', time: '52ms' },
  { method: 'GET', variant: 'muted' as const, name: 'portfolio.get_drift', result: 'sTSLA 6.2%', time: '12ms' },
  { method: 'GET', variant: 'muted' as const, name: 'usyc.yield', result: '4.82%', time: '38ms' },
  { method: 'CALC', variant: 'accent' as const, name: 'optimizer.cost_benefit', result: '+$294', time: '145ms' },
  { method: 'EXEC', variant: 'positive' as const, name: 'vault.rebalance', result: 'success', time: '547ms' },
]

export default function ReasoningTrace() {
  return (
    <>
      <Topbar label="" />
      <div className="page">
        <div className="mb-6 fade-up fade-up-1">
          <div className="flex items-center gap-4 mb-3">
            <h2 className="serif" style={{ fontSize: '2rem' }}>Trace #247</h2>
            <Tag variant="positive">Rebalance</Tag>
            <Tag variant="accent">Verified</Tag>
          </div>
          <div className="flex items-center gap-5 caption">
            <span>Momentum Alpha</span>
            <span>May 13, 2026 · 10:32 AM UTC</span>
            <span>Confidence: <strong className="positive">0.78</strong></span>
          </div>
        </div>

        <VerifyPanel className="mb-7 fade-up fade-up-2">
          <div className="flex items-center justify-between mb-5">
            <div className="verify-badge" style={{ fontSize: '1rem' }}>
              <svg width="20" height="20" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5"/><path d="M5 8l2 2 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
              On-Chain Verification Passed
            </div>
            <button className="btn btn-outline btn-sm" style={{ color: 'var(--positive)', borderColor: 'rgba(34,197,94,0.2)' }}>View on Arc Explorer</button>
          </div>
          <div className="grid g-2" style={{ gap: 12 }}>
            {[
              { label: 'Content Hash (keccak256)', value: '0x8a4f2e7b3c1d9e6f5a2b8c0d4e7f1a3b5c9d2e6f8a0b4c7d1e3f5a9b2c6d8e', color: 'var(--positive)' },
              { label: 'On-Chain Anchor (Arc Tx)', value: <a href="#" style={{ color: 'var(--info)' }}>0x9b2c4e7f1a3d5b8c0e2f6a4d7b9c1e3f5a8b0d2c6e4f7a1b3d5c9e2f8a0b4d</a> },
              { label: 'Recomputed Hash (in-browser)', value: '0x8a4f2e7b3c1d9e6f5a2b8c0d4e7f1a3b5c9d2e6f8a0b4c7d1e3f5a9b2c6d8e', color: 'var(--positive)' },
              { label: 'Result', value: 'Hash Match — Authentic & Unmodified', highlight: true },
            ].map((item, i) => (
              <Card key={i} variant="flat" style={{ padding: 14, background: 'rgba(34,197,94,0.03)' }}>
                <div className="caption mb-2">{item.label}</div>
                <div className="mono" style={{ fontSize: '0.78rem', color: item.color || 'inherit', wordBreak: 'break-all', lineHeight: 1.6 }}>{item.value}</div>
              </Card>
            ))}
          </div>
        </VerifyPanel>

        <div className="grid g-2" style={{ gridTemplateColumns: '1fr 380px' }}>
          <div className="flex-col gap-5">
            <Card className="fade-up fade-up-3">
              <div className="label mb-5">Decision Context</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '6px 20px' }}>
                {[
                  ['Type', <Tag variant="positive" style={{ width: 'fit-content' }}>Rebalance</Tag>],
                  ['Trigger', <span style={{ fontWeight: 500, fontSize: '0.88rem' }}>Drift exceeded (6.2% &gt; 5.0%)</span>],
                  ['Regime', <span className="positive" style={{ fontWeight: 600, fontSize: '0.88rem' }}>Risk-On</span>],
                  ['VIX', <span style={{ fontSize: '0.88rem' }}>14.2</span>],
                  ['S&P 500', <span className="positive" style={{ fontSize: '0.88rem' }}>Above 50/200 MA</span>],
                  ['Credit', <span className="positive" style={{ fontSize: '0.88rem' }}>Tight (1.12%)</span>],
                  ['BTC Dom.', <span style={{ fontSize: '0.88rem' }}>54.2%</span>],
                  ['USYC', <span style={{ fontSize: '0.88rem' }}>4.82% APY</span>],
                ].map(([k, v]) => <React.Fragment key={String(k)}><span className="caption">{k}</span>{v}</React.Fragment>)}
              </div>
            </Card>

            <Card className="fade-up fade-up-4">
              <div className="label mb-5">Agent Reasoning</div>
              <Card variant="flat" style={{ padding: 24, lineHeight: 1.85, fontSize: '0.9rem', color: 'var(--text-2)' }}>
                <p style={{ marginBottom: 14 }}><strong style={{ color: 'var(--text-1)' }}>Trigger.</strong> sTSLA position grew from target 28% to 33.2% — an 8.3% price appreciation over 5 days. Exceeds the 5% drift threshold.</p>
                <p style={{ marginBottom: 14 }}><strong style={{ color: 'var(--text-1)' }}>Regime.</strong> Confirmed Risk-On: VIX 14.2, S&P above both MAs, credit spreads tight at 1.12%, cross-asset correlation normal (0.34). No regime change.</p>
                <p style={{ marginBottom: 14 }}><strong style={{ color: 'var(--text-1)' }}>Cost-benefit.</strong> Selling ~$27,200 sTSLA → USYC. Transaction cost: $18.40 (AMM fee + slippage). Expected risk reduction: volatility from 13.8% to 12.4%. Risk-adjusted benefit: $312 over 30d. Ratio: 17x (well above 2x minimum).</p>
                <p style={{ marginBottom: 14 }}><strong style={{ color: 'var(--text-1)' }}>Earnings note.</strong> TSLA earnings next week. Pre-earnings, tighter sizing limits event risk. Not exiting — rebalancing to target. Post-earnings, momentum may warrant re-increase.</p>
                <p><strong style={{ color: 'var(--text-1)' }}>Action.</strong> Sell $27,200 sTSLA → Buy $27,200 USYC. Allocation: sTSLA 33.2% → 28%, USYC 25% → 30%.</p>
              </Card>
            </Card>

            <Card className="fade-up fade-up-5">
              <div className="label mb-5">Strategies Consulted</div>
              <div className="flex-col gap-3">
                {[
                  { name: 'Cross-Sectional Momentum', ref: 'Jegadeesh & Titman (1993)', weight: '28%' },
                  { name: 'Risk Parity', ref: 'Asness, Frazzini & Pedersen (2012)', weight: '25%' },
                  { name: 'Trend Following CTA', ref: 'Moskowitz, Ooi & Pedersen (2012)', weight: '17%' },
                ].map((s) => (
                  <Card key={s.name} variant="flat" className="flex items-center justify-between" style={{ padding: '12px 16px' }}>
                    <div><div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{s.name}</div><div className="caption">{s.ref}</div></div>
                    <span style={{ fontWeight: 600 }}>{s.weight}</span>
                  </Card>
                ))}
              </div>
            </Card>
          </div>

          <div className="flex-col gap-5">
            <Card className="fade-up fade-up-3">
              <div className="label mb-5">Action Taken</div>
              <Card variant="flat" className="mb-4" style={{ padding: 14 }}>
                <div className="label mb-3">Trades</div>
                <div className="flex items-center justify-between" style={{ padding: '8px 0', borderBottom: '1px solid var(--glass-border)' }}>
                  <div className="flex items-center gap-3"><span className="negative" style={{ fontWeight: 700, fontSize: '0.78rem' }}>SELL</span><span style={{ fontWeight: 600 }}>sTSLA</span></div>
                  <div className="text-right"><div style={{ fontWeight: 600 }}>94.62</div><div className="caption">≈ $27,200</div></div>
                </div>
                <div className="flex items-center justify-between" style={{ padding: '8px 0' }}>
                  <div className="flex items-center gap-3"><span className="positive" style={{ fontWeight: 700, fontSize: '0.78rem' }}>BUY</span><span style={{ fontWeight: 600 }}>USYC</span></div>
                  <div className="text-right"><div style={{ fontWeight: 600 }}>27,167.40</div><div className="caption">≈ $27,200</div></div>
                </div>
              </Card>
              <div className="grid g-2" style={{ gap: 8 }}>
                <Card variant="flat" style={{ padding: '10px 14px' }}><div className="caption">Cost</div><div style={{ fontWeight: 700 }}>$18.40</div></Card>
                <Card variant="flat" style={{ padding: '10px 14px' }}><div className="caption">Benefit</div><div className="positive" style={{ fontWeight: 700 }}>$312</div></Card>
                <Card variant="flat" style={{ padding: '10px 14px' }}><div className="caption">Vault Tx</div><div className="mono" style={{ fontSize: '0.75rem', color: 'var(--info)' }}>0x3f1a…8b2c</div></Card>
                <Card variant="flat" style={{ padding: '10px 14px' }}><div className="caption">Gas</div><div className="positive" style={{ fontWeight: 700 }}>$0.01</div></Card>
              </div>
            </Card>

            <Card className="fade-up fade-up-4">
              <div className="label mb-4">Before → After</div>
              <table style={{ width: '100%' }}>
                <thead><tr><th>Asset</th><th className="text-right">Before</th><th className="text-right">After</th><th className="text-right">Δ</th></tr></thead>
                <tbody>
                  {BEFORE_AFTER.map((row) => (
                    <tr key={row.asset} style={row.highlight ? { background: 'rgba(34,197,94,0.03)' } : {}}>
                      <td style={{ fontWeight: 500 }}>{row.asset}</td>
                      <td className="text-right">{row.before}</td>
                      <td className="text-right" style={{ fontWeight: 600 }}>{row.after}</td>
                      <td className={`text-right ${row.deltaClass}`} style={{ fontWeight: 600 }}>{row.delta}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>

            <Card className="fade-up fade-up-5">
              <div className="flex items-center justify-between mb-4">
                <div className="label">Tool Call Provenance</div>
                <span className="caption">6 calls · 842ms</span>
              </div>
              <div className="flex-col gap-2">
                {TOOL_CALLS.map((tc, i) => (
                  <Card key={i} variant="flat" className="flex items-center justify-between" style={{ padding: '8px 12px' }}>
                    <div className="flex items-center gap-3">
                      <Tag variant={tc.variant} style={{ fontSize: '0.6rem', padding: '2px 6px' }}>{tc.method}</Tag>
                      <span style={{ fontSize: '0.82rem', fontWeight: 500 }}>{tc.name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`caption ${tc.variant === 'positive' ? 'positive' : ''}`}>→ {tc.result}</span>
                      <span className="caption">{tc.time}</span>
                    </div>
                  </Card>
                ))}
              </div>
              <div className="caption mt-4">All inputs/outputs hashed into content hash. Each tool call independently verifiable.</div>
            </Card>
          </div>
        </div>

        <div className="flex justify-between mt-7">
          <button className="btn btn-ghost">← Trace #246</button>
          <button className="btn btn-outline btn-sm accent">Download Trace JSON</button>
          <button className="btn btn-ghost">Trace #248 →</button>
        </div>
      </div>
    </>
  )
}