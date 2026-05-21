"""Mean-variance portfolio optimizer for the three vault risk profiles.

Maps RiskProfile → optimization objective:

  CONSERVATIVE  → Global Minimum Variance: min w'Σw
  MODERATE      → Max Sharpe: max (μ-rf)'w / sqrt(w'Σw)
  AGGRESSIVE    → Max Sharpe (same objective, looser USYC floor applied upstream)
  HYPER_RISKY   → Max Expected Return: max μ'w  (LP — concentrates in top-μ assets)

All objectives are solved on the long-only unit simplex with a per-asset weight
cap to prevent degenerate concentration. Falls back to equal weight if scipy
optimization fails or price history is too short (< 20 bars).

Owner: Önder (math lane)
Spec:  docs/specs/ecosystem-design-spec.md § 3.3, models/portfolio.py
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from archimedes.models.portfolio import RISK_PROFILE_PARAMS, RiskProfile

logger = logging.getLogger(__name__)

_ANNUALIZATION = 252
_RF_DAILY = 0.05 / _ANNUALIZATION  # 5% annual risk-free rate

# Per-asset caps — prevent degenerate corner solutions
_CAP_DEFAULT = 0.40   # Conservative / Moderate / Aggressive
_CAP_HYPER = 0.60     # Hyper-Risky: higher concentration is the intent

_MIN_BARS = 20        # Minimum history required before MVO is meaningful


# ─── Kelly mean-variance: γ-mapped risk aversion ──────────────────
# γ = 2 reproduces half-Kelly (Bell & Cover 1980); γ → 0 = full Kelly;
# γ → ∞ collapses to minimum-variance.  Risk profile controls γ.
RISK_AVERSION: dict[str, float] = {
    "fixed_income": 12.0,
    "conservative": 6.0,
    "moderate":     3.0,
    "aggressive":   2.0,
    "hyper_risky":  1.5,
}


@dataclass
class KellyOptimizationResult:
    """Output of the constrained Kelly mean-variance optimizer."""

    symbols: list[str]                 # synth codes (e.g. 'sNVDA')
    weights: np.ndarray                # weights, sum ≤ synth_budget
    mu_annual: np.ndarray              # per-asset annualized expected return
    sigma_annual: np.ndarray           # per-asset annualized volatility
    cov_annual: np.ndarray             # annualized covariance matrix
    corr_matrix: np.ndarray            # correlation matrix
    expected_return: float             # wᵀμ
    expected_vol: float                # √(wᵀΣw)
    expected_sharpe: float
    diversification_ratio: float       # weighted_avg_vol / portfolio_vol
    converged: bool
    risk_aversion: float


def optimize_weights(
    symbols: list[str],
    daily_returns: dict[str, list[float]],
    risk_profile: RiskProfile,
    synth_budget: float,
) -> dict[str, float]:
    """Compute optimal synth-asset weights for a vault risk profile.

    Args:
        symbols: Ordered list of synth symbols to allocate across.
        daily_returns: {symbol: [per-bar daily returns]} — must cover the
            same date range (aligned). Series are tail-truncated to the
            shortest available length.
        risk_profile: Vault risk profile — selects the MVO objective.
        synth_budget: Total weight budget for synth assets, i.e.
            (1 - USDC_floor). Returned weights sum to this value.

    Returns:
        {symbol: weight} summing to synth_budget.
        Falls back to equal-weight if optimization fails.
    """
    n = len(symbols)
    if n == 0:
        return {}

    R = _aligned_return_matrix(symbols, daily_returns)

    if R is None:
        logger.warning(
            "Insufficient return data for MVO (%s) — using equal weight",
            risk_profile.value,
        )
        return _equal_weight(symbols, synth_budget)

    mu = R.mean(axis=0)        # per-bar mean returns, shape (N,)
    Sigma = np.cov(R.T, ddof=1)  # covariance matrix, shape (N, N)
    if Sigma.ndim == 0:
        # Single-asset edge case: np.cov returns a scalar
        Sigma = np.array([[float(Sigma)]])
    Sigma += np.eye(n) * 1e-8  # numerical regularization

    if risk_profile == RiskProfile.CONSERVATIVE:
        raw = _gmv(Sigma, n, cap=_CAP_DEFAULT)
    elif risk_profile in (RiskProfile.MODERATE, RiskProfile.AGGRESSIVE):
        raw = _max_sharpe(mu, Sigma, n, cap=_CAP_DEFAULT)
    else:
        raw = _max_expected_return(mu, n, cap=_CAP_HYPER)

    if raw is None:
        logger.warning(
            "scipy optimization failed for %s — using equal weight",
            risk_profile.value,
        )
        return _equal_weight(symbols, synth_budget)

    scaled = {sym: round(float(w) * synth_budget, 6) for sym, w in zip(symbols, raw)}
    logger.info(
        "MVO [%s]: %s",
        risk_profile.value,
        "  ".join(f"{s}={w:.1%}" for s, w in scaled.items()),
    )
    return scaled


# ─── Objectives ──────────────────────────────────────────────────────


def compute_efficient_frontier(
    symbols: list[str],
    daily_returns: dict[str, list[float]],
    n_points: int = 30,
) -> list[dict]:
    """Compute the mean-variance efficient frontier.

    Sweeps from the minimum-variance portfolio to the maximum-return portfolio,
    returning n_points (vol, return, weights) triples.

    Returns [] if data is insufficient (< 20 bars).
    """
    n = len(symbols)
    if n == 0:
        return []

    R = _aligned_return_matrix(symbols, daily_returns)
    if R is None:
        return []

    mu = R.mean(axis=0) * _ANNUALIZATION           # annualized expected returns
    Sigma = np.cov(R.T, ddof=1) * _ANNUALIZATION   # annualized covariance
    if Sigma.ndim == 0:
        Sigma = np.array([[float(Sigma)]])
    Sigma += np.eye(n) * 1e-8

    # Bounds for min- and max-return portfolios
    mu_min = float(mu.min())
    mu_max = float(mu.max())
    if mu_min >= mu_max:
        return []

    target_returns = np.linspace(mu_min, mu_max, n_points)
    frontier: list[dict] = []

    w0 = np.ones(n) / n
    bounds = [(0.0, _CAP_DEFAULT)] * n

    for target_mu in target_returns:
        constraints = [
            {"type": "eq", "fun": lambda w: w.sum() - 1.0},
            {"type": "eq", "fun": lambda w, t=target_mu: float(w @ mu) - t},
        ]
        result = minimize(
            lambda w: float(w @ Sigma @ w),
            w0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-9, "maxiter": 500},
        )
        if result.success:
            w = result.x
            port_vol = float(np.sqrt(w @ Sigma @ w))
            port_ret = float(w @ mu)
            frontier.append({
                "vol": round(port_vol, 6),
                "return": round(port_ret, 6),
                "weights": {sym: round(float(wi), 4) for sym, wi in zip(symbols, w)},
            })

    return frontier


# ─── Objectives ──────────────────────────────────────────────────────


def _gmv(Sigma: np.ndarray, n: int, cap: float) -> np.ndarray | None:
    """Global Minimum Variance: min w'Σw  s.t. 1'w=1, 0 ≤ w ≤ cap."""
    w0 = np.ones(n) / n
    constraints = [{"type": "eq", "fun": lambda w: float(np.sum(w)) - 1.0}]
    bounds = [(0.0, cap)] * n

    result = minimize(
        lambda w: float(w @ Sigma @ w),
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    if not result.success:
        return None
    w = np.clip(np.asarray(result.x), 0.0, 1.0)
    return w / w.sum()


def _max_sharpe(
    mu: np.ndarray,
    Sigma: np.ndarray,
    n: int,
    cap: float,
) -> np.ndarray | None:
    """Max Sharpe: maximize (μ-rf)'w / sqrt(w'Σw)  s.t. 1'w=1, 0 ≤ w ≤ cap."""
    w0 = np.ones(n) / n
    constraints = [{"type": "eq", "fun": lambda w: float(np.sum(w)) - 1.0}]
    bounds = [(0.0, cap)] * n

    def neg_sharpe(w: np.ndarray) -> float:
        excess = float(w @ mu) - _RF_DAILY
        port_var = max(float(w @ Sigma @ w), 1e-14)
        return -(excess / math.sqrt(port_var))

    result = minimize(
        neg_sharpe,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    if not result.success:
        return None
    w = np.clip(np.asarray(result.x), 0.0, 1.0)
    return w / w.sum()


def _max_expected_return(mu: np.ndarray, n: int, cap: float) -> np.ndarray | None:
    """Max Expected Return: concentrate in highest-μ assets up to cap.

    This is a linear program on the unit simplex. The unconstrained solution
    is 100% in the single best asset; the per-asset cap forces the remaining
    budget to spill into the second-best, third-best, etc.
    """
    w = np.zeros(n)
    remaining = 1.0
    for idx in np.argsort(mu)[::-1]:
        alloc = min(remaining, cap)
        w[idx] = alloc
        remaining -= alloc
        if remaining < 1e-9:
            break

    if remaining > 1e-9:
        # Numerical residual — dump into the highest-μ asset already capped
        best_idx = int(np.argmax(mu))
        w[best_idx] = min(1.0, w[best_idx] + remaining)

    w = np.clip(w, 0.0, 1.0)
    total = w.sum()
    if total <= 0:
        return None
    return w / total


# ─── Helpers ─────────────────────────────────────────────────────────


def _aligned_return_matrix(
    symbols: list[str],
    daily_returns: dict[str, list[float]],
) -> np.ndarray | None:
    """Build a (T, N) return matrix. T = min series length; N = len(symbols).

    Returns None if any symbol is missing or T < _MIN_BARS.
    """
    arrays: list[np.ndarray] = []
    for sym in symbols:
        r = daily_returns.get(sym)
        if not r:
            return None
        arrays.append(np.asarray(r, dtype=float))

    T = min(len(a) for a in arrays)
    if T < _MIN_BARS:
        return None

    return np.column_stack([a[-T:] for a in arrays])


def _equal_weight(symbols: list[str], budget: float) -> dict[str, float]:
    n = len(symbols)
    if n == 0:
        return {}
    w = round(budget / n, 6)
    return {s: w for s in symbols}


# ─── Kelly mean-variance from price-history dict ──────────────────


def _shrink_cov(cov: np.ndarray, intensity: float = 0.10) -> np.ndarray:
    """Ledoit-Wolf-style identity shrinkage toward asset-specific variance."""
    diag = np.diag(np.diag(cov))
    return (1 - intensity) * cov + intensity * diag


def _build_mu_sigma_from_prices(
    price_histories: dict[str, pd.Series],
    symbols: list[str],
    min_overlap_days: int = 60,
) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray] | None:
    """Build (μ, Σ, corr) from a synth → price-Series dict.

    Aligns all series on a common date index (inner join), drops zero-vol
    columns, annualizes, applies identity shrinkage.  Returns None if
    fewer than 2 viable assets remain or alignment yields too few bars.
    """
    series_map = {
        s: price_histories[s]
        for s in symbols
        if s in price_histories and not price_histories[s].empty
    }
    if len(series_map) < 2:
        return None

    df = pd.DataFrame(series_map).dropna(how="any")
    if len(df) < min_overlap_days:
        df = pd.DataFrame(series_map).ffill().dropna(how="any")
    if len(df) < min_overlap_days:
        return None

    returns = df.pct_change().dropna()
    keep = [c for c in returns.columns if returns[c].std() > 0]
    if len(keep) < 2:
        return None
    returns = returns[keep]

    daily_mean = returns.mean().values
    daily_cov = np.cov(returns.values, rowvar=False)
    mu_annual = daily_mean * _ANNUALIZATION
    cov_annual = _shrink_cov(daily_cov * _ANNUALIZATION, intensity=0.10)
    sigma_annual = np.sqrt(np.diag(cov_annual))
    sigma_safe = np.where(sigma_annual > 1e-9, sigma_annual, 1e-9)
    corr = cov_annual / np.outer(sigma_safe, sigma_safe)
    return keep, mu_annual, cov_annual, corr


