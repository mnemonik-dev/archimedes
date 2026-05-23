"""Verify DSL-interpreted Faber matches hand-written Faber within tolerance on real SPY data.

These tests confirm that the DSL interpretation pipeline produces backtest
metrics directionally consistent with the hand-curated seed strategy when run
on actual market data (SPY 2004-2026).

The SPY OHLCV CSV is a pre-generated fixture — no yfinance at test time.
"""

from __future__ import annotations

from pathlib import Path

from archimedes.services.fusion_evaluator import run_dsl_backtest
from archimedes.services.strategy_dsl import FABER_2007_SPEC, validate_strategy_spec

FIXTURE = Path(__file__).parent.parent / "fixtures" / "spy_ohlcv_2004_2026.csv"

SEED_SHARPE = 0.6335
SEED_MAX_DRAWDOWN = 0.246
TOLERANCE = 0.10


def test_dsl_faber_sharpe_within_010_of_seed_on_real_spy():
    """DSL Faber Sharpe must be within ±0.10 of the seed Faber Sharpe (0.6335) on real SPY data."""
    spec = validate_strategy_spec(FABER_2007_SPEC)
    result = run_dsl_backtest(spec, data_csv_path=FIXTURE)

    delta = abs(result.sharpe_ratio - SEED_SHARPE)
    assert delta < TOLERANCE, (
        f"DSL Faber Sharpe {result.sharpe_ratio} differs from seed {SEED_SHARPE} "
        f"by {delta:.4f}, exceeding tolerance {TOLERANCE}"
    )


def test_dsl_faber_drawdown_directionally_matches_seed_on_real_spy():
    """DSL Faber max drawdown must be within ±0.10 of the seed max drawdown (0.246) on real SPY data."""
    spec = validate_strategy_spec(FABER_2007_SPEC)
    result = run_dsl_backtest(spec, data_csv_path=FIXTURE)

    delta = abs(result.max_drawdown - SEED_MAX_DRAWDOWN)
    assert delta < TOLERANCE, (
        f"DSL Faber max drawdown {result.max_drawdown} differs from seed {SEED_MAX_DRAWDOWN} "
        f"by {delta:.4f}, exceeding tolerance {TOLERANCE}"
    )
