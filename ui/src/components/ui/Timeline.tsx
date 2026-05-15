import type { ReactNode } from 'react'

interface TimelineItem {
  active?: boolean
  tag: ReactNode
  title: string
  description: ReactNode
  time?: string
}

interface TimelineProps {
  items: TimelineItem[]
}

export default function Timeline({ items }: TimelineProps) {
  return (
    <div className="timeline">
      {items.map((item, i) => (
        <div key={i} className={`tl-item${item.active ? ' active' : ''}`}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              {item.tag}
              <span style={{ fontWeight: 600, fontSize: '0.88rem' }}>{item.title}</span>
            </div>
            {item.time && <span className="caption">{item.time}</span>}
          </div>
          <div className="body" style={{ fontSize: '0.82rem' }}>{item.description}</div>
        </div>
      ))}
    </div>
  )
}