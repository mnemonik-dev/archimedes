"""Tests for the walk-forward parameter-selection harness.

Hermetic: synthetic data, no network. The load-bearing test is the
look-ahead proof: when the regime flips exactly at a fold's train/test
boundary, the harness must pick the train-optimal parameter and lose
out-of-sample — picking the test-optimal one would mean it peeked.
"""

from __future__ import annotations

import math

import backtrader as bt
import pandas as pd
import pytest
from archimedes_analytics_engine.engine import run_backtest
from archimedes_analytics_engine.walk_forward import WalkForwardResult, walk_forward_select


def _frame(closes: list[float], start: str = "2018-01-01") -> pd.DataFrame:
    idx = pd.date_range(start, periods=len(closes), freq="D")
    return pd.DataFrame(
        {
            "Open": closes,
            "High": [c * 1.004 for c in closes],
            "Low": [c * 0.996 for c in closes],
            "Close": closes,
            "Volume": [1_000] * len(closes),
        },
        index=idx,
    )


def _uptrend(n: int, base: float = 100.0, slope: float = 0.3) -> list[float]:
    return [base + slope * i + 1.5 * math.sin(i / 6.0) for i in range(n)]


def _up_then_down(n_up: int, n_down: int) -> list[float]:
    up = _uptrend(n_up)
    peak = up[-1]
    down = [peak - 0.4 * i + 1.5 * math.sin(i / 6.0) for i in range(1, n_down + 1)]
    return up + down


class _ExposureStrategy(bt.Strategy):
    """Holds a constant target exposure — the simplest selectable parameter."""

    params = (("invested", 0.0),)

    def next(self) -> None:
        target = float(self.params.invested)
        if len(self) == 2 and target > 0 and not self.position:
            self.order_target_percent(target=target)


class _SmaTrender(bt.Strategy):
    """Long above its SMA — has a real warm-up period (param-selectable)."""

    params = (("period", 20),)

    def __init__(self) -> None:
        self.sma = bt.indicators.SMA(self.data.close, period=int(self.params.period))

    def next(self) -> None:
        if self.data.close[0] > self.sma[0] and not self.position:
            self.order_target_percent(target=0.95)
        elif self.data.close[0] < self.sma[0] and self.position:
            self.order_target_percent(target=0.0)


# ── Engine passthrough prerequisite ───────────────────────────────────────────


def test_strategy_params_flow_through_runner() -> None:
    prices = _frame(_uptrend(60))
    flat = run_backtest(
        prices, strategy_cls=_ExposureStrategy, initial_cash=100_000.0, strategy_params={"invested": 0.0}
    )
    longed = run_backtest(
        prices, strategy_cls=_ExposureStrategy, initial_cash=100_000.0, strategy_params={"invested": 0.9}
    )
    assert flat.traded_notional == 0.0
    assert longed.traded_notional > 0.0
    assert longed.final_value != flat.final_value


# ── Fold mechanics ────────────────────────────────────────────────────────────


def test_fold_layout_and_stitching() -> None:
    result = walk_forward_select(
        _frame(_uptrend(300)),
        strategy_cls=_ExposureStrategy,
        param_grid={"invested": [0.0, 0.9]},
        initial_cash=100_000.0,
        train_bars=100,
        test_bars=50,
    )
    assert isinstance(result, WalkForwardResult)
    assert len(result.folds) == 4  # (300 - 100) // 50
    assert result.n_param_combos == 2
    assert len(result.oos_daily_returns) == 4 * 50
    for k, fold in enumerate(result.folds):
        assert fold.fold == k
        assert len(fold.test_returns) == 50
        assert fold.train_end < fold.test_start  # train strictly precedes test


