import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.redis_pubsub import EVENT_CHANNEL


client = TestClient(app)


def test_websocket_events_connect_receives_messages_and_disconnects():
    """Verify WebSocket client connects, receives Pub/Sub messages decoded, and cleans up on disconnect."""
    mock_subscriber = AsyncMock()
    mock_messages = [
        {"type": "subscribe", "data": 1},  # subscribe acknowledgement message
        {
            "type": "message",
            "data": json.dumps({"type": "event.created", "event_id": "EVT_001", "event_type": "trespassing"}),
        },
        {
            "type": "message",
            "data": json.dumps({"type": "alert.created", "alert_id": 10, "priority": "HIGH"}),
        },
    ]

    async def mock_listen():
        for msg in mock_messages:
            yield msg

    mock_subscriber.listen = mock_listen

    with patch("backend.app.api.v1.endpoints.websocket.get_subscriber", new_callable=AsyncMock) as mock_get_sub, \
         patch("backend.app.api.v1.endpoints.websocket.close_subscriber", new_callable=AsyncMock) as mock_close_sub:

        mock_get_sub.return_value = mock_subscriber

        with client.websocket_connect("/api/v1/ws/events") as websocket:
            mock_get_sub.assert_awaited_once_with(EVENT_CHANNEL)

            msg1 = websocket.receive_json()
            assert msg1 == {"type": "event.created", "event_id": "EVT_001", "event_type": "trespassing"}

            msg2 = websocket.receive_json()
            assert msg2 == {"type": "alert.created", "alert_id": 10, "priority": "HIGH"}

        # Exiting context manager disconnects the websocket
        mock_close_sub.assert_awaited_once_with(mock_subscriber, EVENT_CHANNEL)


def test_websocket_events_handles_subscriber_error_cleanly():
    """Verify WebSocket handles get_subscriber failure gracefully without crashing the app."""
    with patch("backend.app.api.v1.endpoints.websocket.get_subscriber", new_callable=AsyncMock) as mock_get_sub, \
         patch("backend.app.api.v1.endpoints.websocket.close_subscriber", new_callable=AsyncMock) as mock_close_sub:

        mock_get_sub.side_effect = Exception("Redis connection failed")

        with client.websocket_connect("/api/v1/ws/events") as websocket:
            pass

        mock_get_sub.assert_awaited_once_with(EVENT_CHANNEL)
        mock_close_sub.assert_not_called()


def test_websocket_events_handles_close_error_cleanly():
    """Verify errors when closing subscriber do not raise uncaught exceptions."""
    mock_subscriber = AsyncMock()

    async def mock_listen():
        if False:
            yield {}

    mock_subscriber.listen = mock_listen

    with patch("backend.app.api.v1.endpoints.websocket.get_subscriber", new_callable=AsyncMock) as mock_get_sub, \
         patch("backend.app.api.v1.endpoints.websocket.close_subscriber", new_callable=AsyncMock) as mock_close_sub:

        mock_get_sub.return_value = mock_subscriber
        mock_close_sub.side_effect = Exception("Error during subscriber close")

        with client.websocket_connect("/api/v1/ws/events") as websocket:
            pass

        mock_close_sub.assert_awaited_once_with(mock_subscriber, EVENT_CHANNEL)
