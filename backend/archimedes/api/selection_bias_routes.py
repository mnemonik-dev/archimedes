"""Selection-bias correction API routes.

Exposes the rigor gate for strategy validation. The main consumer is the
strategy-list page (shows PASS/FAIL per strategy) and the strategy detail
page (shows full gate breakdown).
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query

from archimedes.api.schemas import StrategyListResponse, StrategyResponse
from archimedes.models.strategy import StrategyStatus
from archimedes.services.selection_bias import (
    RigorGateResult,
    compute_pbo,
    run_rigor_gate,
)
from archimedes.services.strategy_provider import default_provider

selection_bias_router = APIRouter(prefix="/api/selection-bias", tags=["selection-bias"])

_provider = default_provider()


# ── Schemas ──────────────────────────────────────────────────

from dataclasses import dataclass, field
from pydantic import BaseModel


class RigorGateDetail(BaseModel):
    """Per-check pass/fail detail."""
    dsr: str = "MISSING"
    pbo: str = "MISSING"
    oos_sharpe: str = "MISSING"
    look_ahead: str = "MISSING"


class StrategyRigorResult(BaseModel):
    """Rigor gate result for a single strategy."""
    strategy_id: str
    strategy_name: str
    passes_all: bool
    gate_details: RigorGateDetail
    deflated_sharpe: float | None = None
    dsr_p_value: float | None = None
    pbo_score: float | None = None
    oos_sharpe: float | None = None
    in_sample_sharpe: float | None = None


class RigorGateResponse(BaseModel):
    """Response for the library-level rigor gate check."""
    strategies: list[StrategyRigorResult]
    total: int
    passing: int
    failing: int


class PBORequest(BaseModel):
    """Request to compute PBO for a set of strategy returns."""
    returns_matrix: dict[str, list[float]]
    s_partitions: int = 16


class PBOResponse(BaseModel):
    """PBO computation result."""
    pbo_scores: dict[str, float]
    interpretation: str


# ── Endpoints ────────────────────────────────────────────────


@selection_bias_router.get("/gate", response_model=RigorGateResponse)
async def evaluate_rigor_gate():
    """Evaluate the rigor gate for all strategies in the library.

    Runs DSR, PBO, walk-forward OOS, and look-ahead audit for each
    strategy. Returns pass/fail per strategy with detailed breakdown.
    """
    strategies = _provider.list_strategies()

    if not strategies:
        return RigorGateResponse(strategies=[], total=0, passing=0, failing=0)

    # Collect daily returns from strategy backtest stubs
    # In production, these come from the analytics-engine BacktestResult.
    # For the hackathon demo, we generate synthetic returns from the stub metrics.
    returns_by_strategy: dict[str, list[float]] = {}
    strategy_code_map: dict[str, str | None] = {}

    for s in strategies:
        # Generate synthetic daily returns from stub metrics
        # This is a placeholder until the full analytics-engine integration
        if s.stub_sharpe is not None and s.strategy_code_path:
            returns = _synthetic_returns_from_stub(
                sharpe=s.stub_sharpe,
                cagr=s.stub_cagr,
                max_dd=s.stub_max_dd,
            )
            returns_by_strategy[s.id] = returns

            # Load strategy source code for look-ahead audit
            code = _load_strategy_code(s.strategy_code_path)
            strategy_code_map[s.id] = code
        else:
            # No stub data — can't evaluate
            returns_by_strategy[s.id] = []
            strategy_code_map[s.id] = None

    # Compute PBO across all strategies that have returns
    valid_returns = {k: v for k, v in returns_by_strategy.items() if len(v) >= 10}
    pbo_scores = compute_pbo(valid_returns) if len(valid_returns) >= 2 else {}

    num_trials = max(len(valid_returns), 1)

    # Run rigor gate for each strategy
    results: list[StrategyRigorResult] = []
    for s in strategies:
        daily_returns = returns_by_strategy.get(s.id, [])

        if len(daily_returns) < 10:
            results.append(StrategyRigorResult(
                strategy_id=s.id,
                strategy_name=s.paper_title,
                passes_all=False,
                gate_details=RigorGateDetail(
                    dsr="MISSING (no backtest data)",
                    pbo="MISSING (no backtest data)",
                    oos_sharpe="MISSING (no backtest data)",
                    look_ahead="MISSING (no code)",
                ),
            ))
            continue

        gate_result = run_rigor_gate(
            strategy_id=s.id,
            daily_returns=daily_returns,
            num_trials=num_trials,
            pbo_scores=pbo_scores,
            strategy_code=strategy_code_map.get(s.id),
            in_sample_sharpe=s.stub_sharpe,
            paper_claimed_sharpe=s.paper_claimed_sharpe,
        )

        details = gate_result.gate_details
        results.append(StrategyRigorResult(
            strategy_id=s.id,
            strategy_name=s.paper_title,
            passes_all=gate_result.passes_all,
            gate_details=RigorGateDetail(
                dsr=details.get("dsr", "MISSING"),
                pbo=details.get("pbo", "MISSING"),
                oos_sharpe=details.get("oos_sharpe", "MISSING"),
                look_ahead=details.get("look_ahead", "MISSING"),
            ),
            deflated_sharpe=gate_result.deflated_sharpe,
            dsr_p_value=gate_result.dsr_p_value,
            pbo_score=gate_result.pbo_score,
            oos_sharpe=gate_result.oos_sharpe,
            in_sample_sharpe=gate_result.in_sample_sharpe,
        ))

    passing = sum(1 for r in results if r.passes_all)
    return RigorGateResponse(
        strategies=results,
        total=len(results),
        passing=passing,
        failing=len(results) - passing,
    )


@selection_bias_router.get("/gate/{strategy_id}", response_model=StrategyRigorResult)
async def evaluate_strategy_rigor(strategy_id: str):
    """Evaluate rigor gate for a single strategy."""
    strategy = _provider.get_strategy(strategy_id)
    if strategy is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Strategy not found")

    # Reuse the full gate endpoint with single strategy
    # (the per-strategy computation is the same)
    from fastapi import HTTPException
    raise HTTPException(
        status_code=501,
        detail="Use GET /api/selection-bias/gate for full library evaluation",
    )


@selection_bias_router.post("/pbo", response_model=PBOResponse)
async def compute_pbo_endpoint(req: PBORequest):
    """Compute PBO across a set of strategy return series.

    This is the library-level metric — all strategies get the same score.
    """
    pbo_scores = compute_pbo(req.returns_matrix, s_partitions=req.s_partitions)

    score = list(pbo_scores.values())[0] if pbo_scores else 0.0
    if score >= 0.5:
        interpretation = (
            f"PBO={score:.4f}: The in-sample-optimal strategy is expected to "
            f"underperform the median out-of-sample. FAILED rigor gate."
        )
    else:
        interpretation = (
            f"PBO={score:.4f}: Low overfitting probability. PASSED rigor gate."
        )

    return PBOResponse(pbo_scores=pbo_scores, interpretation=interpretation)


# ── Helpers ──────────────────────────────────────────────────


def _synthetic_returns_from_stub(
    sharpe: float,
    cagr: float | None = None,
    max_dd: float | None = None,
    T: int = 504,  # ~2 years of daily data
) -> list[float]:
    """Generate synthetic daily returns matching stub Sharpe.

    This is a hackathon placeholder. In production, the analytics-engine
    runs the actual backtest and produces real BacktestResult.daily_returns.
    """
    import numpy as np

    rng = np.random.default_rng(hash(sharpe) % (2**32))

    # Target daily vol = 1% (reasonable for equity-like assets)
    daily_vol = 0.01
    # Target daily mean from annualized Sharpe
    daily_mean = sharpe * daily_vol / np.sqrt(252)

    returns = rng.normal(daily_mean, daily_vol, size=T).tolist()
    return returns


def _load_strategy_code(code_path: str) -> str | None:
    """Load strategy source code for look-ahead audit."""
    import os

    if not code_path:
        return None

    # Resolve relative to project root
    candidates = [
        code_path,
        os.path.join(os.getcwd(), code_path),
        os.path.join(os.getcwd(), "analytics-engine", code_path),
    ]

    for path in candidates:
        if os.path.isfile(path):
            try:
                with open(path) as f:
                    return f.read()
            except Exception:
                pass

    return None
