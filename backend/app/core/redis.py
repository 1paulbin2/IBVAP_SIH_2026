# -*- coding: utf-8 -*-
"""Async Redis client foundation for IBVAP.

Provides a reusable, application-level async Redis client with:
- Singleton pattern (one connection per process)
- Health-check / connectivity verification
- Clean shutdown support

Redis is used only for ephemeral operational data (future: caching,
pub/sub coordination). PostgreSQL remains the authoritative persistent
database for all domain entities.
"""

import os
from typing import Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from backend.app.core.config import settings

_redis_client: Optional[Redis] = None


def get_redis_url() -> str:
    """Return the Redis URL from settings or environment.

    A safe default is provided in Settings but this helper allows
    overriding via an explicit environment variable at runtime.
    """
    return os.getenv("REDIS_URL", settings.REDIS_URL)


async def get_redis() -> Redis:
    """Return a singleton async Redis client.

    The client is created on first use and reused for subsequent calls.
    It is deliberately *not* tied to an HTTP request lifecycle -- the
    FastAPI endpoints can depend on this function if they need Redis.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(get_redis_url(), decode_responses=True)
    return _redis_client


async def close_redis() -> None:
    """Close the global Redis client if it exists.

    This can be called from FastAPI shutdown events or during test
    teardown. It ensures a clean connection close without raising if the
    client was never created.
    """
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


async def check_redis_connection() -> bool:
    """Health-check helper analogous to ``check_db_connection``.

    Returns ``True`` when a ``PING`` succeeds, otherwise ``False``.
    No connection details are leaked -- only a boolean result.
    """
    try:
        client = await get_redis()
        result = await client.ping()
        return bool(result)
    except Exception:
        return False
