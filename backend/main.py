import os
import re
import sys
import time
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env"))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from ai_helper import get_top_monsters_by_exp, ask_ai_hybrid, detect_intent
from chat_logger import log_chat, get_logs as get_chat_logs
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

# Serve static frontend files (CSS, JS)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


def get_db():
    return sqlite3.connect(DB_PATH)


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
    question: str


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
    """Fetch live streams from YouTube for tracked channels."""
    if not YOUTUBE_API_KEY or not YOUTUBE_CHANNELS:
        return []

    streams = []
    with httpx.Client(timeout=10) as client:
        for entry in YOUTUBE_CHANNELS:
            # Format: "channelId:handle" or just "channelId"
            parts = entry.split(":", 1)
            channel_id = parts[0]
            handle = parts[1] if len(parts) > 1 else channel_id

            resp = client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "channelId": channel_id,
                    "type": "video",
                    "eventType": "live",
                    "key": YOUTUBE_API_KEY,
                },
            )
            data = resp.json()

            for item in data.get("items", []):
                video_id = item["id"].get("videoId", "")
                snippet = item.get("snippet", {})
                streams.append({
                    "id": video_id,
                    "title": snippet.get("title", "Live Stream"),
                    "viewers": 0,  # search API doesn't return viewer count
                    "streamer": snippet.get("channelTitle", handle),
                    "user_login": handle,
                    "platform": "youtube",
                    "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                    "game": "",
                    "video_id": video_id,
                    "channel_url": f"https://www.youtube.com/channel/{channel_id}",
                })

        # Fetch concurrent viewer counts for live videos
        video_ids = [s["video_id"] for s in streams if s.get("video_id")]
        if video_ids:
            resp = client.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={
                    "part": "liveStreamingDetails",
                    "id": ",".join(video_ids),
                    "key": YOUTUBE_API_KEY,
                },
            )
            vdata = resp.json()
            viewers_map = {}
            for v in vdata.get("items", []):
                details = v.get("liveStreamingDetails", {})
                viewers_map[v["id"]] = int(details.get("concurrentViewers", 0))
            for s in streams:
                s["viewers"] = viewers_map.get(s.get("video_id", ""), 0)

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


def _fetch_youtube_channel_stats() -> list:
    """Fetch channel-level statistics for all YOUTUBE_CHANNELS."""
    if not YOUTUBE_API_KEY or not YOUTUBE_CHANNELS:
        return []

    results = []
    with httpx.Client(timeout=10) as client:
        for entry in YOUTUBE_CHANNELS:
            parts = entry.split(":", 1)
            channel_id = parts[0]
            handle = parts[1] if len(parts) > 1 else channel_id

            resp = client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={
                    "part": "snippet,statistics",
                    "id": channel_id,
                    "key": YOUTUBE_API_KEY,
                },
            )
            data = resp.json()
            if resp.status_code != 200:
                print(f"[leaderboard] YouTube API error {resp.status_code}: {data}")
            items = data.get("items", [])
            if not items:
                continue

            item = items[0]
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})

            results.append({
                "login": handle,
                "name": snippet.get("title", handle),
                "avatar_url": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "channel_url": f"https://www.youtube.com/channel/{channel_id}",
                "platform": "youtube",
                "streams": None,
                "total_hours": None,
                "total_views": int(stats.get("viewCount", 0)),
                "subscriber_count": int(stats.get("subscriberCount", 0)),
                "data_source": "youtube_channel_stats",
            })

    return results


@app.get("/api/debug-yt")
def debug_yt():
    """Temporary debug endpoint to check YouTube config on Railway."""
    result = {
        "youtube_api_key_set": bool(YOUTUBE_API_KEY),
        "youtube_api_key_length": len(YOUTUBE_API_KEY),
        "youtube_channels_raw": os.getenv("YOUTUBE_CHANNELS", ""),
        "youtube_channels_parsed": YOUTUBE_CHANNELS,
        "youtube_channels_count": len(YOUTUBE_CHANNELS),
    }
    # Try actual API call
    if YOUTUBE_API_KEY and YOUTUBE_CHANNELS:
        try:
            parts = YOUTUBE_CHANNELS[0].split(":", 1)
            channel_id = parts[0]
            resp = httpx.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={"part": "snippet,statistics", "id": channel_id, "key": YOUTUBE_API_KEY},
                timeout=10,
            )
            result["api_status"] = resp.status_code
            result["api_response"] = resp.json()
        except Exception as e:
            result["api_error"] = str(e)
    return result


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
        entries.extend(_fetch_youtube_channel_stats())
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
