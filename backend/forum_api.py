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
    get_user_post_count, get_user_rank_title, get_user_profile,
    get_forum_db, search_threads,
    get_unread_count, get_notifications, mark_notifications_read,
    get_weekly_forum_mvps, get_weekly_best_thread,
)

forum_router = APIRouter(prefix="/api/forum", tags=["forum"])

# ── User rank cache (in-memory, refreshed per request batch) ──
_rank_cache: dict = {}  # user_id -> {"post_count": int, "rank_title": str}
_rank_cache_expires: float = 0


def _get_rank_info(user_id: int) -> dict:
    """Get cached rank info for a user."""
    global _rank_cache, _rank_cache_expires
    now = time.time()
    if now > _rank_cache_expires:
        _rank_cache = {}
        _rank_cache_expires = now + 300  # 5 min cache

    if user_id not in _rank_cache:
        count = get_user_post_count(user_id)
        _rank_cache[user_id] = {"post_count": count, "rank_title": get_user_rank_title(count)}
    return _rank_cache[user_id]


def _enrich_with_rank(items: list[dict], user_id_key: str = "user_id") -> list[dict]:
    """Add rank_title and post_count to a list of thread/reply dicts."""
    for item in items:
        info = _get_rank_info(item[user_id_key])
        item["author_rank"] = info["rank_title"]
        item["author_post_count"] = info["post_count"]
    return items

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
    # Add rank info to OP
    info = _get_rank_info(thread["user_id"])
    thread["author_rank"] = info["rank_title"]
    thread["author_post_count"] = info["post_count"]
    # Add rank info to replies
    replies = list_replies(thread_id, page=max(1, page))
    _enrich_with_rank(replies["items"])
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


# ── Search endpoint ──

@forum_router.get("/search")
def api_search(q: str = "", page: int = 1):
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    return search_threads(q.strip(), page=max(1, page))


# ── Profile endpoint ──

@forum_router.get("/users/{user_id}")
def api_user_profile(user_id: int):
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    # Remove sensitive fields
    profile.pop("google_id", None)
    profile.pop("email", None)
    return profile


@forum_router.get("/users/{user_id}/threads")
def api_user_threads(user_id: int, page: int = 1):
    """Get threads created by a user."""
    per_page = 20
    offset = (max(1, page) - 1) * per_page
    conn = get_forum_db()
    total = conn.execute("SELECT COUNT(*) FROM threads WHERE user_id = ?", (user_id,)).fetchone()[0]
    rows = conn.execute("""
        SELECT t.*, u.display_name as author_name, u.avatar_url as author_avatar,
               c.slug as category_slug, c.name as category_name
        FROM threads t
        JOIN users u ON u.id = t.user_id
        JOIN categories c ON c.id = t.category_id
        WHERE t.user_id = ?
        ORDER BY t.created_at DESC
        LIMIT ? OFFSET ?
    """, (user_id, per_page, offset)).fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows], "page": page, "per_page": per_page, "total": total}


@forum_router.get("/users/{user_id}/replies")
def api_user_replies(user_id: int, page: int = 1):
    """Get replies by a user."""
    per_page = 20
    offset = (max(1, page) - 1) * per_page
    conn = get_forum_db()
    total = conn.execute("SELECT COUNT(*) FROM replies WHERE user_id = ?", (user_id,)).fetchone()[0]
    rows = conn.execute("""
        SELECT r.*, u.display_name as author_name, u.avatar_url as author_avatar,
               t.title as thread_title, t.id as thread_id
        FROM replies r
        JOIN users u ON u.id = r.user_id
        JOIN threads t ON t.id = r.thread_id
        WHERE r.user_id = ?
        ORDER BY r.created_at DESC
        LIMIT ? OFFSET ?
    """, (user_id, per_page, offset)).fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows], "page": page, "per_page": per_page, "total": total}


# ── Notification endpoints ──

@forum_router.get("/notifications/count")
def api_notification_count(request: Request):
    user = get_current_user(request)
    if not user:
        return {"count": 0}
    return {"count": get_unread_count(user["id"])}


@forum_router.get("/notifications")
def api_notifications(request: Request, page: int = 1):
    user = require_auth(request)
    return get_notifications(user["id"], page=max(1, page))


@forum_router.post("/notifications/read")
def api_mark_read(request: Request):
    user = require_auth(request)
    mark_notifications_read(user["id"])
    return {"ok": True}


# ── MVP Board endpoint ──

_mvp_cache: dict = {"data": None, "expires": 0}


@forum_router.get("/mvp-board")
def api_mvp_board():
    """Weekly MVP board — top contributors and best thread."""
    now = time.time()
    if _mvp_cache["data"] is not None and now < _mvp_cache["expires"]:
        return _mvp_cache["data"]

    from datetime import datetime, timezone, timedelta
    today = datetime.now(timezone.utc)
    monday = today - timedelta(days=today.weekday())
    week_start = monday.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d")

    result = {
        "week_start": week_start,
        "forum_mvps": get_weekly_forum_mvps(5),
        "best_thread": get_weekly_best_thread(),
    }

    _mvp_cache["data"] = result
    _mvp_cache["expires"] = now + 900  # 15 min cache
    return result
