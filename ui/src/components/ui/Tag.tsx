import type { ReactNode, CSSProperties } from 'react'

interface TagProps {
  variant?: 'accent' | 'muted' | 'positive' | 'negative'
  className?: string
  style?: CSSProperties
  children: ReactNode
}

export default function Tag({ variant = 'muted', className = '', style, children }: TagProps) {
  return <span className={`tag tag-${variant} ${className}`} style={style}>{children}</span>
}