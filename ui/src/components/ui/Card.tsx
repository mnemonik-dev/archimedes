import type { ReactNode, CSSProperties } from 'react'

interface CardProps {
  variant?: 'default' | 'flat' | 'elevated'
  className?: string
  style?: CSSProperties
  children: ReactNode
}

export default function Card({ variant = 'default', className = '', style, children }: CardProps) {
  const variantClass = variant === 'flat' ? 'card-flat' : variant === 'elevated' ? 'card-elevated' : 'card'
  return <div className={`${variantClass} ${className}`} style={style}>{children}</div>
}