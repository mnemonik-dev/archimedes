"""Agent status / bootstrap endpoints — /api/agent/*."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter

from archimedes.api.schemas import AgentStatusResponse
from archimedes.chain.executor import chain_executor

agent_router = APIRouter(prefix="/api/agent", tags=["agent"])


@agent_router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status():
    """Get autonomous agent health and state -- reads from Redis."""
    from datetime import datetime, timezone
    from archimedes.services.redis_state import AgentStateStore

    state = AgentStateStore()
    try:
        heartbeat = await state.get_heartbeat()
        regime_data = await state.load_regime()
        events = await state.get_events(count=10)
    except Exception:
        heartbeat = None
        regime_data = None
        events = []
    finally:
        await state.close()

    alive = False
    if heartbeat:
        try:
            hb_time = datetime.fromisoformat(heartbeat)
            age = (datetime.now(timezone.utc) - hb_time).total_seconds()
            alive = age < 600
        except Exception:
            pass

    regime = regime_data.get("regime") if regime_data else None
    confidence = regime_data.get("confidence") if regime_data else None
    source = regime_data.get("source") if regime_data else None
    strat_count = regime_data.get("strategy_count", 0) if regime_data else 0

    vault_count = 0
    try:
        vaults = await chain_executor.get_all_vaults()
        vault_count = len(vaults) if vaults else 0
    except Exception:
        pass

    return AgentStatusResponse(
        alive=alive,
        last_heartbeat=heartbeat,
        regime=regime,
        regime_confidence=confidence,
        regime_source=source,
        strategy_count=strat_count,
        managed_vaults=vault_count,
        recent_events=events,
    )


@agent_router.get("/circle-status")
async def get_circle_integration_status():
    """Get Circle SDK integration breadth status."""
    from archimedes.services.circle_service import circle_service
    return await circle_service.get_integration_status()


@agent_router.post("/bootstrap-liquidity")
async def bootstrap_amm_liquidity():
    """Add AMM pool liquidity so vault rebalances can execute."""
    from archimedes.services.amm_bootstrap import bootstrap_amm_liquidity as _bootstrap

    async def _run():
        try:
            await _bootstrap()
        except Exception:
            pass

    asyncio.create_task(_run())
    return {"status": "started", "message": "Liquidity bootstrap running in background. Check /api/swap/pools in 2-3 minutes."}
