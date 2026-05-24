"""Shared rate limiter instance for the Archimedes API.

Extracted from ``main.py`` to avoid circular imports — route modules need the
``limiter`` object to decorate endpoints, but ``main.py`` imports those same
route modules. By defining the limiter here, both can import it without cycles.

Usage in route files::

    from archimedes.api.limiter import limiter

    @router.post("/heavy-endpoint")
    @limiter.limit("5/minute")
    async def heavy_endpoint(request: Request):
        ...

The limiter is Redis-backed when ``REDIS_URL`` is available (production / ASG),
falling back to in-memory storage for local dev and CI.
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

_redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")

# Try Redis first; fall back to in-memory when unavailable.
try:
    import redis as _redis

    _r = _redis.Redis.from_url(_redis_url)
    _r.ping()
    _storage_uri = _redis_url
except Exception:
    _storage_uri = "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_storage_uri,
    default_limits=["60/minute"],  # default for undecorated routes
    headers_enabled=True,  # X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
    enabled=not os.getenv("TESTING"),  # disable in pytest
)
