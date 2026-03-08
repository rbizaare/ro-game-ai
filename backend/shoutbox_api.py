"""Shoutbox API — real-time lightweight chat for the homepage."""

import asyncio
import json
import time
from fastapi import APIRouter, Request, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from auth import get_current_user, require_auth
from forum_db import (
    get_recent_shoutbox_messages, create_shoutbox_message,
    is_banned, get_user_rank_title, get_user_post_count,
)

shoutbox_router = APIRouter(prefix="/api/shoutbox", tags=["shoutbox"])

# ── Rate limiting ──
_rate_limits: dict = {}


def _check_rate(user_id: int, max_per_min: int = 10):
    key = f"shoutbox:{user_id}"
    now = time.time()
    window = [t for t in _rate_limits.get(key, []) if now - t < 60]
    if len(window) >= max_per_min:
        raise HTTPException(status_code=429, detail="Slow down! Max 10 messages per minute.")
    window.append(now)
    _rate_limits[key] = window


# ── WebSocket connections ──
_ws_clients: set[WebSocket] = set()


async def broadcast_message(msg: dict):
    """Send a message to all connected WebSocket clients."""
    data = json.dumps(msg)
    dead = set()
    for ws in _ws_clients:
        try:
            await ws.send_text(data)
        except Exception:
            dead.add(ws)
    _ws_clients.difference_update(dead)


# ── REST endpoints ──

@shoutbox_router.get("/messages")
def api_get_messages():
    """Get recent shoutbox messages (public)."""
    messages = get_recent_shoutbox_messages(50)
    # Enrich with rank
    for msg in messages:
        count = get_user_post_count(msg["user_id"])
        msg["rank_title"] = get_user_rank_title(count)
    return {"messages": messages}


@shoutbox_router.post("/messages")
async def api_post_message(request: Request):
    """Post a new shoutbox message (requires auth)."""
    user = require_auth(request)
    if is_banned(user["id"]):
        raise HTTPException(status_code=403, detail="You are banned.")

    _check_rate(user["id"])

    body = await request.json()
    text = body.get("message", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    if len(text) > 200:
        raise HTTPException(status_code=400, detail="Message too long (200 chars max).")

    msg = create_shoutbox_message(user["id"], text)
    # Add rank info
    count = get_user_post_count(user["id"])
    msg["rank_title"] = get_user_rank_title(count)

    # Broadcast to WebSocket clients
    await broadcast_message(msg)

    return msg


# ── WebSocket endpoint ──

async def shoutbox_ws(websocket: WebSocket):
    """WebSocket endpoint for real-time shoutbox updates."""
    await websocket.accept()
    _ws_clients.add(websocket)
    try:
        while True:
            # Keep connection alive; ignore any client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _ws_clients.discard(websocket)
