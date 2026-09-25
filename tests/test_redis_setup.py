import os
import pytest
from unittest.mock import AsyncMock, patch

# Import the module under test
from backend.app.core import redis as redis_mod


@pytest.mark.asyncio
async def test_get_redis_returns_singleton(monkeypatch):
    """Ensure get_redis returns the same client instance on multiple calls.

    The actual Redis client is mocked to avoid network activity.
    """
    mock_client = AsyncMock()
    # Patch the redis.from_url function to return our mock
    monkeypatch.setattr(redis_mod.redis, "from_url", lambda url, **kwargs: mock_client)

    client1 = await redis_mod.get_redis()
    client2 = await redis_mod.get_redis()
    assert client1 is client2
    # Ensure the from_url was called exactly once
    assert redis_mod.redis.from_url.call_count == 1


@pytest.mark.asyncio
async def test_check_redis_connection_success(monkeypatch):
    """check_redis_connection should return True when ping succeeds."""
    mock_client = AsyncMock()
    mock_client.ping.return_value = True
    monkeypatch.setattr(redis_mod, "get_redis", AsyncMock(return_value=mock_client))
    assert await redis_mod.check_redis_connection() is True
    mock_client.ping.assert_awaited_once()


# Optional integration test – runs only if a real Redis URL is provided.
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("REDIS_URL") and not os.getenv("TEST_REDIS_URL"),
    reason="Redis server URL not configured",
)
async def test_check_redis_connection_real():
    """Perform a real ping against the configured Redis instance.

    This test is skipped in CI unless REDIS_URL or TEST_REDIS_URL is set.
    """
    # If TEST_REDIS_URL is defined, temporarily override settings.
    from backend.app.core import config, redis as redis_mod

    original_url = config.settings.REDIS_URL
    test_url = os.getenv("TEST_REDIS_URL") or os.getenv("REDIS_URL")
    # Patch the environment variable used by get_redis_url
    os.environ["REDIS_URL"] = test_url
    try:
        # Force recreation of client
        await redis_mod.close_redis()
        result = await redis_mod.check_redis_connection()
        assert result is True
    finally:
        # Restore original settings and close client
        os.environ["REDIS_URL"] = original_url
        await redis_mod.close_redis()
