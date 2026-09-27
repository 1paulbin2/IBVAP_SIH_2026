"""Tests for the Redis foundation layer (PART 4.1).

Unit tests use mocks and never require a running Redis instance.
Integration tests are guarded with ``skipif`` and only run when
``REDIS_URL`` or ``TEST_REDIS_URL`` is present in the environment.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.core import redis as redis_mod
from backend.app.core.config import settings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_redis_singleton():
    """Ensure each test starts with a fresh Redis singleton state."""
    redis_mod._redis_client = None
    yield
    redis_mod._redis_client = None


# ---------------------------------------------------------------------------
# Unit tests – no Redis server required
# ---------------------------------------------------------------------------

class TestGetRedisUrl:
    """Tests for ``get_redis_url()``."""

    def test_returns_settings_url_by_default(self, monkeypatch):
        """Without REDIS_URL in env, should return settings.REDIS_URL."""
        monkeypatch.delenv("REDIS_URL", raising=False)
        url = redis_mod.get_redis_url()
        assert url == settings.REDIS_URL

    def test_env_override(self, monkeypatch):
        """When REDIS_URL is set in the environment, it takes precedence."""
        monkeypatch.setenv("REDIS_URL", "redis://custom:1234/5")
        url = redis_mod.get_redis_url()
        assert url == "redis://custom:1234/5"


class TestGetRedis:
    """Tests for the ``get_redis()`` singleton factory."""

    @pytest.mark.asyncio
    async def test_returns_client(self, monkeypatch):
        """get_redis should return an async Redis client (mocked)."""
        mock_client = AsyncMock()
        mock_from_url = MagicMock(return_value=mock_client)
        monkeypatch.setattr(redis_mod.redis, "from_url", mock_from_url)

        client = await redis_mod.get_redis()
        assert client is mock_client
        mock_from_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_singleton(self, monkeypatch):
        """Multiple calls should return the exact same client instance."""
        mock_client = AsyncMock()
        mock_from_url = MagicMock(return_value=mock_client)
        monkeypatch.setattr(redis_mod.redis, "from_url", mock_from_url)

        client1 = await redis_mod.get_redis()
        client2 = await redis_mod.get_redis()
        assert client1 is client2
        # from_url should be called only once (on first invocation)
        assert mock_from_url.call_count == 1

    @pytest.mark.asyncio
    async def test_passes_decode_responses(self, monkeypatch):
        """The client should be created with decode_responses=True."""
        mock_from_url = MagicMock(return_value=AsyncMock())
        monkeypatch.setattr(redis_mod.redis, "from_url", mock_from_url)

        await redis_mod.get_redis()
        _args, kwargs = mock_from_url.call_args
        assert kwargs.get("decode_responses") is True


class TestCloseRedis:
    """Tests for ``close_redis()``."""

    @pytest.mark.asyncio
    async def test_close_when_no_client(self):
        """close_redis should be a no-op when no client was created."""
        # Should not raise
        await redis_mod.close_redis()
        assert redis_mod._redis_client is None

    @pytest.mark.asyncio
    async def test_close_existing_client(self, monkeypatch):
        """close_redis should call .close() and reset the singleton."""
        mock_client = AsyncMock()
        mock_from_url = MagicMock(return_value=mock_client)
        monkeypatch.setattr(redis_mod.redis, "from_url", mock_from_url)

        # Create the client
        await redis_mod.get_redis()
        assert redis_mod._redis_client is not None

        # Close it
        await redis_mod.close_redis()
        mock_client.close.assert_awaited_once()
        assert redis_mod._redis_client is None

    @pytest.mark.asyncio
    async def test_close_allows_new_client(self, monkeypatch):
        """After close, get_redis should create a fresh client."""
        first = AsyncMock()
        second = AsyncMock()
        call_count = {"n": 0}

        def mock_from_url(url, **kwargs):
            call_count["n"] += 1
            return first if call_count["n"] == 1 else second

        monkeypatch.setattr(redis_mod.redis, "from_url", mock_from_url)

        c1 = await redis_mod.get_redis()
        await redis_mod.close_redis()
        c2 = await redis_mod.get_redis()

        assert c1 is first
        assert c2 is second
        assert c1 is not c2


class TestCheckRedisConnection:
    """Tests for ``check_redis_connection()``."""

    @pytest.mark.asyncio
    async def test_success(self, monkeypatch):
        """Returns True when ping succeeds."""
        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        monkeypatch.setattr(
            redis_mod, "get_redis", AsyncMock(return_value=mock_client)
        )

        assert await redis_mod.check_redis_connection() is True
        mock_client.ping.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_failure(self, monkeypatch):
        """Returns False when ping raises an exception."""
        mock_client = AsyncMock()
        mock_client.ping.side_effect = ConnectionError("refused")
        monkeypatch.setattr(
            redis_mod, "get_redis", AsyncMock(return_value=mock_client)
        )

        assert await redis_mod.check_redis_connection() is False

    @pytest.mark.asyncio
    async def test_failure_on_get_redis_error(self, monkeypatch):
        """Returns False when get_redis itself raises."""
        monkeypatch.setattr(
            redis_mod,
            "get_redis",
            AsyncMock(side_effect=ConnectionError("cannot connect")),
        )
        assert await redis_mod.check_redis_connection() is False


class TestRedisConfig:
    """Tests for REDIS_URL in Settings."""

    def test_settings_has_redis_url(self):
        """The Settings model should expose a REDIS_URL field."""
        assert hasattr(settings, "REDIS_URL")
        assert isinstance(settings.REDIS_URL, str)
        assert settings.REDIS_URL.startswith("redis://")

    def test_default_redis_url(self, monkeypatch):
        """Default REDIS_URL points to localhost:6379/0."""
        monkeypatch.delenv("REDIS_URL", raising=False)
        from backend.app.core.config import Settings
        s = Settings()
        assert s.REDIS_URL == "redis://localhost:6379/0"


# ---------------------------------------------------------------------------
# Optional integration tests – require a live Redis server
# ---------------------------------------------------------------------------

_redis_available = bool(os.getenv("REDIS_URL") or os.getenv("TEST_REDIS_URL"))


@pytest.mark.skipif(not _redis_available, reason="Redis server URL not configured")
class TestRedisIntegration:
    """Integration tests that talk to a real Redis instance.

    Skipped entirely unless REDIS_URL or TEST_REDIS_URL is set.
    """

    @pytest.mark.asyncio
    async def test_ping(self):
        """Perform a real ping against the configured Redis instance."""
        test_url = os.getenv("TEST_REDIS_URL") or os.getenv("REDIS_URL")
        original_url = os.environ.get("REDIS_URL", "")
        os.environ["REDIS_URL"] = test_url
        try:
            await redis_mod.close_redis()
            result = await redis_mod.check_redis_connection()
            assert result is True
        finally:
            if original_url:
                os.environ["REDIS_URL"] = original_url
            else:
                os.environ.pop("REDIS_URL", None)
            await redis_mod.close_redis()

    @pytest.mark.asyncio
    async def test_set_get_delete(self):
        """Basic set/get/delete round-trip on a live Redis instance."""
        test_url = os.getenv("TEST_REDIS_URL") or os.getenv("REDIS_URL")
        original_url = os.environ.get("REDIS_URL", "")
        os.environ["REDIS_URL"] = test_url
        try:
            await redis_mod.close_redis()
            client = await redis_mod.get_redis()
            key = "__ibvap_test_key__"
            await client.set(key, "hello")
            val = await client.get(key)
            assert val == "hello"
            await client.delete(key)
            val2 = await client.get(key)
            assert val2 is None
        finally:
            if original_url:
                os.environ["REDIS_URL"] = original_url
            else:
                os.environ.pop("REDIS_URL", None)
            await redis_mod.close_redis()
