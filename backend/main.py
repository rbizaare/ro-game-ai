import html as html_mod
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env"))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field
from ai_helper import get_top_monsters_by_exp, ask_ai_hybrid, detect_intent
from chat_logger import log_chat, get_logs as get_chat_logs
from auth import auth_router
from forum_api import forum_router
from shoutbox_api import shoutbox_router, shoutbox_ws
from forum_db import init_forum_db
import httpx
import sqlite3
DB_PATH = os.path.join(BASE_DIR, "game.db")

# Twitch API config
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "")
TWITCH_STREAMERS = [s.strip() for s in os.getenv("TWITCH_STREAMERS", "").split(",") if s.strip()]

# YouTube API config
# YOUTUBE_CHANNELS format: "channelId:handle,channelId:handle,..."
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
YOUTUBE_CHANNELS = [s.strip() for s in os.getenv("YOUTUBE_CHANNELS", "").split(",") if s.strip()]

# Cache for Twitch app token and live stream data
_twitch_token: dict = {"token": "", "expires": 0}
_live_cache: dict = {"data": None, "expires": 0}
_leaderboard_cache: dict = {"data": None, "month": "", "expires": 0}

app = FastAPI()


from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# Initialize forum database
init_forum_db()

# Include forum and auth routers
app.include_router(auth_router)
app.include_router(forum_router)
app.include_router(shoutbox_router)
app.add_api_websocket_route("/ws/shoutbox", shoutbox_ws)

# Serve static frontend files (CSS, JS)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


def get_db():
    return sqlite3.connect(DB_PATH)


# ── Health check ──
@app.get("/health")
def health_check():
    return {"status": "ok"}


# ── robots.txt ──
_ROBOTS_TXT = """User-agent: *
Allow: /
Disallow: /api/
Disallow: /auth/
Disallow: /logs
Sitemap: /sitemap.txt
"""

@app.get("/robots.txt")
def robots_txt():
    return PlainTextResponse(_ROBOTS_TXT)


# ── Sitemap ──
_SITEMAP_TXT = """/
/chat
/streamers
/servers
/forum
/privacy
"""

@app.get("/sitemap.txt")
def sitemap_txt():
    return PlainTextResponse(_SITEMAP_TXT, media_type="text/plain")


@app.get("/")
def root():
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))


@app.get("/chat")
def chat_page():
    return FileResponse(os.path.join(BASE_DIR, "static", "chat.html"))


@app.get("/streamers")
def streamers_page():
    return FileResponse(os.path.join(BASE_DIR, "static", "streamers-page.html"))


@app.get("/servers")
def servers_page():
    return FileResponse(os.path.join(BASE_DIR, "static", "servers-page.html"))


@app.get("/privacy")
def privacy_page():
    return FileResponse(os.path.join(BASE_DIR, "static", "privacy.html"))


@app.get("/forum")
def forum_page():
    return FileResponse(os.path.join(BASE_DIR, "static", "forum.html"))


@app.get("/forum/thread/{thread_id}")
def thread_page(thread_id: int):
    from forum_db import get_thread
    thread = get_thread(thread_id)

    template_path = os.path.join(BASE_DIR, "static", "thread.html")
    if not thread:
        return FileResponse(template_path)

    # Build dynamic OG tags (escape all user content)
    title = html_mod.escape(thread["title"])
    author = html_mod.escape(thread.get("author_name", ""))
    body_preview = html_mod.escape((thread["body"] or "")[:200])
    og_desc = f"by {author} — {body_preview}" if author else body_preview

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Replace generic meta tags with dynamic ones
    html = html.replace(
        "<title>Thread — RO PH Community Hub</title>",
        f"<title>{title} — RO PH Community Hub</title>",
    )
    html = html.replace(
        'content="Forum discussion on the RO PH Community Hub."',
        f'content="{og_desc}"',
    )
    html = html.replace(
        'content="Thread — RO PH Community Hub"',
        f'content="{title} — RO PH Community Hub"',
    )

    return HTMLResponse(html)


