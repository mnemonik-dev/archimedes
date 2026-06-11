"""Bollinger Band mean reversion — Bollinger 2001.

Fade extreme deviations from a moving-average envelope: go long when price
closes at or below the lower band (statistically stretched to the downside),
and exit when it reverts to the middle band. A volatility-adaptive
mean-reversion sleeve.
"""

from __future__ import annotations

import backtrader as bt

PAPER_ARXIV_ID: str | None = None
PAPER_TITLE = "Bollinger on Bollinger Bands (lower-band mean reversion)"
PAPER_AUTHORS: list[str] = ["John A. Bollinger"]
PAPER_VENUE = "McGraw-Hill (book, ISBN 978-0-07-137368-5)"
PAPER_YEAR = 2001
PAPER_DOI: str | None = None  # Book — no DOI.
PAPER_CITATION_COUNT: int | None = None

REGIME_TAG: str = "regime_neutral"

METHODOLOGY_SUMMARY = (
    "Long-only mean reversion against a volatility-scaled envelope. The "
    "middle band is a 20-day SMA; the outer bands sit +/- 2 standard "
    "deviations of price away. Enter long when price closes at/below the "
    "lower band; exit when it reverts to the middle band."
)

METHODOLOGY_TEXT = (
    "Bollinger Bands wrap a moving average (default 20-day SMA) with bands set "
    "k standard deviations of price above and below (default k=2). The bands "
    "widen in volatile regimes and contract in calm ones, so a fixed 'distance "
    "from the mean' adapts to conditions. The mean-reversion variant treats a "
    "close at/below the lower band as a stretched, likely-to-revert state: go "
    "long there and exit on reversion to the middle band.\n\n"
    "Provenance honesty: the authoritative reference is Bollinger's 2001 book, "
    "not a peer-reviewed paper, and it describes band construction and example "
    "systems qualitatively without reporting a mechanical Sharpe/CAGR. "
    "paper_claimed_* are null; our DSR/PBO/OOS gate on the real backtest is the "
    "only performance claim.\n\n"
    "v1 Archimedes adaptation: 20-day SMA middle band, 2-sigma outer bands, "
    "long on close <= lower band, exit on close >= middle band. Long/flat, "
    "single asset."
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
    "Volatility-adaptive mean reversion. Complements the fixed-threshold "
    "RSI-2 sleeve: where RSI(2) keys off momentum exhaustion, Bollinger keys "
    "off statistical price dispersion, so the two fire on overlapping but not "
    "identical dips."
)
EXTRACTION_LLM: str | None = None

STATUS = "candidate"

BACKTEST_SHARPE: float | None = None
BACKTEST_CAGR: float | None = None
BACKTEST_MAX_DD: float | None = None
BACKTEST_WIN_RATE: float | None = None
BACKTEST_CALMAR: float | None = None
BACKTEST_CORR_SPY: float | None = None


class BollingerBandReversion(bt.Strategy):
    """Long on close <= lower band; exit on close >= middle band."""

    params = (
        ("period", 20),
        ("devfactor", 2.0),
        ("exposure_fraction", 0.99),
    )

    def __init__(self) -> None:
        self.boll = bt.indicators.BollingerBands(
            self.data.close,
            period=int(self.params.period),
            devfactor=float(self.params.devfactor),
        )
        self._in_market: bool = False

    def next(self) -> None:
        if len(self) < int(self.params.period):
            return

        price = float(self.data.close[0])

        if not self._in_market:
            if price <= float(self.boll.lines.bot[0]):
                account_value = float(self.broker.getvalue())
                target_size = int(account_value * float(self.params.exposure_fraction) // price)
                if target_size > 0:
                    self.order_target_size(target=target_size)
                    self._in_market = True
        elif price >= float(self.boll.lines.mid[0]):
            self.close()
            self._in_market = False
