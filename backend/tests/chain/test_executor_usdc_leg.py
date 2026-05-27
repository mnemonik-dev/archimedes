"""Executor: USDC-denominated legs must not be treated as swaps (issue #399).

A cash / TREASURY allocation maps to USDC itself. The executor must not call
getPool(USDC, USDC) for such a leg — there is no self-pool, and doing so raised
InsufficientLiquidityError, aborting the whole rebalance before any fundable
leg was reached. These tests pin the skip behavior with a mocked router so no
chain access is required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from archimedes.chain.executor import ChainExecutor, InsufficientLiquidityError
from archimedes.models.portfolio import TradeDirection, TradeOrder

USDC = "0x3600000000000000000000000000000000000000"
SYNTH = "0xE745C07d7d32A1Ca0d6162A1c50e876619CF7388"  # sTSLA-style synth


def _executor_with_router(get_pool_return: str) -> tuple[ChainExecutor, MagicMock]:
    """Build a ChainExecutor whose AMM router.getPool returns a fixed address."""
    loader = MagicMock()
    router = MagicMock()
    get_pool_call = MagicMock()
    get_pool_call.call = AsyncMock(return_value=get_pool_return)
    router.functions.getPool = MagicMock(return_value=get_pool_call)
    loader.amm_router = router
    return ChainExecutor(loader=loader), router


@pytest.mark.asyncio
async def test_usdc_leg_skipped_no_getpool_call():
    """A USDC-denominated leg must not trigger a getPool lookup."""
    executor, router = _executor_with_router("0x" + "0" * 40)

    usdc_trade = TradeOrder(
        symbol="USDC",
        token_address=USDC,
        direction=TradeDirection.BUY,
        amount=5.0,
        estimated_usdc_value=5.0,
    )

    # Must not raise — the USDC leg is recognized as "already in cash".
    await executor._validate_trade_liquidity([usdc_trade])
    router.functions.getPool.assert_not_called()


@pytest.mark.asyncio
async def test_usdc_leg_does_not_abort_real_leg():
    """A USDC leg alongside a real synth leg must not block the synth check."""
    # getPool returns zero for any call here; the synth leg should then raise,
    # proving the synth leg WAS evaluated (i.e. the USDC leg didn't short-circuit
    # the whole loop with its own spurious error first).
    executor, router = _executor_with_router("0x" + "0" * 40)

    usdc_trade = TradeOrder(
        symbol="USDC",
        token_address=USDC,
        direction=TradeDirection.BUY,
        amount=5.0,
        estimated_usdc_value=5.0,
    )
    synth_trade = TradeOrder(
        symbol="sTSLA",
        token_address=SYNTH,
        direction=TradeDirection.BUY,
        amount=5.0,
        estimated_usdc_value=5.0,
    )

    with pytest.raises(InsufficientLiquidityError) as exc:
        await executor._validate_trade_liquidity([usdc_trade, synth_trade])

    # The error must be about the synth, never about USDC.
    assert "sTSLA" in str(exc.value)
    assert "USDC" not in str(exc.value)
    # getPool was called exactly once — for the synth, not the USDC leg.
    router.functions.getPool.assert_called_once()
