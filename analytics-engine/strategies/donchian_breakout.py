"""Donchian channel breakout — Donchian (orig.), tested by Brock et al. 1992.

Trade in the direction of a range break: go long when price closes above the
prior N-day high, exit when it closes below the prior M-day low. The
canonical trend-following breakout rule, the spine of the Turtle system.
"""

from __future__ import annotations

import backtrader as bt

PAPER_ARXIV_ID: str | None = None
PAPER_TITLE = "Donchian Channel Breakout (Four-Week Rule); trading-rule evidence in Brock, Lakonishok & LeBaron (1992)"
PAPER_AUTHORS: list[str] = ["Richard Donchian", "William Brock", "Josef Lakonishok", "Blake LeBaron"]
PAPER_VENUE = "The Journal of Finance (Brock et al. 1992, 47(5):1731-1764)"
PAPER_YEAR = 1992
PAPER_DOI = "10.1111/j.1540-6261.1992.tb04681.x"  # Brock et al. — the academic anchor for the breakout family.
PAPER_CITATION_COUNT = 6000  # Brock et al. snapshot 2026-06; verify via Semantic Scholar.

REGIME_TAG: str = "bull"

METHODOLOGY_SUMMARY = (
    "Channel breakout trend-following. Track the highest high and lowest low "
    "over a lookback window; go long when price closes above the prior 20-day "
    "high and exit when it closes below the prior 10-day low. Long/flat."
)

METHODOLOGY_TEXT = (
    "Richard Donchian's channel-breakout / 'four-week rule' (~20 trading days) "
    "is the canonical trend-following entry: buy when price makes a new "
    "n-period high, exit/reverse on a new n-period low. It is practitioner "
    "folklore with a named originator rather than a peer-reviewed result, so "
    "for academic grounding we anchor on Brock, Lakonishok & LeBaron (1992), "
    "which tests trading-range-break and moving-average rules on the DJIA "
    "1897-1986 and finds the breakout/MA family carries predictive content.\n\n"
    "Data-snooping caveat (Sullivan, Timmermann & White 1999): the apparent "
    "profitability of simple technical rules is sensitive to the universe of "
    "rules searched. Our DSR (which penalizes for num_trials_in_selection) and "
    "PBO gate are precisely the corrections that caveat motivates, so the only "
    "performance claim we stand behind is the post-gate one. paper_claimed_* "
    "are null (Brock et al. report conditional mean returns, not a Sharpe).\n\n"
    "v1 Archimedes adaptation: 20-day entry channel, 10-day exit channel, "
    "compared against the PRIOR bar's channel to avoid look-ahead. Long/flat, "
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
    "Breakout trend-follower — captures sustained directional moves that the "
    "SMA-cross Faber filter can lag on. The asymmetric 20-in/10-out channel "
    "gives back less on whipsaws than a symmetric channel."
)
EXTRACTION_LLM: str | None = None

STATUS = "candidate"

BACKTEST_SHARPE: float | None = None
BACKTEST_CAGR: float | None = None
BACKTEST_MAX_DD: float | None = None
BACKTEST_WIN_RATE: float | None = None
BACKTEST_CALMAR: float | None = None
BACKTEST_CORR_SPY: float | None = None


class DonchianChannelBreakout(bt.Strategy):
    """Long on close above prior 20-day high; exit on close below prior 10-day low."""

    params = (
        ("entry_period", 20),
        ("exit_period", 10),
        ("exposure_fraction", 0.99),
    )

    def __init__(self) -> None:
        self.highest = bt.indicators.Highest(self.data.high, period=int(self.params.entry_period))
        self.lowest = bt.indicators.Lowest(self.data.low, period=int(self.params.exit_period))
        self._in_market: bool = False

    def next(self) -> None:
        if len(self) <= int(self.params.entry_period):
            return

        price = float(self.data.close[0])
        prior_high = float(self.highest[-1])  # prior bar's channel — no look-ahead
        prior_low = float(self.lowest[-1])

        if not self._in_market:
            if price > prior_high:
                account_value = float(self.broker.getvalue())
                target_size = int(account_value * float(self.params.exposure_fraction) // price)
                if target_size > 0:
                    self.order_target_size(target=target_size)
                    self._in_market = True
        elif price < prior_low:
            self.close()
            self._in_market = False
