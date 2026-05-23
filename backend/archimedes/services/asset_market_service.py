"""Composes oracle + history data into the /api/explore/assets response.

Wraps the existing yfinance-backed history fetch in a 30-second TTL cache
(per the Phase 3a spec — page must load <1s without synchronous on-chain
reads). The plain-English explanations live in this module so the route
handler stays a thin facade.
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from datetime import datetime, timezone
from typing import Any

from archimedes.api.explore_schemas import (
    AssetExploreItem,
    ExploreAssetsResponse,
    ExploreHistoryPoint,
    ExploreHistoryResponse,
)

logger = logging.getLogger(__name__)


_CACHE_TTL_SECONDS = 30
_HISTORY_LOOKBACK = "3mo"  # enough for 30d realized vol + change windows
_STALE_WINDOW_SECONDS = 24 * 3600  # >24h since last bar → "stale"


# ── Plain-English explanations ────────────────────────────────────────────


_EXPLANATIONS_TEMPLATES = {
    "current_price": "Latest price the on-chain oracle quoted. Settlement on Arc uses this.",
    "change_24h_pct": (
        "Percentage move in the last trading day. Positive = up. "
        "Daily moves bigger than {vol_daily_pct:.1f}% are unusual for this asset."
    ),
    "change_7d_pct": "Percentage move over the past week (5 trading days).",
    "change_30d_pct": "Percentage move over the past month (≈21 trading days).",
    "realized_vol_30d": (
        "How much the price wobbles. Higher = bigger swings. {vol:.2f} annualized "
        "means daily moves of ~{vol_daily_pct:.1f}% are typical."
    ),
}


def _explanations_for(item: dict[str, Any]) -> dict[str, str]:
    vol = item.get("realized_vol_30d") or 0.0
    vol_daily_pct = (vol / math.sqrt(252)) * 100.0 if vol else 0.0
    fields = {}
    for key, template in _EXPLANATIONS_TEMPLATES.items():
        if item.get(key) is None:
            continue
        try:
            fields[key] = template.format(vol=vol, vol_daily_pct=vol_daily_pct)
        except (KeyError, IndexError):
            fields[key] = template
    return fields


# ── Stat math ─────────────────────────────────────────────────────────────


def _pct_change(prices: list[float], n: int) -> float | None:
    """Pct change between prices[-1] and prices[-1-n]. None if not enough data."""
    if not prices or len(prices) < n + 1:
        return None
    end, start = prices[-1], prices[-1 - n]
    if not start:
        return None
    return (end - start) / start * 100.0


def _realized_vol_annual(prices: list[float], window: int = 30) -> float | None:
    """Annualized realized vol over the most recent ``window`` trading days."""
    if not prices or len(prices) < window + 1:
        return None
    tail = prices[-(window + 1):]
    rets = []
    for i in range(1, len(tail)):
        prev = tail[i - 1]
        if not prev:
            continue
        rets.append((tail[i] - prev) / prev)
    if len(rets) < 2:
        return None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(252)


# ── Service ───────────────────────────────────────────────────────────────


class AssetMarketService:
    """Composes per-synth market stats from histories. 30s TTL cache."""

    def __init__(self) -> None:
        self._cache: ExploreAssetsResponse | None = None
        self._cache_ts: float = 0.0
        self._cache_history: dict[str, ExploreHistoryResponse] = {}

    async def list_assets(self) -> ExploreAssetsResponse:
        now = time.time()
        if self._cache and (now - self._cache_ts) < _CACHE_TTL_SECONDS:
            return self._cache

        # Fetch in a thread — yfinance is blocking and slow.
        try:
            from archimedes.services.strategy_signal_evaluator import (
                DEFAULT_SCAN_UNIVERSE, GLOBAL_ASSETS, _fetch_price_histories,
            )
            histories = await asyncio.wait_for(
                asyncio.to_thread(_fetch_price_histories, DEFAULT_SCAN_UNIVERSE, _HISTORY_LOOKBACK),
                timeout=20.0,
            )
        except Exception as exc:
            logger.warning("explore: history fetch failed: %s", exc)
            histories = {}

        try:
            from archimedes.chain.client import chain_client
            oracle_addrs = chain_client.settings.oracle_addresses or {}
            synth_addrs = chain_client.settings.synth_addresses or {}
        except Exception:
            oracle_addrs, synth_addrs = {}, {}

        items: list[AssetExploreItem] = []
        nowstamp = datetime.now(timezone.utc).isoformat()
        for synth, hist in histories.items():
            prices = hist.get("close") if isinstance(hist, dict) else None
            if not prices:
                continue
            current = prices[-1]
            stat_dict: dict[str, Any] = {
                "current_price": current,
                "change_24h_pct": _pct_change(prices, 1),
                "change_7d_pct": _pct_change(prices, 5),
                "change_30d_pct": _pct_change(prices, 21),
                "realized_vol_30d": _realized_vol_annual(prices, 30),
            }
            entry = GLOBAL_ASSETS.get(synth)
            asset_class = entry[2] if entry else "unknown"
            real_ticker = entry[0] if entry else synth.lstrip("s")
            last_ts = hist.get("last_ts") if isinstance(hist, dict) else None
            is_stale = bool(last_ts and (time.time() - float(last_ts)) > _STALE_WINDOW_SECONDS)
            items.append(AssetExploreItem(
                symbol=synth,
                name=f"Synthetic {real_ticker}",
                asset_class=asset_class,
                oracle_address=oracle_addrs.get(synth) or synth_addrs.get(synth),
                last_updated=nowstamp,
                is_stale=is_stale,
                explanations=_explanations_for(stat_dict),
                **stat_dict,
            ))

        # Stable ordering — equities first, then crypto, then everything else.
        items.sort(key=lambda a: (
            0 if "equity" in a.asset_class else 1 if "crypto" in a.asset_class else 2,
            a.symbol,
        ))

        self._cache = ExploreAssetsResponse(
            assets=items, cache_ttl_seconds=_CACHE_TTL_SECONDS, generated_at=nowstamp,
        )
        self._cache_ts = now
        return self._cache

    async def get_history(self, symbol: str) -> ExploreHistoryResponse:
        if symbol in self._cache_history:
            return self._cache_history[symbol]
        try:
            from archimedes.services.strategy_signal_evaluator import _fetch_price_histories
            histories = await asyncio.to_thread(_fetch_price_histories, [symbol], _HISTORY_LOOKBACK)
        except Exception as exc:
            logger.warning("explore: history for %s failed: %s", symbol, exc)
            histories = {}
        hist = histories.get(symbol) or {}
        prices = hist.get("close") or []
        dates = hist.get("dates") or []
        points = [
            ExploreHistoryPoint(ts=str(dates[i]) if i < len(dates) else "", price=prices[i])
            for i in range(len(prices))
        ]
        resp = ExploreHistoryResponse(symbol=symbol, points=points)
        self._cache_history[symbol] = resp
        return resp


asset_market_service = AssetMarketService()
