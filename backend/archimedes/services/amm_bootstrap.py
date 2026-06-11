"""Quick AMM liquidity bootstrap — callable from API to add pool liquidity on-demand.

Adds USDC + synth token liquidity to all AMM pools using the Circle wallet.
This is needed because the initial bootstrap didn't add AMM pool liquidity.
"""

from __future__ import annotations

import logging

from archimedes.chain.circle_signer import circle_signer
from archimedes.chain.client import chain_client
from archimedes.chain.contracts import get_contract_loader

logger = logging.getLogger(__name__)


async def bootstrap_amm_liquidity(usdc_per_pool: float | None = None) -> dict:
    """Add liquidity to all AMM pools that have zero or insufficient reserves.

    If usdc_per_pool is None (default), auto-calculates from the operator
    wallet's USDC balance divided by the number of empty pools. This
    ensures we use whatever funds are available rather than failing when
    the wallet has less than the ideal $1500.

    Idempotent: skips pools that already have reserves above the target.
    Returns a dict of results per pool.
    """
    if not circle_signer.is_configured:
        return {"error": "Circle wallet not configured"}

    loader = get_contract_loader()
    router = loader.amm_router
    usdc_address = chain_client.settings.usdc_address
    synth_addresses = chain_client.settings.synth_addresses

    # Auto-calculate usdc_per_pool from wallet balance if not specified
    if usdc_per_pool is None:
        try:
            usdc_contract = loader.usdc()
            wallet_addr = chain_client.to_checksum("0xc221dcd6fe7d81ff741f94c08e61f52bea1f9ac9")
            balance_raw = await usdc_contract.functions.balanceOf(wallet_addr).call()
            wallet_usdc = balance_raw / 1e6
            # Count empty pools
            empty_count = 0
            for _sym, addr in synth_addresses.items():
                if not addr:
                    continue
                try:
                    pool_addr = await router.functions.getPool(
                        chain_client.to_checksum(usdc_address), chain_client.to_checksum(addr)
                    ).call()
                    if pool_addr != "0x" + "0" * 40:
                        pool = loader.amm_pool(pool_addr)
                        r0 = await pool.functions.reserve0().call()
                        if r0 == 0:
                            empty_count += 1
                except Exception:
                    empty_count += 1
            if empty_count > 0 and wallet_usdc > 2.0:
                # Reserve $2 for gas, split rest across empty pools
                usdc_per_pool = (wallet_usdc - 2.0) / empty_count
                logger.info(
                    "Auto-calculated $%.2f per pool (%d empty, $%.2f available)",
                    usdc_per_pool,
                    empty_count,
                    wallet_usdc,
                )
            else:
                usdc_per_pool = 5.0  # minimum fallback
                logger.info("Fallback: $%.2f per pool (wallet: $%.2f)", usdc_per_pool, wallet_usdc)
        except Exception as exc:
            logger.warning("Balance check failed, using $5/pool fallback: %s", exc)
            usdc_per_pool = 5.0

    results = {}

    for symbol, token_addr in synth_addresses.items():
        if not token_addr:
            continue

        try:
            # Check if pool exists
            pool_addr = await router.functions.getPool(
                chain_client.to_checksum(usdc_address),
                chain_client.to_checksum(token_addr),
            ).call()

            if pool_addr == "0x0000000000000000000000000000000000000000":
                results[symbol] = {"status": "skipped", "reason": "no pool"}
                continue

            # Idempotent: skip pools that already have sufficient reserves
            pool_contract = loader.amm_pool(pool_addr)
            try:
                r0 = await pool_contract.functions.reserve0().call()
                r1 = await pool_contract.functions.reserve1().call()
                existing_usdc = max(r0, r1) / 1e6  # rough — larger reserve is likely USDC
                if existing_usdc >= usdc_per_pool * 0.5:  # already has meaningful liquidity
                    results[symbol] = {"status": "skipped", "reason": f"already has ${existing_usdc:.0f} reserve"}
                    continue
            except Exception:
                pass  # can't read reserves — try to add anyway

            # Get oracle price
            oracle = loader.oracle_for(symbol)
            price_raw = await oracle.functions.price().call()
            price_usd = price_raw / 1e6

            if price_usd <= 0:
                results[symbol] = {"status": "skipped", "reason": "zero price"}
                continue

            # Compute amounts
            usdc_raw = int(usdc_per_pool * 1e6)
            token_amount = usdc_per_pool / price_usd
            token_raw = int(token_amount * 1e18)

            if token_raw <= 0:
                results[symbol] = {"status": "skipped", "reason": "amount too small"}
                continue

            # Approve router to spend tokens
            await circle_signer.execute_contract(
                contract_address=usdc_address,
                abi_function="approve(address,uint256)",
                abi_params=[chain_client.settings.amm_router_address, usdc_raw],
            )

            await circle_signer.execute_contract(
                contract_address=token_addr,
                abi_function="approve(address,uint256)",
                abi_params=[chain_client.settings.amm_router_address, token_raw],
            )

            # Add liquidity
            tx_hash = await circle_signer.execute_contract(
                contract_address=chain_client.settings.amm_router_address,
                abi_function="addLiquidity(address,address,uint256,uint256,uint256)",
                abi_params=[
                    chain_client.to_checksum(usdc_address),
                    chain_client.to_checksum(token_addr),
                    usdc_raw,
                    token_raw,
                    0,  # min LP tokens
                ],
            )

            results[symbol] = {
                "status": "success",
                "usdc_added": usdc_per_pool,
                "tokens_added": round(token_amount, 6),
                "tx_hash": tx_hash[:16] + "...",
            }
            logger.info("Added liquidity to %s pool: $%.0f USDC + %.4f tokens", symbol, usdc_per_pool, token_amount)

        except Exception as e:
            results[symbol] = {"status": "failed", "error": str(e)[:100]}
            logger.error("Failed to add liquidity to %s pool: %s", symbol, e)

    return results
