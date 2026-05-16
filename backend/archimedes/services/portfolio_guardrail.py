"""Deterministic weight guardrail (Dan's lane — Step 2).

Claude (the architect, Step 1) proposes *relative emphasis* across
paper-grounded strategies. This module turns that into a structurally safe
book with hard, auditable rules — no model in the loop:

  1. Reserve the risk profile's USYC (cash-yield) floor.
  2. Normalize strategy weights into the remaining investable budget.
  3. Cap any single strategy at `max_per_strategy` of the whole book
     (design.md § 4.3.2), iteratively redistributing the excess.
  4. Anything that cannot be placed under the cap spills back to USYC.

Every adjustment is recorded in `notes` so the Step 3 reasoning trace can
state exactly what the guardrail did and why — provenance, not a black box.

Seam for Önder: this is the conservative stand-in for `IPortfolioConstructor`.
His risk-model optimizer (mean-variance / correlation-aware weighting + the
strategy→token expansion to `list[TargetAllocation]`) is the drop-in upgrade;
`apply_guardrail` deliberately takes the same `risk_profile` + strategy inputs
so the call site doesn't change when his implementation lands.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from archimedes.models.portfolio import RISK_PROFILE_PARAMS, RiskProfile
from archimedes.services.strategy_architect import ArchitectProposal

logger = logging.getLogger(__name__)

DEFAULT_MAX_PER_STRATEGY = 0.30  # design.md § 4.3.2: max 30% in any one strategy
_EPS = 1e-9


@dataclass
class GuardrailedAllocation:
    """Structurally safe allocation. Weights (incl. USYC) sum to 1.0."""

    strategy_weights: dict[str, float]  # strategy_id → fraction of whole book
    usyc_weight: float  # cash-yield sleeve (>= the risk-profile floor)
    risk_profile: str
    notes: list[str] = field(default_factory=list)

    @property
    def total(self) -> float:
        return sum(self.strategy_weights.values()) + self.usyc_weight


def apply_guardrail(
    proposal: ArchitectProposal,
    *,
    max_per_strategy: float = DEFAULT_MAX_PER_STRATEGY,
) -> GuardrailedAllocation:
    """Project an `ArchitectProposal` onto the risk profile's hard constraints.

    Pure and deterministic. Safe on degenerate input (no/zero-weight
    selections → full USYC). The cap loop is monotone and bounded by the
    number of strategies, so it always converges.
    """
    risk_profile = RiskProfile(proposal.risk_profile)
    usyc_floor = RISK_PROFILE_PARAMS[risk_profile]["usyc_floor"]
    notes: list[str] = []

    raw = {sid: w for sid, w in proposal.raw_weights.items() if w > _EPS}
    if not raw:
        notes.append(
            "No strategies selected (or all zero weight) — allocating the "
            "full book to USYC."
        )
        return GuardrailedAllocation(
            strategy_weights={},
            usyc_weight=1.0,
            risk_profile=risk_profile.value,
            notes=notes,
        )

    investable = 1.0 - usyc_floor
    if usyc_floor > 0:
        notes.append(
            f"Reserved {usyc_floor:.0%} USYC floor for the "
            f"'{risk_profile.value}' risk profile."
        )

    # Normalize into the investable budget.
    total_raw = sum(raw.values())
    weights = {sid: (w / total_raw) * investable for sid, w in raw.items()}

    # Iteratively cap and redistribute the excess across uncapped strategies.
    capped: set[str] = set()
    for _ in range(len(weights) + 1):
        over = {
            sid: w for sid, w in weights.items()
            if sid not in capped and w > max_per_strategy + _EPS
        }
        if not over:
            break
        for sid in over:
            weights[sid] = max_per_strategy
            capped.add(sid)
            notes.append(
                f"Capped strategy {sid[:12]} at {max_per_strategy:.0%} of the "
                f"book (single-strategy concentration limit)."
            )
        placed = sum(weights[s] for s in capped)
        remaining_budget = investable - placed
        free = {sid: weights[sid] for sid in weights if sid not in capped}
        free_total = sum(free.values())
        if remaining_budget <= _EPS or free_total <= _EPS:
            for sid in free:
                weights[sid] = 0.0
            break
        for sid in free:
            weights[sid] = (free[sid] / free_total) * remaining_budget

    strategy_weights = {sid: w for sid, w in weights.items() if w > _EPS}
    placed_total = sum(strategy_weights.values())
    usyc_weight = 1.0 - placed_total

    spill = usyc_weight - usyc_floor
    if spill > 1e-4:
        notes.append(
            f"{spill:.0%} could not be placed under the per-strategy cap with "
            f"the selected strategies — spilled into USYC (now {usyc_weight:.0%})."
        )

    # Guard against float drift: pin the total to exactly 1.0 via USYC.
    drift = 1.0 - (placed_total + usyc_weight)
    if abs(drift) > _EPS:
        usyc_weight += drift

    return GuardrailedAllocation(
        strategy_weights=strategy_weights,
        usyc_weight=usyc_weight,
        risk_profile=risk_profile.value,
        notes=notes,
    )
