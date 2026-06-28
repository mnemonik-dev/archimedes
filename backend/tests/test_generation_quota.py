"""Tests for the wallet-less generation quota (anti-abuse per-IP daily cap).

Hermetic — mocks at the Redis boundary; tests the cap logic, the real-IP
resolver, the 429 steering response, the authenticated bypass, and fail-open.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from archimedes.services.generation_quota import (
    GenerationQuota,
    client_ip,
    daily_cap,
    enforce_generation_quota,
)
from fastapi import HTTPException


def _mock_redis(incr_return: int):
    r = MagicMock()
    r.incr = AsyncMock(return_value=incr_return)
    r.expire = AsyncMock(return_value=True)
    return r


def _req(headers: dict | None = None, client_host: str | None = None):
    client = SimpleNamespace(host=client_host) if client_host else None
    return SimpleNamespace(headers=headers or {}, client=client)


# ─── GenerationQuota.check_and_increment ─────────────────────────────────


async def test_under_cap_allowed():
    q = GenerationQuota()
    q._get_redis = AsyncMock(return_value=_mock_redis(3))
    allowed, used = await q.check_and_increment("1.2.3.4", 5)
    assert allowed is True
    assert used == 3


async def test_at_cap_allowed():
    q = GenerationQuota()
    q._get_redis = AsyncMock(return_value=_mock_redis(5))
    allowed, used = await q.check_and_increment("1.2.3.4", 5)
    assert allowed is True  # the 5th is still allowed
    assert used == 5


async def test_over_cap_not_allowed():
    q = GenerationQuota()
    q._get_redis = AsyncMock(return_value=_mock_redis(6))
    allowed, used = await q.check_and_increment("1.2.3.4", 5)
    assert allowed is False
    assert used == 6


async def test_first_use_sets_ttl():
    r = _mock_redis(1)
    q = GenerationQuota()
    q._get_redis = AsyncMock(return_value=r)
    await q.check_and_increment("1.2.3.4", 5)
    r.expire.assert_awaited_once()  # TTL stamped exactly on the first use


async def test_subsequent_use_does_not_reset_ttl():
    r = _mock_redis(2)
    q = GenerationQuota()
    q._get_redis = AsyncMock(return_value=r)
    await q.check_and_increment("1.2.3.4", 5)
    r.expire.assert_not_awaited()  # don't slide the window on every hit


async def test_check_fails_open_on_redis_error():
    q = GenerationQuota()
    q._get_redis = AsyncMock(side_effect=ConnectionError("redis down"))
    allowed, used = await q.check_and_increment("1.2.3.4", 5)
    assert allowed is True  # fail OPEN — never block on a cache outage
    assert used == 0


# ─── client_ip resolver ──────────────────────────────────────────────────


def test_client_ip_prefers_x_real_ip():
    req = _req({"x-real-ip": "9.9.9.9", "x-forwarded-for": "1.1.1.1"})
    assert client_ip(req) == "9.9.9.9"


def test_client_ip_xff_first_hop_fallback():
    req = _req({"x-forwarded-for": "1.1.1.1, 2.2.2.2, 3.3.3.3"})
    assert client_ip(req) == "1.1.1.1"


def test_client_ip_socket_fallback():
    assert client_ip(_req({}, client_host="3.3.3.3")) == "3.3.3.3"


def test_client_ip_unknown_when_nothing_available():
    assert client_ip(_req({})) == "unknown"


# ─── enforce_generation_quota ────────────────────────────────────────────


async def test_enforce_skips_authenticated_wallet(monkeypatch):
    called = {"n": 0}

    class Boom:
        async def check_and_increment(self, *a):
            called["n"] += 1
            return (False, 99)

        async def close(self):
            pass

    monkeypatch.setattr("archimedes.services.generation_quota.GenerationQuota", Boom)
    # A wallet-bearing caller must bypass the cap entirely — never touch Redis.
    await enforce_generation_quota(_req({"x-real-ip": "1.1.1.1"}), wallet="0xabc")
    assert called["n"] == 0


async def test_enforce_disabled_when_cap_zero(monkeypatch):
    monkeypatch.setenv("WALLET_LESS_GENERATION_DAILY_CAP", "0")
    called = {"n": 0}

    class Boom:
        async def check_and_increment(self, *a):
            called["n"] += 1
            return (False, 99)

        async def close(self):
            pass

    monkeypatch.setattr("archimedes.services.generation_quota.GenerationQuota", Boom)
    await enforce_generation_quota(_req({"x-real-ip": "1.1.1.1"}), wallet=None)
    assert called["n"] == 0


async def test_enforce_allows_under_cap(monkeypatch):
    monkeypatch.setenv("WALLET_LESS_GENERATION_DAILY_CAP", "5")

    class Under:
        async def check_and_increment(self, ip, cap):
            return (True, 2)

        async def close(self):
            pass

    monkeypatch.setattr("archimedes.services.generation_quota.GenerationQuota", Under)
    # No raise.
    await enforce_generation_quota(_req({"x-real-ip": "1.1.1.1"}), wallet=None)


async def test_enforce_raises_429_over_cap(monkeypatch):
    monkeypatch.setenv("WALLET_LESS_GENERATION_DAILY_CAP", "5")

    class Over:
        async def check_and_increment(self, ip, cap):
            return (False, 6)

        async def close(self):
            pass

    monkeypatch.setattr("archimedes.services.generation_quota.GenerationQuota", Over)
    with pytest.raises(HTTPException) as ei:
        await enforce_generation_quota(_req({"x-real-ip": "1.1.1.1"}), wallet=None)
    assert ei.value.status_code == 429
    assert ei.value.detail["reason"] == "wallet_less_generation_cap"
    assert ei.value.detail["cap"] == 5
    assert "Connect a wallet" in ei.value.detail["message"]


# ─── daily_cap config ────────────────────────────────────────────────────


def test_daily_cap_default(monkeypatch):
    monkeypatch.delenv("WALLET_LESS_GENERATION_DAILY_CAP", raising=False)
    assert daily_cap() == 5


def test_daily_cap_env_override(monkeypatch):
    monkeypatch.setenv("WALLET_LESS_GENERATION_DAILY_CAP", "3")
    assert daily_cap() == 3


def test_daily_cap_invalid_falls_back(monkeypatch):
    monkeypatch.setenv("WALLET_LESS_GENERATION_DAILY_CAP", "not-an-int")
    assert daily_cap() == 5
