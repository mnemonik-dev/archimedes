"""Dual moving-average crossover (golden cross) — Brock, Lakonishok & LeBaron 1992.

The classic 50/200 trend filter: hold the asset when the fast SMA is above the
slow SMA ("golden cross"), go flat when it crosses below ("death cross"). The
single best-documented member of the moving-average-rule family.
"""

from __future__ import annotations

import backtrader as bt

PAPER_ARXIV_ID: str | None = None
PAPER_TITLE = "Simple Technical Trading Rules and the Stochastic Properties of Stock Returns"
PAPER_AUTHORS: list[str] = ["William Brock", "Josef Lakonishok", "Blake LeBaron"]
PAPER_VENUE = "The Journal of Finance (47(5):1731-1764)"
PAPER_YEAR = 1992
PAPER_DOI = "10.1111/j.1540-6261.1992.tb04681.x"
PAPER_CITATION_COUNT = 6000  # Snapshot 2026-06; verify via Semantic Scholar.

REGIME_TAG: str = "bull"

METHODOLOGY_SUMMARY = (
    "Dual-SMA trend filter. Long when the 50-day SMA is above the 200-day SMA "
    "(golden cross), flat when below (death cross). The most widely cited "
    "long/short moving-average rule. Long/flat here."
)

METHODOLOGY_TEXT = (
    "The 50/200 'golden cross' is folklore with no single inventor, but Brock, "
    "Lakonishok & LeBaron (1992) provide its rigorous academic test: they "
    "evaluate variable- and fixed-length moving-average rules (including "
    "long/short SMA pairs) on the DJIA 1897-1986 and report that buy-signal "
    "days carry significantly higher mean returns than sell-signal days. They "
    "report conditional mean returns and t-statistics, NOT a tradeable Sharpe "
    "or CAGR, so paper_claimed_* are null.\n\n"
    "Data-snooping caveat (Sullivan, Timmermann & White 1999): Brock et al.'s "
    "result is the textbook target of the data-snooping critique. Our DSR "
    "(num_trials-penalized) and PBO gate are exactly the corrections that "
    "critique calls for, so the only performance claim we make is the "
    "post-gate one on our own backtest.\n\n"
    "v1 Archimedes adaptation: 50-day fast SMA, 200-day slow SMA, long when "
    "fast > slow, flat otherwise. Long/flat, single asset."
)

PAPER_CLAIMED_SHARPE: float | None = None
PAPER_CLAIMED_CAGR: float | None = None
PAPER_CLAIMED_MAX_DD: float | None = None

ASSET_UNIVERSE: list[str] = ["SPY", "NIKKEI", "GOLD", "TREASURY", "OIL"]
POSITION_SIZING = "equal_weight"
REBALANCE_FREQUENCY = "daily"
RISK_PROFILES: list[str] = ["conservative", "moderate"]

CURATOR_WALLET: str | None = None
CURATOR_NOTE = (
    "The most recognizable trend filter in markets. Slower than Faber's "
    "price/200-SMA cross (it compares two averages, so both whipsaw less and "
    "lag more), it serves as a sanity benchmark for the trend sleeve and is "
    "the rule retail users will recognize on sight."
)
EXTRACTION_LLM: str | None = None

STATUS = "candidate"

BACKTEST_SHARPE: float | None = None
BACKTEST_CAGR: float | None = None
BACKTEST_MAX_DD: float | None = None
BACKTEST_WIN_RATE: float | None = None
BACKTEST_CALMAR: float | None = None
BACKTEST_CORR_SPY: float | None = None


class DualMACrossover(bt.Strategy):
    """Long when fast SMA > slow SMA; flat otherwise."""

    params = (
        ("fast_period", 50),
        ("slow_period", 200),
        ("exposure_fraction", 0.99),
    )

    def __init__(self) -> None:
        self.sma_fast = bt.indicators.SimpleMovingAverage(self.data.close, period=int(self.params.fast_period))
        self.sma_slow = bt.indicators.SimpleMovingAverage(self.data.close, period=int(self.params.slow_period))
        self._in_market: bool = False

    def next(self) -> None:
        if len(self) < int(self.params.slow_period):
            return

        price = float(self.data.close[0])
        signal = float(self.sma_fast[0]) > float(self.sma_slow[0])

        if signal and not self._in_market:
            account_value = float(self.broker.getvalue())
            target_size = int(account_value * float(self.params.exposure_fraction) // price)
            if target_size > 0:
                self.order_target_size(target=target_size)
                self._in_market = True
        elif not signal and self._in_market:
            self.close()
            self._in_market = False
