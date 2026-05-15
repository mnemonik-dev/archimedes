import { Topbar } from '../components/layout'
import { Card, Tag } from '../components/ui'

const POOLS = [
  { pair: 'USDC / sTSLA', fee: '0.3%', tvl: '$842K', vol24h: '$124K', apr: '16.2%', highlight: false },
  { pair: 'USDC / sBTC', fee: '0.3%', tvl: '$1.2M', vol24h: '$342K', apr: '24.8%', highlight: false },
  { pair: 'USDC / sSPY', fee: '0.3%', tvl: '$621K', vol24h: '$89K', apr: '12.4%', highlight: false },
  { pair: 'USDC / USYC', fee: '0.05%', tvl: '$2.1M', vol24h: '$421K', apr: '5.4%', highlight: false },
  { pair: 'USDC / vMOMENTUM', fee: '0.3%', tvl: '$182K', vol24h: '$28K', apr: '+0.4%', highlight: true },
]

export default function Swap() {
  return (
    <>
      <Topbar label="Trade" />
      <div className="page">
        <div className="tabs">
          <button className="tab active">Swap</button>
          <button className="tab">Pools</button>
          <button className="tab">My Positions</button>
        </div>

        <div className="grid g-2" style={{ gridTemplateColumns: '1fr 1fr', gap: 48 }}>
          <div>
            <div style={{ maxWidth: 440, margin: '0 auto' }} className="fade-up fade-up-1">
              <div className="swap-token-input mb-2">
                <div className="flex justify-between mb-3">
                  <span className="caption">From</span>
                  <span className="caption">Balance: <strong style={{ color: 'var(--text-2)' }}>3,240.00</strong></span>
                </div>
                <div className="flex items-center justify-between">
                  <input type="text" className="swap-amount" defaultValue="1,000" />
                  <div className="token-pill">
                    <div className="token-dot" style={{ background: '#3B82F6', color: 'white' }}>U</div>
                    USDC ▾
                  </div>
                </div>
                <div className="caption mt-4">≈ $1,000.00</div>
              </div>

              <div className="flex justify-center" style={{ margin: '-6px 0' }}>
                <button style={{ width: 36, height: 36, borderRadius: 10, border: '3px solid var(--canvas)', background: 'var(--surface-2)', color: 'var(--text-3)', fontSize: '1rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', zIndex: 2 }}>↕</button>
              </div>

              <div className="swap-token-input mb-5" style={{ marginTop: -6 }}>
                <div className="flex justify-between mb-3">
                  <span className="caption">To</span>
                  <span className="caption">Balance: <strong style={{ color: 'var(--text-2)' }}>0.00</strong></span>
                </div>
                <div className="flex items-center justify-between">
                  <input type="text" className="swap-amount" defaultValue="3.481" readOnly style={{ color: 'var(--positive)' }} />
                  <div className="token-pill">
                    <div className="token-dot" style={{ background: '#3B82F6', color: 'white' }}>T</div>
                    sTSLA ▾
                  </div>
                </div>
                <div className="caption mt-4">≈ $1,000.47</div>
              </div>

              <Card variant="flat" style={{ padding: 14, marginBottom: 20 }}>
                <div className="flex justify-between caption mb-2"><span>Rate</span><span style={{ color: 'var(--text-2)' }}>1 sTSLA = 287.42 USDC</span></div>
                <div className="flex justify-between caption mb-2"><span>Price impact</span><span className="positive">&lt; 0.01%</span></div>
                <div className="flex justify-between caption mb-2"><span>Fee (0.3%)</span><span style={{ color: 'var(--text-2)' }}>3.00 USDC</span></div>
                <div className="flex justify-between caption mb-2"><span>Min received</span><span style={{ color: 'var(--text-2)' }}>3.464 sTSLA</span></div>
                <div className="flex justify-between caption"><span>Gas</span><span className="positive">~$0.01 Paymaster</span></div>
              </Card>

              <button className="btn btn-primary w-full btn-lg">Swap</button>
              <div className="caption text-center mt-4">AMM · Constant Product · USDC/sTSLA</div>
            </div>
          </div>

          <div>
            <div className="label mb-5 fade-up fade-up-2">Liquidity Pools</div>
            <div className="flex-col gap-3">
              {POOLS.map((p, i) => (
                <Card key={p.pair} className={`fade-up fade-up-${Math.min(i + 2, 5)}`} style={p.highlight ? { borderColor: 'rgba(212,168,83,0.12)' } : {}}>
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{p.pair}</div>
                      <div className="caption">Fee: {p.fee}</div>
                    </div>
                    <button className="btn btn-outline btn-sm">+ Add</button>
                  </div>
                  <div className="flex gap-5">
                    <div><div className="caption">TVL</div><div style={{ fontWeight: 700 }}>{p.tvl}</div></div>
                    <div><div className="caption">24h Vol</div><div style={{ fontWeight: 700 }}>{p.vol24h}</div></div>
                    <div><div className="caption">{p.highlight ? 'Prem.' : 'APR'}</div><div className="positive" style={{ fontWeight: 700 }}>{p.apr}</div></div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}