@app.get("/forum/profile/{user_id}")
def profile_page(user_id: int):
    return FileResponse(os.path.join(BASE_DIR, "static", "profile.html"))


@app.get("/monsters")
def list_monsters(limit: int = 10):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, level, race, element
        FROM monsters
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "name": r[1],
            "level": r[2],
            "race": r[3],
            "element": r[4]
        }
        for r in rows
    ]


@app.get("/search/race/{race}")
def search_by_race(race: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT name, level, race
        FROM monsters
        WHERE race = ?
        ORDER BY level DESC
        LIMIT 20
    """, (race,))

    rows = cur.fetchall()
    conn.close()

    return rows


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


@app.post("/chat")
def chat(req: ChatRequest):
    intent = detect_intent(req.question)
    answer = ask_ai_hybrid(req.question)
    log_chat(req.question, intent, answer)
    return {
        "question": req.question,
        "answer": answer
    }


@app.get("/logs")
def logs_page():
    return FileResponse(os.path.join(BASE_DIR, "static", "logs.html"))


@app.get("/api/logs")
def api_logs(unanswered_only: bool = True, limit: int = 100):
    return get_chat_logs(unanswered_only=unanswered_only, limit=limit)


def get_twitch_token():
    """Get or refresh Twitch App Access Token."""
    now = time.time()
    if _twitch_token["token"] and now < _twitch_token["expires"]:
        return _twitch_token["token"]

    resp = httpx.post(
        "https://id.twitch.tv/oauth2/token",
        data={
            "client_id": TWITCH_CLIENT_ID,
            "client_secret": TWITCH_CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
        timeout=10,
    )
    data = resp.json()
    _twitch_token["token"] = data["access_token"]
    _twitch_token["expires"] = now + data.get("expires_in", 3600) - 60
    return _twitch_token["token"]


def _fetch_twitch_streams() -> list:
    """Fetch live streams from Twitch for tracked streamers."""
    if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET or not TWITCH_STREAMERS:
        return []

    token = get_twitch_token()
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}",
    }

    streams = []
    with httpx.Client(timeout=10) as client:
        resp = client.get(
            "https://api.twitch.tv/helix/streams",
            params=[("user_login", name) for name in TWITCH_STREAMERS],
            headers=headers,
        )
        data = resp.json()

        for stream in data.get("data", []):
            streams.append({
                "id": stream["id"],
                "title": stream.get("title", "Live Stream"),
                "viewers": stream.get("viewer_count", 0),
                "streamer": stream["user_name"],
                "user_login": stream["user_login"],
                "platform": "twitch",
                "thumbnail": stream.get("thumbnail_url", "").replace("{width}", "440").replace("{height}", "248"),
                "game": stream.get("game_name", ""),
                "channel_url": f"https://www.twitch.tv/{stream['user_login']}",
            })
    return streams


def _fetch_youtube_streams() -> list:
    """Fetch currently-live YouTube streams using PlaylistItems + Videos API.

    Uses the channel's uploads playlist (UC->UU) to get recent video IDs,
    then Videos API to check which are currently live.
    """
    if not YOUTUBE_API_KEY or not YOUTUBE_CHANNELS:
        return []

    streams = []
    video_ids = []
    channel_map: dict = {}  # video_id -> (channel_id, handle)

    with httpx.Client(timeout=15) as client:
        # Step 1: Get recent video IDs via PlaylistItems API (uploads playlist)
        for entry in YOUTUBE_CHANNELS:
            parts = entry.split(":", 1)
            channel_id = parts[0]
            handle = parts[1] if len(parts) > 1 else channel_id
            uploads_playlist = channel_id.replace("UC", "UU", 1)

            try:
                pl_resp = client.get(
                    "https://www.googleapis.com/youtube/v3/playlistItems",
                    params={
                        "part": "snippet",
                        "playlistId": uploads_playlist,
                        "maxResults": 5,
                        "key": YOUTUBE_API_KEY,
                    },
                )
                if pl_resp.status_code != 200:
                    continue
                for item in pl_resp.json().get("items", []):
                    vid_id = item["snippet"]["resourceId"]["videoId"]
                    video_ids.append(vid_id)
                    channel_map[vid_id] = (channel_id, handle)
            except Exception:
                continue

        if not video_ids:
            return []

        # Step 2: Check which videos are live via Videos API (1 unit, batched)
        resp = client.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "part": "snippet,liveStreamingDetails",
                "id": ",".join(video_ids),
                "key": YOUTUBE_API_KEY,
            },
        )
        data = resp.json()

        for item in data.get("items", []):
            live_details = item.get("liveStreamingDetails", {})
            snippet = item.get("snippet", {})

            # Currently live: has actualStartTime but no actualEndTime
            if live_details.get("actualStartTime") and not live_details.get("actualEndTime"):
                video_id = item["id"]
                channel_id, handle = channel_map.get(video_id, ("", ""))
                viewers = int(live_details.get("concurrentViewers", 0))

                streams.append({
                    "id": video_id,
                    "title": snippet.get("title", "Live Stream"),
                    "viewers": viewers,
                    "streamer": snippet.get("channelTitle", handle),
                    "user_login": handle,
                    "platform": "youtube",
                    "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                    "game": "",
                    "video_id": video_id,
                    "channel_url": f"https://www.youtube.com/channel/{channel_id}",
                })

    return streams


def _parse_twitch_duration(duration: str) -> float:
    """Convert Twitch duration string '2h12m4s' to decimal hours."""
    h = int(m.group(1)) if (m := re.search(r'(\d+)h', duration)) else 0
    mi = int(m.group(1)) if (m := re.search(r'(\d+)m', duration)) else 0
    s = int(m.group(1)) if (m := re.search(r'(\d+)s', duration)) else 0
    return h + mi / 60 + s / 3600


def _fetch_twitch_vod_stats(started_after: str) -> list:
    """Fetch VOD archive stats for all TWITCH_STREAMERS since started_after (ISO8601)."""
    if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET or not TWITCH_STREAMERS:
        return []

    token = get_twitch_token()
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}",
    }

    results = []
    with httpx.Client(timeout=15) as client:
        # Batch-resolve user IDs
        resp = client.get(
            "https://api.twitch.tv/helix/users",
            params=[("login", name) for name in TWITCH_STREAMERS],
            headers=headers,
        )
        users = {u["login"].lower(): u for u in resp.json().get("data", [])}

        for login_lower, user in users.items():
            user_id = user["id"]
            total_streams = 0
            total_hours = 0.0
            total_views = 0
            cursor = None

            while True:
                params = {"user_id": user_id, "type": "archive", "first": 100}
                if cursor:
                    params["after"] = cursor

                vresp = client.get(
                    "https://api.twitch.tv/helix/videos",
                    params=params,
                    headers=headers,
                )
                vdata = vresp.json()
                videos = vdata.get("data", [])
                if not videos:
                    break

                hit_old = False
                for v in videos:
                    # VODs are newest-first; stop when older than cutoff
                    if v.get("created_at", "") < started_after:
                        hit_old = True
                        break
                    total_streams += 1
                    total_hours += _parse_twitch_duration(v.get("duration", "0s"))
                    total_views += v.get("view_count", 0)

                if hit_old:
                    break
                cursor = vdata.get("pagination", {}).get("cursor")
                if not cursor:
                    break

            results.append({
                "login": login_lower,
                "name": user["display_name"],
                "avatar_url": user.get("profile_image_url", ""),
                "channel_url": f"https://www.twitch.tv/{login_lower}",
                "platform": "twitch",
                "streams": total_streams,
                "total_hours": round(total_hours, 2),
                "total_views": total_views,
                "data_source": "twitch_vods",
            })

    return results


def _parse_yt_duration(duration: str) -> float:
    """Convert ISO 8601 duration 'PT2H12M4S' to decimal hours."""
    h = int(m.group(1)) if (m := re.search(r'(\d+)H', duration)) else 0
    mi = int(m.group(1)) if (m := re.search(r'(\d+)M', duration)) else 0
    s = int(m.group(1)) if (m := re.search(r'(\d+)S', duration)) else 0
    return h + mi / 60 + s / 3600


def _fetch_youtube_channel_stats(started_after: str) -> list:
    """Fetch monthly live stream stats for YouTube channels.

    Uses PlaylistItems API (uploads playlist) to get recent video IDs,
    then Videos API to get durations, view counts, and live stream details.
    Only counts actual live streams to keep it fair with Twitch.
    """
    if not YOUTUBE_API_KEY or not YOUTUBE_CHANNELS:
        print("[leaderboard] YouTube skipped: missing API key or channels config")
        return []

    results = []
    with httpx.Client(timeout=15) as client:
        for entry in YOUTUBE_CHANNELS:
            parts = entry.split(":", 1)
            channel_id = parts[0]
            handle = parts[1] if len(parts) > 1 else channel_id

            # Step 1: Channel info (snippet + statistics) — 1 unit
            ch_resp = client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={
                    "part": "snippet,statistics",
                    "id": channel_id,
                    "key": YOUTUBE_API_KEY,
                },
            )
            ch_data = ch_resp.json()
            if ch_resp.status_code != 200:
                print(f"[leaderboard] YouTube channels API error {ch_resp.status_code}: {ch_data}")
                continue
            ch_items = ch_data.get("items", [])
            if not ch_items:
                continue

            ch_item = ch_items[0]
            snippet = ch_item.get("snippet", {})
            ch_stats = ch_item.get("statistics", {})

            # Step 2: Uploads playlist for recent video IDs (UC -> UU)
            uploads_playlist = channel_id.replace("UC", "UU", 1)
            video_ids = []
            try:
                pl_resp = client.get(
                    "https://www.googleapis.com/youtube/v3/playlistItems",
                    params={
                        "part": "snippet",
                        "playlistId": uploads_playlist,
                        "maxResults": 25,
                        "key": YOUTUBE_API_KEY,
                    },
                )
                if pl_resp.status_code == 200:
                    for item in pl_resp.json().get("items", []):
                        video_ids.append(item["snippet"]["resourceId"]["videoId"])
            except Exception as e:
                print(f"[leaderboard] YouTube PlaylistItems error for {handle}: {e}")

            # Step 3: Videos API for durations + views (1 unit per batch of 50)
            streams = 0
            total_hours = 0.0
            total_views = 0
            if video_ids:
                vid_resp = client.get(
                    "https://www.googleapis.com/youtube/v3/videos",
                    params={
                        "part": "contentDetails,statistics,snippet,liveStreamingDetails",
                        "id": ",".join(video_ids),
                        "key": YOUTUBE_API_KEY,
                    },
                )
                vid_data = vid_resp.json()
                if vid_resp.status_code == 200:
                    for vid in vid_data.get("items", []):
                        # Only count actual live streams (not regular uploads/shorts)
                        if not vid.get("liveStreamingDetails", {}).get("actualStartTime"):
                            continue
                        published = vid.get("snippet", {}).get("publishedAt", "")
                        if published < started_after:
                            continue
                        duration = vid.get("contentDetails", {}).get("duration", "PT0S")
                        views = int(vid.get("statistics", {}).get("viewCount", 0))
                        streams += 1
                        total_hours += _parse_yt_duration(duration)
                        total_views += views
                else:
                    print(f"[leaderboard] YouTube videos API error {vid_resp.status_code}: {vid_data}")

            print(f"[leaderboard] YouTube {handle}: {len(video_ids)} videos, {streams} live streams, {round(total_hours, 1)}h")

            results.append({
                "login": handle,
                "name": snippet.get("title", handle),
                "avatar_url": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "channel_url": f"https://www.youtube.com/channel/{channel_id}",
                "platform": "youtube",
                "streams": streams if streams > 0 else None,
                "total_hours": round(total_hours, 1) if total_hours > 0 else None,
                "total_views": total_views,
                "subscriber_count": int(ch_stats.get("subscriberCount", 0)),
                "data_source": "youtube_vods" if streams > 0 else "youtube_channel_stats",
            })

    return results


@app.get("/api/leaderboard")
def api_leaderboard(month: str = ""):
    """Monthly streamer leaderboard. Optional ?month=YYYY-MM param."""
    now = time.time()

    if not month:
        today = datetime.now(timezone.utc)
        month = today.strftime("%Y-%m")

    # Validate format
    try:
        year, mon = month.split("-")
        year, mon = int(year), int(mon)
        if not (1 <= mon <= 12):
            raise ValueError
    except (ValueError, AttributeError):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM.")

    # Check cache
    if (
        _leaderboard_cache["data"] is not None
        and _leaderboard_cache.get("month") == month
        and now < _leaderboard_cache["expires"]
    ):
        return _leaderboard_cache["data"]

    started_after = f"{year:04d}-{mon:02d}-01T00:00:00Z"
    entries = []

    try:
        entries.extend(_fetch_twitch_vod_stats(started_after))
    except Exception as e:
        print(f"[leaderboard] Twitch VOD fetch error: {e}")

    try:
        entries.extend(_fetch_youtube_channel_stats(started_after))
    except Exception as e:
        print(f"[leaderboard] YouTube channel stats error: {e}")

    # Sort by total_hours descending (nulls last)
    entries.sort(key=lambda e: e.get("total_hours") if e.get("total_hours") is not None else -1, reverse=True)
    for i, entry in enumerate(entries):
        entry["rank"] = i + 1

    result = {
        "month": month,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entries": entries,
    }

    _leaderboard_cache["data"] = result
    _leaderboard_cache["month"] = month
    _leaderboard_cache["expires"] = now + 900  # 15 minutes

    return result


@app.get("/api/live-streams")
def api_live_streams():
    now = time.time()

    # Return cached data if still fresh
    if _live_cache["data"] is not None and now < _live_cache["expires"]:
        return _live_cache["data"]

    streams = []

    try:
        streams.extend(_fetch_twitch_streams())
    except Exception:
        pass  # Twitch unavailable, continue with YouTube

    try:
        streams.extend(_fetch_youtube_streams())
    except Exception:
        pass  # YouTube unavailable, continue

    # Sort by viewer count descending
    streams.sort(key=lambda s: s["viewers"], reverse=True)

    result = {"streams": streams}
    _live_cache["data"] = result
    _live_cache["expires"] = now + 60

    return result


@app.get("/farm/{item_name}")
def find_item_sources(item_name: str):
    conn = get_db()
    cur = conn.cursor()

    # Normalize input
    normalized = item_name.replace(" ", "_")

    # Step 1: Find correct AegisName
    cur.execute("""
        SELECT aegis_name, name
        FROM items
        WHERE name = ?
        OR aegis_name = ?
        LIMIT 1
    """, (item_name, normalized))

    item = cur.fetchone()

    if not item:
        conn.close()
        return {"error": "Item not found"}

    aegis_name = item[0]
    display_name = item[1]

    # Step 2: Find monsters that drop it
    cur.execute("""
        SELECT
            m.name,
            m.level,
            d.rate
        FROM drops d
        JOIN monsters m ON d.monster_id = m.id
        WHERE d.item_name = ?
        ORDER BY d.rate DESC
        LIMIT 20
    """, (aegis_name,))

    rows = cur.fetchall()
    conn.close()

    return {
        "item": display_name,
        "aegis_name": aegis_name,
        "sources": [
            {
                "monster": r[0],
                "level": r[1],
                "drop_rate": r[2]
            }
            for r in rows
        ]
    }


# ── 404 handler ──
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    # Return JSON for API routes, HTML page for everything else
    if request.url.path.startswith("/api/"):
        return PlainTextResponse("Not found", status_code=404)
    return FileResponse(os.path.join(BASE_DIR, "static", "404.html"), status_code=404)
