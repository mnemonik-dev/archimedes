import type { ReactNode } from 'react'

interface StatBlockProps {
  label: string
  value: ReactNode
  sub?: ReactNode
  className?: string
  size?: 'lg' | 'sm'
}

export default function StatBlock({ label, value, sub, className = '', size = 'lg' }: StatBlockProps) {
  return (
    <div className={className}>
      <div className="label mb-2">{label}</div>
      <div className={size === 'sm' ? 'stat-sm' : 'stat'}>{value}</div>
      {sub && <div className={`caption mt-4 ${typeof sub === 'string' && sub.startsWith('+') ? 'positive' : ''}`}>{sub}</div>}
    </div>
  )
}