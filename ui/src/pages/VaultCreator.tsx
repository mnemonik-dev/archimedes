import { Card, Stepper, Tag, AllocBar } from '../components/ui'
import { Topbar } from '../components/layout'

const STEPS = [
  { label: 'Name', number: 1, state: 'done' as const },
  { label: 'Assets', number: 2, state: 'done' as const },
  { label: 'Weights', number: 3, state: 'active' as const },
  { label: 'Fees', number: 4, state: 'pending' as const },
  { label: 'Deploy', number: 5, state: 'pending' as const },
]

const WEIGHTS = [
  { symbol: 'sTSLA', name: 'Synthetic Tesla', pct: 40, color: '#3B82F6', letter: 'T' },
  { symbol: 'sSPY', name: 'Synthetic S&P 500', pct: 30, color: '#6366F1', letter: 'S' },
  { symbol: 'USYC', name: 'Circle Yield', pct: 30, color: '#22C55E', letter: 'Y' },
]

export default function VaultCreator() {
  return (
    <>
      <Topbar label="Create Vault" />
      <div className="page" style={{ maxWidth: 780 }}>
        <Stepper steps={STEPS} />

        <Card className="mb-5 fade-up fade-up-1" style={{ opacity: 0.5 }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Tag variant="positive">Done</Tag>
              <div><span style={{ fontWeight: 600 }}>AI & Defense</span><span className="caption" style={{ marginLeft: 8 }}>vAIDEF · Community</span></div>
            </div>
            <button className="btn btn-ghost btn-sm">Edit</button>
          </div>
        </Card>

        <Card className="mb-5 fade-up fade-up-2" style={{ opacity: 0.5 }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Tag variant="positive">Done</Tag>
              <div><span style={{ fontWeight: 600 }}>3 assets selected</span><span className="caption" style={{ marginLeft: 8 }}>sTSLA · sSPY · USYC</span></div>
            </div>
            <button className="btn btn-ghost btn-sm">Edit</button>
          </div>
        </Card>

        <Card variant="elevated" className="mb-5 fade-up fade-up-3" style={{ borderColor: 'rgba(212,168,83,0.15)' }}>
          <div className="flex items-center justify-between mb-6">
            <h3>Set Target Weights</h3>
            <span className="caption">Remaining: <strong className="accent">0%</strong></span>
          </div>

          <AllocBar segs={WEIGHTS.map(w => ({ width: `${w.pct}%`, color: w.color }))} height={6} className="mb-6" />

          {WEIGHTS.map((w) => (
            <div key={w.symbol} style={{ borderBottom: '1px solid var(--glass-border)', padding: '16px 0' }}>
              <div className="flex items-center gap-4">
                <div className="asset-dot" style={{ background: w.color, width: 28, height: 28, fontSize: '0.68rem' }}>{w.letter}</div>
                <div style={{ width: 120 }}><div style={{ fontWeight: 600, fontSize: '0.88rem' }}>{w.symbol}</div><div className="caption">{w.name}</div></div>
                <div style={{ flex: 1 }}><input type="range" min={0} max={100} defaultValue={w.pct} /></div>
                <div style={{ width: 48, textAlign: 'right', fontWeight: 700, color: w.color }}>{w.pct}%</div>
              </div>
            </div>
          ))}

          <Card variant="flat" className="mt-5" style={{ padding: 14 }}>
            <div className="flex items-center gap-3 mb-2" style={{ fontSize: '0.82rem' }}>
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="var(--positive)" strokeWidth="1.5"/><path d="M5 8l2 2 4-4" stroke="var(--positive)" strokeWidth="1.5" strokeLinecap="round"/></svg>
              Weights sum to 100%
            </div>
            <div className="flex items-center gap-3 mb-2" style={{ fontSize: '0.82rem' }}>
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="var(--positive)" strokeWidth="1.5"/><path d="M5 8l2 2 4-4" stroke="var(--positive)" strokeWidth="1.5" strokeLinecap="round"/></svg>
              No single asset &gt; 50%
            </div>
            <div className="flex items-center gap-3" style={{ fontSize: '0.82rem' }}>
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="var(--positive)" strokeWidth="1.5"/><path d="M5 8l2 2 4-4" stroke="var(--positive)" strokeWidth="1.5" strokeLinecap="round"/></svg>
              USYC floor 30% (above 5% min)
            </div>
          </Card>

          <div className="flex justify-between mt-6">
            <button className="btn btn-ghost">← Assets</button>
            <button className="btn btn-primary">Fees →</button>
          </div>
        </Card>

        <Card className="mb-5 fade-up fade-up-4" style={{ opacity: 0.4 }}>
          <h3 className="mb-5">Fee Structure</h3>
          <div className="grid g-2">
            <div className="field"><label>Management Fee (Annual)</label><input type="number" defaultValue="1.00" disabled /></div>
            <div className="field"><label>Performance Fee (Above HWM)</label><input type="number" defaultValue="15.00" disabled /></div>
          </div>
        </Card>

        <Card className="fade-up fade-up-5" style={{ opacity: 0.4 }}>
          <h3 className="mb-5">Deploy</h3>
          <div className="card-flat mb-5" style={{ padding: 16 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <span className="caption">Vault</span><span style={{ fontWeight: 500, fontSize: '0.88rem' }}>AI & Defense (vAIDEF)</span>
              <span className="caption">Tier</span><span className="tier tier-community" style={{ width: 'fit-content' }}>Community</span>
              <span className="caption">Assets</span><span style={{ fontSize: '0.88rem' }}>sTSLA 40% · sSPY 30% · USYC 30%</span>
              <span className="caption">Fees</span><span style={{ fontSize: '0.88rem' }}>1.00% mgmt · 15% perf</span>
              <span className="caption">Agent</span><span className="positive" style={{ fontSize: '0.88rem' }}>Enabled (5% drift)</span>
              <span className="caption">Deploy cost</span><span className="positive" style={{ fontSize: '0.88rem' }}>~$0.05 Paymaster</span>
            </div>
          </div>
          <button className="btn btn-primary w-full btn-lg" disabled style={{ opacity: 0.4 }}>Deploy Vault to Arc</button>
        </Card>
      </div>
    </>
  )
}