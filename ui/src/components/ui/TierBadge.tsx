interface TierBadgeProps {
  tier: 'verified' | 'community'
  className?: string
}

export default function TierBadge({ tier, className = '' }: TierBadgeProps) {
  return <span className={`tier tier-${tier} ${className}`}>{tier === 'verified' ? 'Verified' : 'Community'}</span>
}