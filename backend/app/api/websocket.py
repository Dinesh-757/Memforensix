"""
WebSocket endpoint for real-time analysis progress updates.
Subscribes to a Redis pub/sub channel per analysis_id, populated by
the Celery worker, and relays messages to the connected browser.
"""
import asyncio
import json
import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/analysis/{analysis_id}")
async def analysis_progress_ws(websocket: WebSocket, analysis_id: str):
    await websocket.accept()
    redis_client = aioredis.from_url(settings.REDIS_URL)
    pubsub = redis_client.pubsub()
    channel = f"analysis:{analysis_id}"
    await pubsub.subscribe(channel)

    try:
        # Send an initial hello so the client knows the socket is live
        await websocket.send_json({"type": "connected", "analysis_id": analysis_id})

        listen_task = asyncio.create_task(_relay_messages(pubsub, websocket))
        # Keep connection open, listen for client disconnect / pings
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for analysis %s", analysis_id)
    finally:
        listen_task.cancel()
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await redis_client.close()


async def _relay_messages(pubsub, websocket: WebSocket):
    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            data = json.loads(message["data"])
            await websocket.send_json({"type": "progress", **data})
        except Exception as exc:
            logger.warning("Failed to relay ws message: %s", exc)
