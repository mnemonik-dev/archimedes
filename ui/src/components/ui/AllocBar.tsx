import type { CSSProperties } from 'react'

interface Seg {
  width: string
  color: string
  borderRadius?: string
}

interface AllocBarProps {
  segs: Seg[]
  height?: number
  className?: string
  style?: CSSProperties
}

export default function AllocBar({ segs, height = 4, className = '', style }: AllocBarProps) {
  return (
    <div className={`alloc-bar ${className}`} style={{ height, ...style }}>
      {segs.map((seg, i) => (
        <div key={i} className="seg" style={{ width: seg.width, background: seg.color, borderRadius: seg.borderRadius || '1px' }} />
      ))}
    </div>
  )
}