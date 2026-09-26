import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.core.redis_pubsub import get_subscriber, close_subscriber, EVENT_CHANNEL

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket endpoint forwarding realtime Redis Pub/Sub events to clients."""
    await websocket.accept()
    subscriber = None
    try:
        subscriber = await get_subscriber(EVENT_CHANNEL)
        async for message in subscriber.listen():
            if message and message.get("type") == "message":
                data = message.get("data")
                if isinstance(data, (str, bytes)):
                    try:
                        payload = json.loads(data)
                    except (json.JSONDecodeError, TypeError):
                        payload = {"raw": data if isinstance(data, str) else data.decode("utf-8", errors="replace")}
                elif isinstance(data, dict):
                    payload = data
                else:
                    payload = {"data": str(data)}
                await websocket.send_json(payload)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally")
    except Exception as exc:
        logger.exception("Error in WebSocket event streaming: %s", exc)
    finally:
        if subscriber is not None:
            try:
                await close_subscriber(subscriber, EVENT_CHANNEL)
            except Exception as exc:
                logger.exception("Error closing Redis subscriber: %s", exc)
