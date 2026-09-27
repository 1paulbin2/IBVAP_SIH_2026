"""Tests for the Redis Pub/Sub foundation (PART 4.2).

These are unit tests using mocks. They do not require a running Redis server.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.core import redis_pubsub as pubsub_mod


@pytest.mark.asyncio
async def test_publish_event_serialises_and_publishes(monkeypatch):
    """publish_event should serialize the event and publish it."""
    mock_client = AsyncMock()
    mock_client.publish = AsyncMock(return_value=1)

    async def fake_get_redis():
        return mock_client

    monkeypatch.setattr(pubsub_mod, "get_redis", fake_get_redis)

    event = {"type": "test", "data": {"value": 42}}

    result = await pubsub_mod.publish_event(event)

    expected_payload = json.dumps(event)

    mock_client.publish.assert_awaited_once_with(
        pubsub_mod.EVENT_CHANNEL,
        expected_payload,
    )
    assert result == 1


@pytest.mark.asyncio
async def test_publish_event_supports_custom_channel(monkeypatch):
    """publish_event should support an explicitly supplied channel."""
    mock_client = AsyncMock()
    mock_client.publish = AsyncMock(return_value=2)

    async def fake_get_redis():
        return mock_client

    monkeypatch.setattr(pubsub_mod, "get_redis", fake_get_redis)

    event = {"type": "custom_test"}

    result = await pubsub_mod.publish_event(
        event,
        channel="ibvap.test",
    )

    mock_client.publish.assert_awaited_once_with(
        "ibvap.test",
        json.dumps(event),
    )
    assert result == 2


@pytest.mark.asyncio
async def test_get_subscriber_subscribes_to_default_channel(monkeypatch):
    """get_subscriber should subscribe to the default event channel."""
    mock_pubsub = AsyncMock()
    mock_client = MagicMock()
    mock_client.pubsub.return_value = mock_pubsub

    async def fake_get_redis():
        return mock_client

    monkeypatch.setattr(pubsub_mod, "get_redis", fake_get_redis)

    result = await pubsub_mod.get_subscriber()

    mock_client.pubsub.assert_called_once_with()
    mock_pubsub.subscribe.assert_awaited_once_with(
        pubsub_mod.EVENT_CHANNEL
    )
    assert result is mock_pubsub


@pytest.mark.asyncio
async def test_get_subscriber_supports_custom_channel(monkeypatch):
    """get_subscriber should support an explicitly supplied channel."""
    mock_pubsub = AsyncMock()
    mock_client = MagicMock()
    mock_client.pubsub.return_value = mock_pubsub

    async def fake_get_redis():
        return mock_client

    monkeypatch.setattr(pubsub_mod, "get_redis", fake_get_redis)

    result = await pubsub_mod.get_subscriber("ibvap.test")

    mock_client.pubsub.assert_called_once_with()
    mock_pubsub.subscribe.assert_awaited_once_with("ibvap.test")
    assert result is mock_pubsub


@pytest.mark.asyncio
async def test_close_subscriber_unsubscribes_and_closes():
    """close_subscriber should unsubscribe and close the Pub/Sub client."""
    mock_pubsub = AsyncMock()

    await pubsub_mod.close_subscriber(mock_pubsub)

    mock_pubsub.unsubscribe.assert_awaited_once_with(
        pubsub_mod.EVENT_CHANNEL
    )
    mock_pubsub.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_subscriber_supports_custom_channel():
    """close_subscriber should support an explicitly supplied channel."""
    mock_pubsub = AsyncMock()

    await pubsub_mod.close_subscriber(
        mock_pubsub,
        channel="ibvap.test",
    )

    mock_pubsub.unsubscribe.assert_awaited_once_with("ibvap.test")
    mock_pubsub.close.assert_awaited_once()
