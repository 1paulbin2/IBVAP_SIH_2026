"""Redis Pub/Sub foundation for IBVAP realtime events.

Redis is used only for transient realtime messaging. PostgreSQL remains
the authoritative persistent database for all domain entities.
"""

import json
from typing import Any, Dict

from redis.asyncio.client import PubSub

from backend.app.core.redis import get_redis


EVENT_CHANNEL: str = "ibvap.events"


async def publish_event(
    event: Dict[str, Any],
    channel: str = EVENT_CHANNEL,
) -> int:
    """Publish a JSON-serializable event to a Redis channel."""
    payload = json.dumps(event)
    client = await get_redis()
    return await client.publish(channel, payload)


async def get_subscriber(
    channel: str = EVENT_CHANNEL,
) -> PubSub:
    """Create and subscribe a Redis Pub/Sub client to a channel."""
    client = await get_redis()
    pubsub = client.pubsub()
    await pubsub.subscribe(channel)
    return pubsub


async def close_subscriber(
    pubsub: PubSub,
    channel: str = EVENT_CHANNEL,
) -> None:
    """Unsubscribe and close a Redis Pub/Sub client."""
    await pubsub.unsubscribe(channel)
    await pubsub.close()
