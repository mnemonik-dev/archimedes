"""MACD signal-line crossover — Appel (1979), tested by Brock et al. 1992.

A smoothed dual-EMA momentum oscillator: go long when the MACD line crosses
above its signal line, flat when it crosses below. The most widely used
member of the moving-average-crossover family.
"""

from __future__ import annotations

import backtrader as bt

PAPER_ARXIV_ID: str | None = None
PAPER_TITLE = "MACD Trading Method (Appel 1979); MA-rule evidence in Brock, Lakonishok & LeBaron (1992)"
PAPER_AUTHORS: list[str] = ["Gerald Appel", "William Brock", "Josef Lakonishok", "Blake LeBaron"]
PAPER_VENUE = "The Journal of Finance (Brock et al. 1992, 47(5):1731-1764)"
PAPER_YEAR = 1992
PAPER_DOI = "10.1111/j.1540-6261.1992.tb04681.x"  # Brock et al. — academic anchor for the MA-crossover family.
PAPER_CITATION_COUNT = 6000  # Brock et al. snapshot 2026-06; verify via Semantic Scholar.

REGIME_TAG: str = "regime_neutral"

METHODOLOGY_SUMMARY = (
    "Momentum trend-following via a smoothed dual-EMA crossover. MACD line = "
    "EMA(12) - EMA(26); signal line = EMA(9) of the MACD line. Go long when "
    "MACD crosses above signal, flat when it crosses below. Long/flat."
)

METHODOLOGY_TEXT = (
    "Gerald Appel's Moving Average Convergence/Divergence (1979) is a smoothed "
    "dual-EMA crossover with a signal line: MACD = EMA(12) - EMA(26), signal = "
    "EMA(9) of MACD. A bullish crossover (MACD above signal) is a long entry; "
    "a bearish crossover exits. MACD is practitioner folklore with a named "
    "originator and no peer-reviewed origin paper, so we anchor academically on "
    "Brock, Lakonishok & LeBaron (1992), whose tests of the moving-average-rule "
    "family on the DJIA support its predictive content.\n\n"
    "Data-snooping caveat (Sullivan, Timmermann & White 1999) applies as it "
    "does to all simple technical rules; our DSR/PBO gate is the intended "
    "correction. paper_claimed_* are null (no clean published Sharpe).\n\n"
    "v1 Archimedes adaptation: MACD(12, 26, 9), long on signal-line cross up, "
    "flat on cross down. Long/flat, single asset."
)

PAPER_CLAIMED_SHARPE: float | None = None
PAPER_CLAIMED_CAGR: float | None = None
PAPER_CLAIMED_MAX_DD: float | None = None

ASSET_UNIVERSE: list[str] = ["SPY", "NIKKEI", "GOLD", "TREASURY", "OIL"]
POSITION_SIZING = "equal_weight"
REBALANCE_FREQUENCY = "daily"
RISK_PROFILES: list[str] = ["moderate", "aggressive"]

CURATOR_WALLET: str | None = None
CURATOR_NOTE = (
    "Smoothed-momentum trend-follower. The EMA smoothing makes it slower to "
    "flip than a raw price/SMA cross, trading some lag for fewer whipsaws — a "
    "different point on the trend-following speed spectrum than Faber or "
    "Donchian."
)
EXTRACTION_LLM: str | None = None

STATUS = "candidate"

BACKTEST_SHARPE: float | None = None
BACKTEST_CAGR: float | None = None
BACKTEST_MAX_DD: float | None = None
BACKTEST_WIN_RATE: float | None = None
BACKTEST_CALMAR: float | None = None
BACKTEST_CORR_SPY: float | None = None


class MACDTrend(bt.Strategy):
    """Long when MACD line > signal line; flat otherwise."""

    params = (
        ("period_fast", 12),
        ("period_slow", 26),
        ("period_signal", 9),
        ("exposure_fraction", 0.99),
    )

    def __init__(self) -> None:
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=int(self.params.period_fast),
            period_me2=int(self.params.period_slow),
            period_signal=int(self.params.period_signal),
        )
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)
        self._in_market: bool = False

    def next(self) -> None:
        if len(self) < int(self.params.period_slow) + int(self.params.period_signal):
            return

        price = float(self.data.close[0])
        cross = float(self.crossover[0])

        if not self._in_market and cross > 0:
            account_value = float(self.broker.getvalue())
            target_size = int(account_value * float(self.params.exposure_fraction) // price)
            if target_size > 0:
                self.order_target_size(target=target_size)
                self._in_market = True
        elif self._in_market and cross < 0:
            self.close()
            self._in_market = False
