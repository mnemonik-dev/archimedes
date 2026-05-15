import type { ReactNode } from 'react'
import { WalletChip } from '../ui'

interface TopbarProps {
  label?: string
  rightContent?: ReactNode
  walletAddress?: string | null
}

export default function Topbar({ label, rightContent, walletAddress }: TopbarProps) {
  return (
    <div className="topbar">
      <div className="flex items-center gap-4">
        {label && <span className="label">{label}</span>}
      </div>
      <div className="flex items-center gap-5">
        <span className="caption">Regime <strong className="positive">Risk-On</strong></span>
        {walletAddress ? (
          <WalletChip address={walletAddress} />
        ) : rightContent}
      </div>
    </div>
  )
}