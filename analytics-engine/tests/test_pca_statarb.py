"""Test for the Phase 3 PCA / eigenportfolio stat-arb strategy.

Hermetic: a synthetic universe with a genuine common factor plus mean-reverting
idiosyncratic residuals (seeded RNG, no network), so the PCA decomposition and
residual s-score trade path are actually exercised. Real performance metrics
live in backtest_fixtures.json; this test guards the plumbing + trade path.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from archimedes_analytics_engine.engine import BacktestResult, run_multi_backtest

_STRATEGIES_DIR = Path(__file__).parent.parent / "strategies"
sys.path.insert(0, str(_STRATEGIES_DIR))
sys.path.insert(0, str(_STRATEGIES_DIR.parent / "src"))

_NAMES = ["SPY", "^N225", "GC=F", "TLT", "CL=F"]


def _factor_universe(n: int = 400, seed: int = 3) -> list[pd.DataFrame]:
    """Five feeds sharing a common factor with mean-reverting idiosyncratic noise."""
    rng = np.random.RandomState(seed)
    common = rng.normal(0.0, 0.008, n)
    frames = []
    for k in range(5):
        idio = np.zeros(n)
        for i in range(1, n):
            idio[i] = 0.85 * idio[i - 1] + rng.normal(0.0, 0.006)
        closes = [100.0 + 10.0 * k]
        for i in range(1, n):
            closes.append(closes[-1] * (1.0 + 0.0003 + common[i] * (0.8 + 0.1 * k) + idio[i]))
        idx = pd.date_range("2015-01-01", periods=n, freq="D")
        frames.append(
            pd.DataFrame(
                {
                    "Open": [c * 0.999 for c in closes],
                    "High": [c * 1.002 for c in closes],
                    "Low": [c * 0.998 for c in closes],
                    "Close": closes,
                    "Volume": [1_000] * n,
                },
                index=idx,
            )
        )
    return frames


def test_pca_statarb_loads_and_trades() -> None:
    from archimedes_analytics_engine.strategy_loader import load_strategy

    bundle = load_strategy(_STRATEGIES_DIR / "avellaneda_lee_2010_pca_statarb.py")
    assert bundle.cls.__name__ == "PCAStatArb"

    frames = _factor_universe()
    result = run_multi_backtest(frames, strategy_cls=bundle.cls, initial_cash=100_000.0, names=_NAMES)
    assert isinstance(result, BacktestResult)
    assert result.bars == 400
    assert result.look_ahead_audit_passed is True
    assert isinstance(result.daily_returns, list)
    assert len(result.daily_returns) > 0
    # On a factor-structured universe with mean-reverting residuals, the s-score
    # trade path must fire (at least one closed long/short round-trip).
    assert result.total_trades > 0
