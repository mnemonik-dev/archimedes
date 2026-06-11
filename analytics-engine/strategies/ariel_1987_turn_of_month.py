"""Turn-of-the-month seasonality — Ariel 1987; Lakonishok & Smidt 1988.

Hold the asset only around the turn of the month — the calendar window into
which the historical equity premium has disproportionately concentrated — and
sit in cash the rest of the time. A pure calendar-timing sleeve.
"""

from __future__ import annotations

import backtrader as bt

PAPER_ARXIV_ID: str | None = None
PAPER_TITLE = "A Monthly Effect in Stock Returns"
PAPER_AUTHORS: list[str] = ["Robert A. Ariel"]
PAPER_VENUE = "Journal of Financial Economics (18(1):161-174); corroborated by Lakonishok & Smidt (1988)"
PAPER_YEAR = 1987
PAPER_DOI = "10.1016/0304-405X(87)90066-3"
PAPER_CITATION_COUNT = 1300  # Snapshot 2026-06; verify via Semantic Scholar.

REGIME_TAG: str = "regime_neutral"

METHODOLOGY_SUMMARY = (
    "Calendar-timing. Hold the asset long only during the turn-of-the-month "
    "window (around month-end through the first few trading days of the next "
    "month) and stay in cash otherwise. Captures the documented concentration "
    "of returns in that window."
)

METHODOLOGY_TEXT = (
    "Ariel (1987) documented that essentially all of the market's cumulative "
    "capital gain over 1963-1981 accrued in the first half of trading months "
    "(from the last day of the prior month onward), with the second half "
    "contributing roughly zero. Lakonishok & Smidt (1988) confirmed anomalous "
    "returns concentrated around the turn of the month across 90 years of DJIA "
    "data. Both report mean returns by calendar window, not a risk-adjusted "
    "ratio, so paper_claimed_* are null.\n\n"
    "v1 Archimedes adaptation (look-ahead safe): we cannot know in advance "
    "which bar is the LAST trading day of a month without peeking, so we "
    "approximate the turn-of-month window using only the current bar's date — "
    "long during the first ``first_n`` trading days of each month OR when the "
    "calendar day-of-month is >= ``month_end_day`` (a proxy for the final "
    "trading days), flat otherwise. The trading-day counter resets when the "
    "calendar month changes. Long/flat, single asset."
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
    "Pure calendar sleeve with very low time-in-market (~25-30% of days), so "
    "its returns are nearly orthogonal to the always-on and trend strategies. "
    "Even a modest standalone Sharpe makes it a useful low-exposure "
    "diversifier; the honest test is whether the effect survives DSR/PBO out "
    "of sample, which is exactly what the gate measures."
)
EXTRACTION_LLM: str | None = None

STATUS = "candidate"

BACKTEST_SHARPE: float | None = None
BACKTEST_CAGR: float | None = None
BACKTEST_MAX_DD: float | None = None
BACKTEST_WIN_RATE: float | None = None
BACKTEST_CALMAR: float | None = None
BACKTEST_CORR_SPY: float | None = None


class TurnOfMonthSeasonality(bt.Strategy):
    """Long during the turn-of-month window (first N trading days or month-end), flat otherwise."""

    params = (
        ("first_n", 3),  # first N trading days of the month
        ("month_end_day", 28),  # calendar day-of-month proxy for month-end
        ("exposure_fraction", 0.99),
    )

    def __init__(self) -> None:
        self._prev_month: int | None = None
        self._trading_day_of_month: int = 0
        self._in_market: bool = False

    def next(self) -> None:
        current = self.data.datetime.date(0)

        if self._prev_month != current.month:
            self._trading_day_of_month = 1
            self._prev_month = current.month
        else:
            self._trading_day_of_month += 1

        in_window = self._trading_day_of_month <= int(self.params.first_n) or current.day >= int(
            self.params.month_end_day
        )

        price = float(self.data.close[0])

        if in_window and not self._in_market:
            account_value = float(self.broker.getvalue())
            target_size = int(account_value * float(self.params.exposure_fraction) // price)
            if target_size > 0:
                self.order_target_size(target=target_size)
                self._in_market = True
        elif not in_window and self._in_market:
            self.close()
            self._in_market = False
