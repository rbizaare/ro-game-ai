import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from ai_helper import get_top_monsters_by_exp, ask_ai_hybrid, detect_intent
from chat_logger import log_chat, get_logs as get_chat_logs
import sqlite3
DB_PATH = os.path.join(BASE_DIR, "game.db")

app = FastAPI()

# Serve static frontend files (CSS, JS)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


def get_db():
    return sqlite3.connect(DB_PATH)


@app.get("/")
def root():
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))


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
