import os
from typing import Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from backend.app.core.config import settings

_redis_client: Optional[Redis] = None

def get_redis_url() -> str:
    " \\Return the Redis URL from settings or environment.\n\n A safe default is provided in Settings but this helper allows\n overriding via an explicit environment variable at runtime.\n \\\
 return os.getenv('REDIS_URL', settings.REDIS_URL)

async def get_redis() -> Redis:
 \\\Return a singleton async Redis client.\n\n The client is created on first use and reused for subsequent calls.\n It is deliberately *not* tied to an HTTP request lifecycle – the\n FastAPI endpoints can depend on this function if they need Redis.\n \\\
 global _redis_client
 if _redis_client is None:
 _redis_client = redis.from_url(get_redis_url(), decode_responses=True)
 return _redis_client

async def close_redis() -> None:
 \\\Close the global Redis client if it exists.\n\n This can be called from FastAPI shutdown events or during test\n teardown. It ensures a clean connection close without raising if the\n client was never created.\n \\\
 global _redis_client
 if _redis_client is not None:
 await _redis_client.close()
 _redis_client = None

async def check_redis_connection() -> bool:
 \\\Health-check helper analogous to `check_db_connection`.\n\n Returns `True` when a `PING` succeeds otherwise `False`.\n No connection details are leaked – only a boolean result.\n \\\
 try:
 client = await get_redis()
 result = await client.ping()
 return bool(result)
 except Exception:
 return False
