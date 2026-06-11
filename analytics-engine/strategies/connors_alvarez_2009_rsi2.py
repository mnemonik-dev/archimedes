"""RSI(2) mean reversion — Connors & Alvarez 2009.

Buy short-term weakness inside an established uptrend: when a 2-period RSI
drops to an oversold extreme while price is above its long trend filter, go
long; exit on the first sign of strength. A high-turnover counterpoint to the
trend-following sleeve.
"""

from __future__ import annotations

import backtrader as bt

PAPER_ARXIV_ID: str | None = None
PAPER_TITLE = "Short Term Trading Strategies That Work (RSI-2 mean reversion)"
PAPER_AUTHORS: list[str] = ["Laurence A. Connors", "Cesar Alvarez"]
PAPER_VENUE = "The Connors Group (book, ISBN 978-0-9819239-0-1)"
PAPER_YEAR = 2009
PAPER_DOI: str | None = None  # Book — no DOI.
PAPER_CITATION_COUNT: int | None = None

# Regime suitability: short-term mean reversion inside an uptrend filter.
REGIME_TAG: str = "regime_neutral"

METHODOLOGY_SUMMARY = (
    "Long-only short-term mean reversion. Enter when the 2-period RSI is "
    "below an oversold threshold AND price is above its 200-day SMA (trend "
    "filter); exit when price closes back above a short (5-day) SMA. Trades "
    "the dip inside an uptrend, not the trend itself."
)

METHODOLOGY_TEXT = (
    "Connors & Alvarez popularized the 2-period RSI as a short-term "
    "mean-reversion trigger. The canonical rule: only consider longs when the "
    "instrument trades above its 200-day moving average (so the bet is 'buy "
    "the dip in an uptrend'); enter when RSI(2) falls below a low threshold "
    "(commonly 5-10); exit when price closes above a short moving average "
    "(e.g., the 5-day SMA) or RSI rises back toward neutral.\n\n"
    "Provenance honesty: the source is a trading book, not a peer-reviewed "
    "paper, and it reports win-rate / average-gain tables rather than a clean "
    "Sharpe or CAGR. paper_claimed_* are therefore null; the rigor gate "
    "(DSR/PBO/OOS) on our own backtest is the only performance claim we stand "
    "behind.\n\n"
    "v1 Archimedes adaptation: RSI(2) entry threshold 10.0, 200-day SMA trend "
    "filter, exit on close above the 5-day SMA. Long/flat, single asset."
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
    "High-turnover mean-reversion sleeve. The 200-day trend filter keeps it "
    "from catching falling knives, and its short holding period makes it "
    "lowly correlated with the buy-and-hold and Faber trend strategies — a "
    "useful behavioral diversifier even if standalone Sharpe is modest."
)
EXTRACTION_LLM: str | None = None

STATUS = "candidate"

# Fixture (backtest_fixtures.json) is authoritative; documentation fallbacks left null.
BACKTEST_SHARPE: float | None = None
BACKTEST_CAGR: float | None = None
BACKTEST_MAX_DD: float | None = None
BACKTEST_WIN_RATE: float | None = None
BACKTEST_CALMAR: float | None = None
BACKTEST_CORR_SPY: float | None = None


class RSI2MeanReversion(bt.Strategy):
    """Long when RSI(2) oversold and price > 200d SMA; exit on close > 5d SMA."""

    params = (
        ("rsi_period", 2),
        ("rsi_entry", 10.0),
        ("sma_fast", 5),
        ("sma_trend", 200),
        ("exposure_fraction", 0.99),
    )

    def __init__(self) -> None:
        # safediv guards the period-2 RSI against zero-loss windows (avg_loss == 0 → div-by-zero).
        self.rsi = bt.indicators.RelativeStrengthIndex(
            self.data.close, period=int(self.params.rsi_period), safediv=True
        )
        self.sma_fast = bt.indicators.SimpleMovingAverage(self.data.close, period=int(self.params.sma_fast))
        self.sma_trend = bt.indicators.SimpleMovingAverage(self.data.close, period=int(self.params.sma_trend))
        self._in_market: bool = False

    def next(self) -> None:
        if len(self) < int(self.params.sma_trend):
            return

        price = float(self.data.close[0])

        if not self._in_market:
            oversold = float(self.rsi[0]) < float(self.params.rsi_entry)
            uptrend = price > float(self.sma_trend[0])
            if oversold and uptrend:
                account_value = float(self.broker.getvalue())
                target_size = int(account_value * float(self.params.exposure_fraction) // price)
                if target_size > 0:
                    self.order_target_size(target=target_size)
                    self._in_market = True
        elif price > float(self.sma_fast[0]):
            self.close()
            self._in_market = False
