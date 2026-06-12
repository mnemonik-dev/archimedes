"""Tests for portfolio_backtester Phase 2.2 additions.

Covers the three new functions that do NOT require network access:
  - monte_carlo_portfolio: only needs a list[float] return series
  - sensitivity_sweep: tested with a mock to avoid yfinance calls
  - walk_forward_validate: tested with a mock to avoid yfinance calls

Hermetic: no network, no DB, no .env. Follows the existing pattern in
test_rigor_evaluator.py — mock only at system boundaries.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest


# ─── monte_carlo_portfolio ───────────────────────────────────────────


class TestMonteCarlPortfolio:
    """Unit tests for monte_carlo_portfolio (pure computation, no network)."""

    def _pos_returns(self, n: int = 500) -> list[float]:
        rng = np.random.default_rng(42)
        return list(rng.normal(0.001, 0.01, n))

    def test_returns_expected_keys(self):
        from archimedes.services.portfolio_backtester import monte_carlo_portfolio

        result = monte_carlo_portfolio(self._pos_returns(), n_trials=100, seed=0)
        for key in (
            "observed_sharpe",
            "observed_cagr",
            "observed_max_dd",
            "observed_sortino",
            "sharpe_ci_95",
            "cagr_ci_95",
            "max_dd_ci_95",
            "sortino_ci_95",
            "trial_sharpes",
            "trial_cagrs",
            "trial_max_dds",
            "pct_positive_sharpe",
            "n_trials",
            "block_size",
        ):
            assert key in result, f"Missing key: {key}"

    def test_ci_bounds_ordered(self):
        from archimedes.services.portfolio_backtester import monte_carlo_portfolio

        result = monte_carlo_portfolio(self._pos_returns(), n_trials=200, seed=1)
        for ci_key in ("sharpe_ci_95", "cagr_ci_95", "max_dd_ci_95", "sortino_ci_95"):
            lo, hi = result[ci_key]
            assert lo <= hi, f"{ci_key}: lower bound {lo} > upper bound {hi}"

    def test_n_trials_matches_output_length(self):
        from archimedes.services.portfolio_backtester import monte_carlo_portfolio

        n = 150
        result = monte_carlo_portfolio(self._pos_returns(), n_trials=n, seed=2)
        assert len(result["trial_sharpes"]) == n
        assert len(result["trial_cagrs"]) == n
        assert len(result["trial_max_dds"]) == n
        assert result["n_trials"] == n

    def test_max_dd_non_negative(self):
        """Drawdown is always ≥ 0."""
        from archimedes.services.portfolio_backtester import monte_carlo_portfolio

        result = monte_carlo_portfolio(self._pos_returns(), n_trials=100, seed=3)
        assert result["observed_max_dd"] >= 0.0
        assert all(v >= 0.0 for v in result["trial_max_dds"])

    def test_pct_positive_sharpe_in_unit_interval(self):
        from archimedes.services.portfolio_backtester import monte_carlo_portfolio

        result = monte_carlo_portfolio(self._pos_returns(), n_trials=200, seed=4)
        assert 0.0 <= result["pct_positive_sharpe"] <= 1.0

    def test_reproducible_with_same_seed(self):
        from archimedes.services.portfolio_backtester import monte_carlo_portfolio

        rets = self._pos_returns()
        r1 = monte_carlo_portfolio(rets, n_trials=100, seed=99)
        r2 = monte_carlo_portfolio(rets, n_trials=100, seed=99)
        assert r1["trial_sharpes"] == r2["trial_sharpes"]

    def test_different_seeds_differ(self):
        from archimedes.services.portfolio_backtester import monte_carlo_portfolio

        rets = self._pos_returns()
        r1 = monte_carlo_portfolio(rets, n_trials=100, seed=1)
        r2 = monte_carlo_portfolio(rets, n_trials=100, seed=2)
        assert r1["trial_sharpes"] != r2["trial_sharpes"]

    def test_positive_drift_series_mostly_positive_sharpe(self):
        """Strong positive drift should yield high pct_positive_sharpe."""
        from archimedes.services.portfolio_backtester import monte_carlo_portfolio

        rng = np.random.default_rng(0)
        pos_rets = list(rng.normal(0.003, 0.005, 600))
        result = monte_carlo_portfolio(pos_rets, n_trials=300, seed=5)
        assert result["pct_positive_sharpe"] > 0.90

    def test_raises_on_too_short_series(self):
        from archimedes.services.portfolio_backtester import monte_carlo_portfolio

        with pytest.raises(ValueError, match="block bootstrap"):
            monte_carlo_portfolio([0.001] * 5, n_trials=100, block_size=20)


# ─── sensitivity_sweep (mocked) ──────────────────────────────────────


class TestSensitivitySweep:
    """Tests for sensitivity_sweep using mocked backtest calls."""

    def _mock_backtest_result(self, sharpe: float) -> MagicMock:
        r = MagicMock()
        r.sharpe_ratio = sharpe
        return r

    def test_raises_on_empty_param_grid(self):
        from archimedes.services.portfolio_backtester import sensitivity_sweep

        with pytest.raises(ValueError, match="param_grid must contain"):
            sensitivity_sweep(
                strategy_id="s1",
                weights={"SPY": 1.0},
                param_grid={"unknown_param": [1, 2]},
            )

    def test_grid_length_matches_combinations(self):
        from archimedes.services.portfolio_backtester import sensitivity_sweep

        with patch("archimedes.services.portfolio_backtester.backtest_portfolio") as mock_bp:
            mock_bp.return_value = (self._mock_backtest_result(0.8), {})
            result = sensitivity_sweep(
                strategy_id="s1",
                weights={"SPY": 1.0},
                param_grid={"rebalance_days": [10, 21, 42], "tx_cost_bps": [5, 15]},
            )
        # 3 × 2 = 6 combinations
        assert len(result["grid"]) == 6

    def test_best_and_worst_params_present(self):
        from archimedes.services.portfolio_backtester import sensitivity_sweep

        sharpes = [0.3, 0.9, 0.5, 1.2]
        call_count = [0]

        def fake_backtest(**kw):
            s = sharpes[call_count[0] % len(sharpes)]
            call_count[0] += 1
            return (self._mock_backtest_result(s), {})

        with patch("archimedes.services.portfolio_backtester.backtest_portfolio", side_effect=fake_backtest):
            result = sensitivity_sweep(
                strategy_id="s1",
                weights={"SPY": 1.0},
                param_grid={"rebalance_days": [10, 21, 42, 63]},
            )

        assert result["best_params"] is not None
        assert result["worst_params"] is not None
        assert result["metric_range"][0] <= result["metric_range"][1]

    def test_sensitivity_ratio_computed(self):
        from archimedes.services.portfolio_backtester import sensitivity_sweep

        # Two values far apart → large sensitivity ratio
        call_sharpes = [2.0, 0.1]
        call_count = [0]

        def fake_backtest(**kw):
            s = call_sharpes[call_count[0] % 2]
            call_count[0] += 1
            return (self._mock_backtest_result(s), {})

        with patch("archimedes.services.portfolio_backtester.backtest_portfolio", side_effect=fake_backtest):
            result = sensitivity_sweep(
                strategy_id="s1",
                weights={"SPY": 1.0},
                param_grid={"rebalance_days": [10, 63]},
            )

        assert result["sensitivity_ratio"] > 0.5, "Wide spread should yield sensitivity_ratio > 0.5"


# ─── walk_forward_validate (mocked) ──────────────────────────────────


class TestWalkForwardValidate:
    """Tests for walk_forward_validate using mocked backtest calls."""

    def _mock_result(self, sharpe: float) -> MagicMock:
        r = MagicMock()
        r.sharpe_ratio = sharpe
        return r

    def test_output_keys_present(self):
        from archimedes.services.portfolio_backtester import walk_forward_validate

        with patch("archimedes.services.portfolio_backtester.backtest_portfolio") as mock_bp:
            mock_bp.return_value = (self._mock_result(0.8), {})
            result = walk_forward_validate(
                strategy_id="s1",
                weights={"SPY": 1.0},
                start_date="2015-01-01",
                end_date="2023-01-01",
                n_splits=3,
            )

        for key in (
            "splits",
            "mean_is_sharpe",
            "mean_oos_sharpe",
            "mean_cliff",
            "max_cliff",
            "passes_cliff_gate",
            "n_splits",
        ):
            assert key in result

    def test_n_splits_matches_output(self):
        from archimedes.services.portfolio_backtester import walk_forward_validate

        with patch("archimedes.services.portfolio_backtester.backtest_portfolio") as mock_bp:
            mock_bp.return_value = (self._mock_result(1.0), {})
            result = walk_forward_validate(
                strategy_id="s1",
                weights={"SPY": 1.0},
                start_date="2010-01-01",
                end_date="2023-01-01",
                n_splits=5,
            )
        assert result["n_splits"] == 5
        assert len(result["splits"]) == 5

    def test_passes_cliff_gate_when_no_degradation(self):
        """IS = OOS → cliff = 0 → should pass the gate."""
        from archimedes.services.portfolio_backtester import walk_forward_validate

        with patch("archimedes.services.portfolio_backtester.backtest_portfolio") as mock_bp:
            mock_bp.return_value = (self._mock_result(1.0), {})
            result = walk_forward_validate(
                strategy_id="s1",
                weights={"SPY": 1.0},
                start_date="2010-01-01",
                end_date="2023-01-01",
                n_splits=4,
            )
        assert result["passes_cliff_gate"] is True

    def test_fails_cliff_gate_when_severe_degradation(self):
        """IS Sharpe 2.0, OOS Sharpe 0.5 → cliff = 0.75 > 0.30 → fails gate."""
        from archimedes.services.portfolio_backtester import walk_forward_validate

        call_count = [0]

        def alternating(**kw):
            # Even calls = IS (sharpe 2.0), odd calls = OOS (sharpe 0.5)
            s = 2.0 if call_count[0] % 2 == 0 else 0.5
            call_count[0] += 1
            return (self._mock_result(s), {})

        with patch("archimedes.services.portfolio_backtester.backtest_portfolio", side_effect=alternating):
            result = walk_forward_validate(
                strategy_id="s1",
                weights={"SPY": 1.0},
                start_date="2010-01-01",
                end_date="2023-01-01",
                n_splits=4,
            )
        assert result["passes_cliff_gate"] is False

    def test_raises_on_period_too_short(self):
        from archimedes.services.portfolio_backtester import walk_forward_validate

        with pytest.raises(ValueError, match="Period too short"):
            walk_forward_validate(
                strategy_id="s1",
                weights={"SPY": 1.0},
                start_date="2023-01-01",
                end_date="2023-03-01",  # only ~60 days
                n_splits=5,
            )
