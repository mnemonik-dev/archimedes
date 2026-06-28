"""Wallet-less generation quota — a strict per-IP daily cap (anti-abuse).

The Generate path is intentionally **open** (`REQUIRE_SIWE_FOR_GENERATION` off) so
visitors — humans *and* agents — can try the product before connecting a wallet
(value-before-wallet, #787). But an open LLM-spending endpoint is a flood/abuse
risk: an agent in a loop could hammer `/api/generate/start` and burn LLM budget.

This module caps **wallet-less** generations to a small daily allowance per client
IP. Authenticated (SIWE-wallet) callers bypass the cap entirely. When the cap is
hit we return HTTP 429 with a steering payload — so the cap doubles as a
**conversion prompt** ("connect a wallet to keep generating") rather than a dead
end.

Defense in depth: this sits *on top of* the existing slowapi per-route limit
(`5/minute`) and the nginx `limit_req_zone` per-IP limits — those bound the burst
*rate*; this bounds the wallet-less *daily volume*.

Rigor + keying:
  - Keyed on the **real client IP**, read from the `X-Real-IP` header that nginx
    sets from its `real_ip`-resolved `$remote_addr`. nginx overwrites any
    client-supplied value and binds `real_ip_header` to the trusted ALB CIDR, so
    this header is not client-spoofable. (Uvicorn runs without `--proxy-headers`,
    so `request.client.host` is nginx, not the client — hence we read the header.)
  - IP-keyed on purpose: an agent that drops the anonymous `archimedes_vid` cookie
    would defeat a cookie-keyed cap. A sophisticated IP-rotating abuser is out of
    scope for this MVP cap (the slowapi + nginx limits remain the rate backstop).

Fail-open: a Redis error returns "allowed" (logged at WARNING). Blocking every
wallet-less generation during a Redis blip would be worse than the narrow abuse
window, and the slowapi/nginx rate limits remain in force regardless. Set
`WALLET_LESS_GENERATION_DAILY_CAP=0` to disable the cap (unlimited).
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime

import redis.asyncio as aioredis
from fastapi import HTTPException
from starlette.requests import Request

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_DEFAULT_DAILY_CAP = 5
# Day-bucket TTL: a bit over 24h to cover the UTC-day boundary + clock skew, so
# each key self-expires and the allowance resets daily without a sweep.
_QUOTA_TTL_SECONDS = 36 * 60 * 60


def daily_cap() -> int:
    """The wallet-less daily generation cap. ``<= 0`` disables the cap."""
    raw = os.getenv("WALLET_LESS_GENERATION_DAILY_CAP", str(_DEFAULT_DAILY_CAP))
    try:
        return int(raw)
    except ValueError:
        logger.warning("invalid WALLET_LESS_GENERATION_DAILY_CAP=%r; using default %d", raw, _DEFAULT_DAILY_CAP)
        return _DEFAULT_DAILY_CAP


def client_ip(request: Request) -> str:
    """Resolve the real client IP behind nginx/ALB.

    Prefers ``X-Real-IP`` (nginx-set, not client-spoofable), then the first hop of
    ``X-Forwarded-For``, then the socket peer. Returns ``"unknown"`` if nothing is
    available (a single shared bucket — still capped, just coarser).
    """
    xri = request.headers.get("x-real-ip")
    if xri and xri.strip():
        return xri.strip()
    xff = request.headers.get("x-forwarded-for")
    if xff and xff.strip():
        return xff.split(",")[0].strip()
    client = request.client
    return client.host if client and client.host else "unknown"


class GenerationQuota:
    """Fail-safe Redis wrapper for the per-IP daily wallet-less generation cap."""

    def __init__(self, url: str | None = None) -> None:
        self._url = url or REDIS_URL
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(self._url, decode_responses=True)
        return self._redis

    async def check_and_increment(self, ip: str, cap: int) -> tuple[bool, int]:
        """Atomically count this wallet-less generation for ``ip`` today.

        Returns ``(allowed, used)`` where ``used`` is the count *after* this
        attempt. ``allowed`` is ``used <= cap``. **Fails open** — on any Redis
        error returns ``(True, 0)`` so a cache outage never blocks generation
        (the slowapi/nginx rate limits remain the backstop).
        """
        try:
            r = await self._get_redis()
            day = datetime.now(UTC).strftime("%Y-%m-%d")
            key = f"archimedes:genquota:{day}:{ip}"
            count = await r.incr(key)
            if count == 1:
                # First use today — stamp the TTL so the bucket self-expires.
                await r.expire(key, _QUOTA_TTL_SECONDS)
            return (count <= cap, int(count))
        except Exception as exc:
            logger.warning("generation quota check failed for ip=%s — FAILING OPEN: %s", ip, exc)
            return (True, 0)

    async def close(self) -> None:
        if self._redis:
            try:
                await self._redis.aclose()
            except Exception as exc:
                logger.debug("generation quota close failed: %s", exc)
            self._redis = None


async def enforce_generation_quota(request: Request, wallet: str | None) -> None:
    """Enforce the wallet-less daily generation cap. Raises HTTP 429 when exceeded.

    - Authenticated (``wallet`` truthy) callers bypass the cap.
    - A cap of ``<= 0`` disables enforcement (unlimited).
    - On the cap being hit, raises 429 with a structured, UI-friendly payload so
      the frontend can turn the limit into a connect-wallet prompt.
    """
    if wallet:
        return
    cap = daily_cap()
    if cap <= 0:
        return

    ip = client_ip(request)
    quota = GenerationQuota()
    try:
        allowed, used = await quota.check_and_increment(ip, cap)
    finally:
        await quota.close()

    if not allowed:
        logger.info("wallet-less generation cap hit ip=%s used=%d cap=%d", ip, used, cap)
        raise HTTPException(
            status_code=429,
            detail={
                "message": (
                    f"You've reached the free generation limit ({cap}/day). "
                    "Connect a wallet to keep generating — it's free and takes a few seconds."
                ),
                "reason": "wallet_less_generation_cap",
                "cap": cap,
            },
        )
