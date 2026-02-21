import os
import sqlite3
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DB_PATH = os.path.join(BASE_DIR, "logs.db")

_UNANSWERED_PATTERNS = [
    "i didn't understand that",
    "not found",
    "no results found",
    "no monsters found",
    "no farmable",
    "no items found dropping",
    "no known spawn",
    "not sold by any npc",
    "please specify two items",
    "no maps found",
    "no valid filters",
    "no item data found",
    "no monster drops found",
    "skill not found",
    "no skills found",
    "no data found for",
    "headgear quest not found",
    "no headgear quest found",
]


def _get_log_db():
    conn = sqlite3.connect(LOG_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_log_db():
    conn = _get_log_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            question TEXT NOT NULL,
            intent TEXT,
            answer TEXT NOT NULL,
            is_unanswered INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def _is_unanswered(answer: str) -> bool:
    lower = answer.lower()
    return any(p in lower for p in _UNANSWERED_PATTERNS)


def log_chat(question: str, intent: str, answer: str):
    conn = _get_log_db()
    conn.execute(
        """
        INSERT INTO chat_logs (timestamp, question, intent, answer, is_unanswered)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            question,
            intent,
            answer,
            1 if _is_unanswered(answer) else 0,
        ),
    )
    conn.commit()
    conn.close()


def get_logs(unanswered_only: bool = True, limit: int = 100):
    conn = _get_log_db()

    query = "SELECT id, timestamp, question, intent, answer, is_unanswered FROM chat_logs"
    if unanswered_only:
        query += " WHERE is_unanswered = 1"
    query += " ORDER BY id DESC LIMIT ?"

    rows = conn.execute(query, (limit,)).fetchall()
    conn.close()

    return [dict(row) for row in rows]


# Auto-init on import
init_log_db()
