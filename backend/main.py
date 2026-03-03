import os
import sys
import time

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