def kelly_optimize_from_prices(
    symbols: list[str],
    price_histories: dict[str, pd.Series],
    risk_profile: str,
    synth_budget: float,
    max_weight: float = 0.20,
    mu_override: dict[str, float] | None = None,
) -> KellyOptimizationResult | None:
    """Solve the constrained Kelly mean-variance problem.

        maximize   wᵀμ - ½·γ·wᵀΣw
        subject to 0 ≤ wᵢ ≤ max_weight
                   Σ wᵢ ≤ synth_budget

    γ is mapped from ``risk_profile`` via RISK_AVERSION.  ``mu_override``
    lets the caller substitute Kelly-derived or backtest-stat expected
    returns for the sample mean (which is noisy on short windows).
    """
    built = _build_mu_sigma_from_prices(price_histories, symbols)
    if built is None:
        return None

    kept, mu_sample, cov_annual, corr = built
    if mu_override:
        mu = np.array([mu_override.get(s, mu_sample[i]) for i, s in enumerate(kept)])
    else:
        mu = mu_sample
    sigma_annual = np.sqrt(np.diag(cov_annual))

    gamma = RISK_AVERSION.get(risk_profile, 3.0)
    n = len(kept)

    def neg_obj(w: np.ndarray) -> float:
        return -(w @ mu - 0.5 * gamma * w @ cov_annual @ w)

    def neg_grad(w: np.ndarray) -> np.ndarray:
        return -(mu - gamma * cov_annual @ w)

    constraints = [{"type": "ineq", "fun": lambda w: synth_budget - np.sum(w)}]
    bounds = [(0.0, max_weight)] * n
    w0 = np.full(n, synth_budget / n)

    try:
        res = minimize(
            neg_obj, w0, jac=neg_grad,
            bounds=bounds, constraints=constraints,
            method="SLSQP",
            options={"maxiter": 200, "ftol": 1e-9},
        )
    except Exception as e:  # pylint: disable=broad-except
        logger.warning("Kelly SLSQP failed: %s", e)
        return None

    w = np.clip(res.x, 0.0, max_weight)
    total = w.sum()
    if total > synth_budget:
        w = w * (synth_budget / total)
    w = np.clip(w, 0.0, max_weight)

    portfolio_mu = float(w @ mu)
    portfolio_var = float(w @ cov_annual @ w)
    portfolio_vol = float(math.sqrt(max(portfolio_var, 0.0)))
    sharpe = portfolio_mu / portfolio_vol if portfolio_vol > 1e-9 else 0.0
    weighted_vol = float(np.sum(w * sigma_annual))
    div_ratio = weighted_vol / portfolio_vol if portfolio_vol > 1e-9 else 1.0

    return KellyOptimizationResult(
        symbols=kept,
        weights=w,
        mu_annual=mu,
        sigma_annual=sigma_annual,
        cov_annual=cov_annual,
        corr_matrix=corr,
        expected_return=portfolio_mu,
        expected_vol=portfolio_vol,
        expected_sharpe=sharpe,
        diversification_ratio=div_ratio,
        converged=bool(res.success),
        risk_aversion=gamma,
    )


