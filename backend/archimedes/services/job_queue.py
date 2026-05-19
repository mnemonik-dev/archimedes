"""Redis-backed async job queue for strategy generation.

Jobs are stored as Redis hashes with a TTL. States: queued → running → done | failed.
Uses the same aioredis pattern as redis_state.py.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
KEY_PREFIX = "archimedes:job:"
JOB_TTL = 3600  # 1 hour


class JobStore:
    """Thin Redis wrapper for async job lifecycle."""

    def __init__(self, url: str | None = None) -> None:
        self._url = url or REDIS_URL
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(self._url, decode_responses=True)
        return self._redis

    async def enqueue(
        self,
        *,
        job_type: str,
        payload: dict[str, Any],
    ) -> str:
        """Create a queued job and return its ID."""
        job_id = uuid.uuid4().hex[:16]
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "id": job_id,
            "type": job_type,
            "status": "queued",
            "payload": json.dumps(payload, default=str),
            "result": "",
            "error": "",
            "created_at": now,
            "updated_at": now,
        }
        r = await self._get_redis()
        key = f"{KEY_PREFIX}{job_id}"
        await r.hset(key, mapping=data)
        await r.expire(key, JOB_TTL)
        logger.info("job: enqueued %s (%s)", job_id, job_type)
        return job_id

    async def get(self, job_id: str) -> dict[str, Any] | None:
        """Get job data by ID. Returns None if not found."""
        r = await self._get_redis()
        key = f"{KEY_PREFIX}{job_id}"
        raw = await r.hgetall(key)
        if not raw:
            return None
        return {
            "id": raw.get("id", job_id),
            "type": raw.get("type", ""),
            "status": raw.get("status", "unknown"),
            "payload": json.loads(raw["payload"]) if raw.get("payload") else {},
            "result": json.loads(raw["result"]) if raw.get("result") else None,
            "error": raw.get("error", ""),
            "created_at": raw.get("created_at", ""),
            "updated_at": raw.get("updated_at", ""),
        }

    async def update_status(
        self,
        job_id: str,
        status: str,
        *,
        result: dict[str, Any] | None = None,
        error: str = "",
    ) -> None:
        """Transition a job to a new status with optional result/error."""
        r = await self._get_redis()
        key = f"{KEY_PREFIX}{job_id}"
        now = datetime.now(timezone.utc).isoformat()
        updates: dict[str, str] = {
            "status": status,
            "updated_at": now,
        }
        if result is not None:
            updates["result"] = json.dumps(result, default=str)
        if error:
            updates["error"] = error
        await r.hset(key, mapping=updates)
        logger.info("job: %s → %s", job_id, status)

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()
            self._redis = None
