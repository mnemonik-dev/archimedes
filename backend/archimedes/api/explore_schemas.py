"""Schemas for the /explore page (asset discovery surface).

Per page-roles-spec.md, Explore is the read-only "what's tradable?" page —
no wallet required. The response includes plain-English explanations so
non-finance users can read it without a glossary.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AssetExploreItem(BaseModel):
    symbol: str
    name: str
    asset_class: str = Field(description="us_stock, us_equity_etf, crypto, etc.")
    current_price: float | None
    change_24h_pct: float | None
    change_7d_pct: float | None
    change_30d_pct: float | None
    realized_vol_30d: float | None = Field(
        default=None, description="Annualized standard deviation of daily returns over last 30 trading days"
    )
    oracle_address: str | None = None
    last_updated: str | None = Field(default=None, description="ISO8601 timestamp of last oracle price")
    is_stale: bool = Field(default=False, description="True iff oracle hasn't updated in the past staleness window")
    explanations: dict[str, str] = Field(
        default_factory=dict,
        description="Per-metric plain-English copy keyed by field name",
    )


class ExploreAssetsResponse(BaseModel):
    assets: list[AssetExploreItem]
    cache_ttl_seconds: int = 30
    generated_at: str


class ExploreHistoryPoint(BaseModel):
    ts: str  # ISO8601 date
    price: float


class ExploreHistoryResponse(BaseModel):
    symbol: str
    interval: Literal["1d"] = "1d"
    points: list[ExploreHistoryPoint]
