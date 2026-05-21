import { useState, useEffect, useCallback } from 'react'
import {
  publicClient,
  VAULT_ABI, VAULT_FACTORY_ABI, NEW_CONTRACTS,
} from '../config'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

// Portfolio page — consolidates the old Dashboard + Vaults + Risk + agent
// activity into the single "what do I own and what is the agent doing"
// surface per docs/user-stories.md §④ Monitor. Wallet-gated — without a
// connected wallet we show the connect prompt rather than fake data.

function timeAgo(iso) {
  const d = typeof iso === 'string' ? new Date(iso) : new Date(iso * 1000)
  const secs = Math.floor((Date.now() - d.getTime()) / 1000)
  if (Number.isNaN(secs)) return '—'
  if (secs < 60) return `${secs}s ago`
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`
  return `${Math.floor(secs / 86400)}d ago`
}

function shortAddr(a) {
  return a ? `${a.slice(0, 6)}…${a.slice(-4)}` : '—'
}

export default function Portfolio({ walletAddr, onSelectVault, onSelectTrace }) {
  const [userVaults, setUserVaults] = useState([])
  const [agentStatus, setAgentStatus] = useState(null)
  const [regime, setRegime] = useState(null)
  const [recentTraces, setRecentTraces] = useState([])
  const [tracesLoading, setTracesLoading] = useState(false)
  const [vaultsLoading, setVaultsLoading] = useState(false)

  const loadVaults = useCallback(async () => {
    const factoryAddr = NEW_CONTRACTS.vaultFactory
    if (!factoryAddr || !walletAddr) { setUserVaults([]); return }
    setVaultsLoading(true)
    try {
      const creatorVaults = await publicClient.readContract({
        address: factoryAddr, abi: VAULT_FACTORY_ABI, functionName: 'getVaultsByCreator', args: [walletAddr],
      })
      const rows = await Promise.all((creatorVaults || []).map(async (addr) => {
        try {
          const [totalAssets, tier, name] = await Promise.all([
            publicClient.readContract({ address: addr, abi: VAULT_ABI, functionName: 'totalAssets' }),
            publicClient.readContract({ address: addr, abi: VAULT_ABI, functionName: 'tier' }),
            publicClient.readContract({ address: addr, abi: VAULT_ABI, functionName: 'name' }).catch(() => ''),
          ])
          return { address: addr, aum: Number(totalAssets) / 1e6, tier: Number(tier), name }
        } catch { return null }
      }))
      setUserVaults(rows.filter(Boolean))
    } catch {
      setUserVaults([])
    } finally {
      setVaultsLoading(false)
    }
  }, [walletAddr])

  const loadAgentAndRegime = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/api/agent/status`)
      if (r.ok) setAgentStatus(await r.json())
    } catch {}
    try {
      const r = await fetch(`${API_BASE}/api/regime/current`)
      if (r.ok) setRegime(await r.json())
    } catch {}
  }, [])

  const loadTraces = useCallback(async () => {
    setTracesLoading(true)
    try {
      const r = await fetch(`${API_BASE}/api/traces/?limit=20`)
      if (r.ok) {
        const data = await r.json()
        setRecentTraces(data.traces || [])
      }
    } catch {}
    setTracesLoading(false)
  }, [])

  useEffect(() => { loadVaults() }, [loadVaults])
  useEffect(() => { loadAgentAndRegime(); loadTraces() }, [loadAgentAndRegime, loadTraces])
  useEffect(() => {
    const t = setInterval(() => { loadAgentAndRegime(); loadTraces() }, 30_000)
    return () => clearInterval(t)
  }, [loadAgentAndRegime, loadTraces])

  const totalAum = userVaults.reduce((s, v) => s + v.aum, 0)

  return (
    <div>
      <div className="fade-up fade-up-1" style={{ maxWidth: 720, marginBottom: 24 }}>
        <h2 className="serif" style={{ fontSize: '2rem', marginBottom: 10 }}>Portfolio</h2>
        <p className="body">
          What you own, how the agent is managing it, and what it's been doing recently.
          Every rebalance has a reasoning trace anchored on Arc — click into any decision
          to inspect what the agent saw and why it acted.
        </p>
      </div>

      {!walletAddr && (
        <div className="info-box warning" style={{ marginBottom: 24 }}>
          Connect your wallet (top right) to load your vault positions. Agent activity
          and the live regime classification are visible without a wallet.
        </div>
      )}

      {/* Status strip — agent + regime are real (Redis-backed) regardless of wallet */}
      <div className="grid g-4" style={{ gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        <div className="card-flat" style={{ padding: 16 }}>
          <div className="label mb-2">Your Vaults</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700 }}>{walletAddr ? userVaults.length : '—'}</div>
          <div className="caption" style={{ marginTop: 6 }}>
            {walletAddr ? `${userVaults.filter(v => v.tier === 1).length} Tier 1 · ${userVaults.filter(v => v.tier === 2).length} Tier 2` : 'connect wallet'}
          </div>
        </div>
        <div className="card-flat" style={{ padding: 16 }}>
          <div className="label mb-2">Total AUM</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700 }}>
            {walletAddr ? `$${totalAum.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
          </div>
          <div className="caption positive" style={{ marginTop: 6 }}>Arc Testnet</div>
        </div>
        <div className="card-flat" style={{ padding: 16 }}>
          <div className="label mb-2">Agent</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700 }}>
            {agentStatus?.alive ? '🟢 Alive' : '🔴 Offline'}
          </div>
          <div className="caption" style={{ marginTop: 6 }}>
            Last heartbeat: {agentStatus?.last_heartbeat ? timeAgo(agentStatus.last_heartbeat) : '—'}
          </div>
        </div>
        <div className="card-flat" style={{ padding: 16 }}>
          <div className="label mb-2">Market Regime</div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, textTransform: 'capitalize' }}>
            {regime?.regime?.replace('_', ' ') || '—'}
          </div>
          <div className="caption" style={{ marginTop: 6 }}>
            {regime?.confidence != null ? `${(regime.confidence * 100).toFixed(0)}% confidence` : 'no data'}
          </div>
        </div>
      </div>

      {/* User vaults */}
      {walletAddr && (
        <div style={{ marginBottom: 28 }}>
          <div className="label mb-3">Your Vault Positions</div>
          {vaultsLoading && <div className="caption">Loading vaults…</div>}
          {!vaultsLoading && userVaults.length === 0 && (
            <div className="card" style={{ padding: 18 }}>
              <p className="body" style={{ marginBottom: 8 }}>You don't own any vaults yet.</p>
              <p className="caption">
                Go to <a href="/generate" style={{ color: 'var(--accent)' }}>Generate</a> to design a
                strategy, then deploy it into a non-custodial vault from the result card.
              </p>
            </div>
          )}
          {userVaults.length > 0 && (
            <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
              {userVaults.map(v => (
                <div key={v.address} className="card vault-card-clickable" onClick={() => onSelectVault?.(v.address)}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <code style={{ fontSize: '0.8rem' }}>{shortAddr(v.address)}</code>
                    <span className={`tag ${v.tier === 1 ? 'tag-accent' : 'tag-muted'}`}>T{v.tier}</span>
                  </div>
                  {v.name && <div className="caption" style={{ marginBottom: 4 }}>{v.name}</div>}
                  <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>${v.aum.toFixed(2)}</div>
                  <div className="caption">AUM</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Agent activity feed — real traces from /api/traces */}
      <div>
        <div className="label mb-3">Recent Agent Activity</div>
        {tracesLoading && <div className="caption">Loading traces…</div>}
        {!tracesLoading && recentTraces.length === 0 && (
          <div className="card" style={{ padding: 18 }}>
            <p className="body" style={{ marginBottom: 6 }}>No agent activity yet.</p>
            <p className="caption">
              The agent runner persists a reasoning trace every time it makes a decision.
              Construction traces from the Generate page also appear here.
            </p>
          </div>
        )}
        {recentTraces.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {recentTraces.map(t => (
              <div
                key={t.id}
                className="trace-card vault-card-clickable"
                onClick={() => onSelectTrace?.(t.id)}
                style={{ cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                  <div>
                    <span className="tag tag-muted" style={{ marginRight: 8, textTransform: 'capitalize' }}>{t.decision_type}</span>
                    <strong style={{ fontSize: '0.9rem' }}>{t.trigger}</strong>
                  </div>
                  <span className="caption">{t.timestamp ? timeAgo(t.timestamp) : ''}</span>
                </div>
                {t.reasoning && (
                  <div className="caption" style={{ marginTop: 6, lineHeight: 1.45 }}>
                    {t.reasoning.slice(0, 180)}{t.reasoning.length > 180 ? '…' : ''}
                  </div>
                )}
                <div className="caption" style={{ marginTop: 6, display: 'flex', gap: 12, color: 'var(--text-3)' }}>
                  {t.vault_address && <span>vault {shortAddr(t.vault_address)}</span>}
                  {t.trace_hash && <span className="mono">{t.trace_hash.slice(0, 10)}…</span>}
                  {t.is_verified ? <span className="positive">✓ anchored</span> : <span>off-chain only</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
