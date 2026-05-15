interface WalletChipProps {
  address: string
  connected?: boolean
  onClick?: () => void
}

export default function WalletChip({ address, connected = true, onClick }: WalletChipProps) {
  return (
    <button className="wallet-chip" onClick={onClick}>
      <span className="dot" style={{ background: connected ? 'var(--positive)' : 'var(--text-4)' }} />
      {address}
    </button>
  )
}