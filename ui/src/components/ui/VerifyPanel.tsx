import type { ReactNode } from 'react'

interface VerifyPanelProps {
  children: ReactNode
  className?: string
}

export default function VerifyPanel({ children, className = '' }: VerifyPanelProps) {
  return <div className={`verify-panel ${className}`}>{children}</div>
}