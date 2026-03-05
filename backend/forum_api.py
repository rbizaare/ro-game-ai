"""Forum API endpoints — threads, replies, moderation."""

import time
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user, require_auth, require_admin
from forum_db import (
    list_categories, get_category_by_slug,
    list_threads, get_thread, create_thread, delete_thread, toggle_pin, toggle_lock,
    list_replies, create_reply, delete_reply,
    ban_user, unban_user, get_user_by_id,
)

forum_router = APIRouter(prefix="/api/forum", tags=["forum"])

# ── Rate limiting ──

_rate_limits: dict = {}


def _check_rate(user_id: int, action: str, max_per_min: int):
    key = f"{user_id}:{action}"
    now = time.time()
    window = [t for t in _rate_limits.get(key, []) if now - t < 60]
    if len(window) >= max_per_min:
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a moment.")
    window.append(now)
    _rate_limits[key] = window


# ── Request models ──

class CreateThreadRequest(BaseModel):
    category_slug: str = Field(..., min_length=1)
    title: str = Field(..., min_length=3, max_length=200)
    body: str = Field(..., min_length=1, max_length=10000)


class CreateReplyRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=10000)


class BanRequest(BaseModel):
    user_id: int
    reason: str = ""
    duration_days: int | None = None


# ── Category endpoints ──

@forum_router.get("/categories")
def api_categories():
    return list_categories()


@forum_router.get("/categories/{slug}/threads")
def api_category_threads(slug: str, page: int = 1):
    cat = get_category_by_slug(slug)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return {
        "category": cat,
        **list_threads(cat["id"], page=max(1, page)),
    }


# ── Thread endpoints ──

@forum_router.get("/threads/{thread_id}")
def api_get_thread(thread_id: int, page: int = 1):
    thread = get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    replies = list_replies(thread_id, page=max(1, page))
    return {"thread": thread, "replies": replies}


@forum_router.post("/threads")
def api_create_thread(req: CreateThreadRequest, request: Request):
    user = require_auth(request)
    _check_rate(user["id"], "thread", 5)

    cat = get_category_by_slug(req.category_slug)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    thread_id = create_thread(cat["id"], user["id"], req.title.strip(), req.body.strip())
    return {"id": thread_id}


@forum_router.delete("/threads/{thread_id}")
def api_delete_thread(thread_id: int, request: Request):
    require_admin(request)
    thread = get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    delete_thread(thread_id)
    return {"ok": True}


@forum_router.post("/threads/{thread_id}/pin")
def api_pin_thread(thread_id: int, request: Request):
    require_admin(request)
    thread = get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    pinned = toggle_pin(thread_id)
    return {"is_pinned": pinned}


@forum_router.post("/threads/{thread_id}/lock")
def api_lock_thread(thread_id: int, request: Request):
    require_admin(request)
    thread = get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    locked = toggle_lock(thread_id)
    return {"is_locked": locked}


# ── Reply endpoints ──

@forum_router.post("/threads/{thread_id}/replies")
def api_create_reply(thread_id: int, req: CreateReplyRequest, request: Request):
    user = require_auth(request)
    _check_rate(user["id"], "reply", 10)

    thread = get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    if thread["is_locked"]:
        raise HTTPException(status_code=403, detail="Thread is locked")

    reply_id = create_reply(thread_id, user["id"], req.body.strip())
    return {"id": reply_id}


@forum_router.delete("/replies/{reply_id}")
def api_delete_reply(reply_id: int, request: Request):
    require_admin(request)
    delete_reply(reply_id)
    return {"ok": True}


# ── Moderation endpoints ──

@forum_router.post("/bans")
def api_ban_user(req: BanRequest, request: Request):
    admin = require_admin(request)
    target = get_user_by_id(req.user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target["is_admin"]:
        raise HTTPException(status_code=400, detail="Cannot ban an admin")
    ban_user(req.user_id, admin["id"], req.reason, req.duration_days)
    return {"ok": True}


@forum_router.delete("/bans/{user_id}")
def api_unban_user(user_id: int, request: Request):
    require_admin(request)
    unban_user(user_id)
    return {"ok": True}
