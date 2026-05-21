import { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

/**
 * CorrelationMatrix — compact pairwise correlation table for the strategy library.
 *
 * Fetches /api/strategies/correlation and renders a color-coded heatmap table:
 *   - Near 0  → green  (low correlation, good diversification)
 *   - Near 1  → red    (high correlation, less diversification benefit)
 *
 * Honest disclosure: all strategies track broad equity markets so
 * inter-strategy correlations are expected to be high.
 *
 * NOTE: Returns are simulated from summary statistics since raw daily series
 * are not stored in backtest_fixtures.json.
 */
export default function CorrelationMatrix() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    apiGet('/api/strategies/correlation')
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message || 'Failed to load correlation data'); setLoading(false) })
  }, [])

  if (loading) {
    return (
      <div className="card-flat" style={{ padding: 20 }}>
        <div className="label mb-2">Library Correlation</div>
        <div className="caption" style={{ color: 'var(--text-4)' }}>Computing correlation matrix…</div>
      </div>
    )
  }

  if (error || !data || !data.matrix || data.matrix.length === 0) {
    return (
      <div className="card-flat" style={{ padding: 20 }}>
        <div className="label mb-2">Library Correlation</div>
        <div className="caption" style={{ color: 'var(--text-4)' }}>
          {error || 'Need at least 2 strategies with real backtest data.'}
        </div>
      </div>
    )
  }

  const { matrix, labels, avg_pairwise_correlation, note } = data
  const n = labels.length

  /**
   * Colour interpolation: green (0) → neutral (0.5) → red (1).
   * Uses RGBA so it works on any background.
   */
  function cellColor(value) {
    const v = Math.max(0, Math.min(1, value))
    if (v <= 0.5) {
      // 0 → pure green, 0.5 → neutral
      const t = v * 2
      const r = Math.round(16 + t * (239 - 16))   // 16→239
      const g = Math.round(185 + t * (68 - 185))   // 185→68
      const b = Math.round(129 + t * (68 - 129))   // 129→68
      return `rgba(${r},${g},${b},${0.15 + t * 0.25})`
    } else {
      // 0.5 → neutral, 1 → pure red
      const t = (v - 0.5) * 2
      const r = Math.round(239)
      const g = Math.round(68 - t * 68)
      const b = Math.round(68 - t * 68)
      return `rgba(${r},${g},${b},${0.15 + t * 0.35})`
    }
  }

  function textColor(value) {
    return value > 0.7 ? 'var(--negative)' : value < 0.3 ? 'var(--positive)' : 'var(--text-2)'
  }

  // Short label for table header: trim to 12 chars
  function shortLabel(title) {
    return title.length > 12 ? title.slice(0, 11) + '…' : title
  }

  return (
    <div className="card-flat" style={{ padding: 20 }}>
      <div className="flex items-center justify-between mb-3">
        <div className="label">Library Correlation</div>
        {avg_pairwise_correlation != null && (
          <div className="caption" style={{ color: 'var(--text-3)', fontSize: '0.72rem' }}>
            avg pairwise: <strong style={{ color: avg_pairwise_correlation > 0.7 ? 'var(--negative)' : 'var(--text-1)' }}>
              {avg_pairwise_correlation.toFixed(3)}
            </strong>
          </div>
        )}
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: '0.75rem' }}>
          <thead>
            <tr>
              <th style={{ padding: '4px 8px', textAlign: 'left', color: 'var(--text-4)', fontWeight: 400, borderBottom: '1px solid var(--glass-border)', whiteSpace: 'nowrap' }}>
                Strategy
              </th>
              {labels.map((l, j) => (
                <th key={j} style={{
                  padding: '4px 6px', textAlign: 'center', color: 'var(--text-3)',
                  fontWeight: 400, borderBottom: '1px solid var(--glass-border)',
                  fontSize: '0.67rem', whiteSpace: 'nowrap',
                }}>
                  {shortLabel(l.title)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, i) => (
              <tr key={i}>
                <td style={{
                  padding: '4px 8px', color: 'var(--text-2)', fontWeight: 500,
                  borderBottom: '1px solid var(--glass-border)', whiteSpace: 'nowrap',
                  fontSize: '0.68rem',
                }}>
                  {shortLabel(labels[i].title)}
                  {labels[i].passes_rigor_gate && (
                    <span style={{ marginLeft: 4, color: 'var(--positive)', fontSize: '0.65rem' }}>T1</span>
                  )}
                </td>
                {row.map((val, j) => (
                  <td key={j} style={{
                    padding: '4px 6px', textAlign: 'center',
                    background: i === j ? 'rgba(255,255,255,0.06)' : cellColor(val),
                    borderBottom: '1px solid var(--glass-border)',
                    color: i === j ? 'var(--text-4)' : textColor(val),
                    fontWeight: i === j ? 400 : 600,
                    minWidth: 44,
                  }}>
                    {i === j ? '—' : val.toFixed(2)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {note && (
        <div className="caption" style={{ marginTop: 10, color: 'var(--text-4)', fontSize: '0.67rem', fontStyle: 'italic' }}>
          {note}
        </div>
      )}
      <div className="caption" style={{ marginTop: 4, color: 'var(--text-4)', fontSize: '0.67rem' }}>
        Returns simulated from backtest summary statistics. Raw daily series not stored in fixture file.
      </div>
    </div>
  )
}
