"""/api/explore — Asset discovery surface for the spine.

Read-only; no wallet gate. Per page-roles-spec.md, Explore is "the universe of
tradable assets, demystified" — current oracle prices + plain-English stats.

Lives in its own router file per cross-cutting principle #2 (no new endpoints
in routes.py).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from archimedes.api.explore_schemas import ExploreAssetsResponse, ExploreHistoryResponse
from archimedes.services.asset_market_service import asset_market_service

explore_router = APIRouter(prefix="/api/explore", tags=["explore"])


@explore_router.get("/assets", response_model=ExploreAssetsResponse)
async def list_explore_assets() -> ExploreAssetsResponse:
    """All available synth assets with current price + change windows + vol."""
    return await asset_market_service.list_assets()


@explore_router.get("/assets/{symbol}/history", response_model=ExploreHistoryResponse)
async def get_explore_history(symbol: str) -> ExploreHistoryResponse:
    """Daily price history for one asset, used by sparklines + detail charts."""
    resp = await asset_market_service.get_history(symbol)
    if not resp.points:
        raise HTTPException(
            status_code=404,
            detail=f"No price history available for {symbol}. Check the symbol spelling.",
        )
    return resp