def test_uptrend_selects_invested_every_fold() -> None:
    result = walk_forward_select(
        _frame(_uptrend(300)),
        strategy_cls=_ExposureStrategy,
        param_grid={"invested": [0.0, 0.9]},
        initial_cash=100_000.0,
        train_bars=100,
        test_bars=50,
    )
    assert all(f.chosen_params == {"invested": 0.9} for f in result.folds)
    assert result.oos_sharpe is not None and result.oos_sharpe > 0


def test_look_ahead_proof_regime_flip_at_boundary() -> None:
    # Up for 200 bars, then straight down. With train=100/test=50, fold 2
    # trains on bars 100-199 (all uptrend) and tests on 200-249 (all downtrend).
    # A peeking selector would choose invested=0.0 for that fold; an honest one
    # must choose the train-optimal invested=0.9 and lose out-of-sample.
    result = walk_forward_select(
        _frame(_up_then_down(200, 100)),
        strategy_cls=_ExposureStrategy,
        param_grid={"invested": [0.0, 0.9]},
        initial_cash=100_000.0,
        train_bars=100,
        test_bars=50,
    )
    boundary_fold = result.folds[2]
    assert boundary_fold.chosen_params == {"invested": 0.9}  # train-optimal, NOT test-optimal
    assert sum(boundary_fold.test_returns) < 0  # and it pays for it out-of-sample


def test_warm_up_draws_on_train_bars_not_cold_start() -> None:
    # The chosen strategy has a 20-bar SMA. Because evaluation runs over
    # train+test (slicing only the test tail), the position carries into the
    # test window — early test bars must show market exposure, not a cold start.
    result = walk_forward_select(
        _frame(_uptrend(220)),
        strategy_cls=_SmaTrender,
        param_grid={"period": [10, 20]},
        initial_cash=100_000.0,
        train_bars=150,
        test_bars=70,
    )
    first_fold = result.folds[0]
    assert any(r != 0.0 for r in first_fold.test_returns[:5])


# ── Input validation ──────────────────────────────────────────────────────────


def test_rejects_empty_grid() -> None:
    with pytest.raises(ValueError, match="param_grid"):
        walk_forward_select(
            _frame(_uptrend(200)),
            strategy_cls=_ExposureStrategy,
            param_grid={},
            initial_cash=100_000.0,
            train_bars=100,
            test_bars=50,
        )
    with pytest.raises(ValueError, match="param_grid"):
        walk_forward_select(
            _frame(_uptrend(200)),
            strategy_cls=_ExposureStrategy,
            param_grid={"invested": []},
            initial_cash=100_000.0,
            train_bars=100,
            test_bars=50,
        )


def test_rejects_data_shorter_than_one_fold() -> None:
    with pytest.raises(ValueError, match="aligned bars"):
        walk_forward_select(
            _frame(_uptrend(120)),
            strategy_cls=_ExposureStrategy,
            param_grid={"invested": [1.0]},
            initial_cash=100_000.0,
            train_bars=100,
            test_bars=50,
        )


# ── Multi-feed support ────────────────────────────────────────────────────────


class _PickALeg(bt.Strategy):
    """Goes long one feed chosen by parameter — selectable across feeds."""

    params = (("leg", 0),)

    def next(self) -> None:
        if len(self) == 2 and not self.getposition(self.datas[int(self.params.leg)]).size:
            self.order_target_percent(data=self.datas[int(self.params.leg)], target=0.95)


def test_multi_feed_walk_forward_selects_winning_leg() -> None:
    n = 240
    up = _frame(_uptrend(n))
    down = _frame([200.0 - 0.3 * i + 1.5 * math.sin(i / 6.0) for i in range(n)])
    result = walk_forward_select(
        [up, down],
        strategy_cls=_PickALeg,
        param_grid={"leg": [0, 1]},
        initial_cash=100_000.0,
        train_bars=120,
        test_bars=60,
        names=["UP", "DOWN"],
    )
    assert len(result.folds) == 2
    assert all(f.chosen_params == {"leg": 0} for f in result.folds)
    assert result.oos_sharpe is not None and result.oos_sharpe > 0