def kelly_risk_decomposition(result: KellyOptimizationResult) -> list[dict]:
    """Per-asset marginal contribution to portfolio variance.

    Euler decomposition: MCᵢ = wᵢ · (Σw)ᵢ / σ²ₚ.  Sums to 1 across assets.
    Lets the UI show "GLD contributes 22% of portfolio variance" — the
    standard risk-attribution view at any real shop.
    """
    w = result.weights
    sigma_p_sq = float(w @ result.cov_annual @ w)
    if sigma_p_sq < 1e-12:
        return []
    contributions = w * (result.cov_annual @ w) / sigma_p_sq
    return [
        {
            "symbol": result.symbols[i],
            "weight": round(float(w[i]), 4),
            "mu_annual": round(float(result.mu_annual[i]), 4),
            "vol_annual": round(float(result.sigma_annual[i]), 4),
            "variance_contribution": round(float(contributions[i]), 4),
        }
        for i in range(len(result.symbols))
    ]


def correlation_pairs(result: KellyOptimizationResult, top_n: int = 8) -> list[dict]:
    """Top-N highest-magnitude correlation pairs for the picked assets."""
    n = len(result.symbols)
    pairs: list[tuple[float, int, int]] = []
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((float(result.corr_matrix[i, j]), i, j))
    pairs.sort(key=lambda x: abs(x[0]), reverse=True)
    return [
        {
            "a": result.symbols[i],
            "b": result.symbols[j],
            "corr": round(rho, 3),
        }
        for rho, i, j in pairs[:top_n]
    ]
