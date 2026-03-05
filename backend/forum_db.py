"""Forum database module — schema, init, and CRUD helpers."""

import os
import sqlite3
import time
from datetime import datetime, timezone

FORUM_DB_PATH = os.path.join(os.path.dirname(__file__), "forum.db")

CATEGORIES = [
    ("streamer-reviews", "Streamer Reviews", "Reviews and discussions about RO PH streamers", 1),
    ("server-reviews", "Server Reviews", "Rate and review Ragnarok Online servers", 2),
    ("hot-topics", "Hot Topics", "Trending discussions in the RO PH community", 3),
    ("general", "General Discussion", "Anything goes - off-topic, introductions, and more", 4),
]


def get_forum_db() -> sqlite3.Connection:
    conn = sqlite3.connect(FORUM_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_forum_db():
    """Create tables and seed categories if they don't exist."""
    conn = get_forum_db()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_id TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            display_name TEXT NOT NULL,
            avatar_url TEXT DEFAULT '',
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            last_login TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS bans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            reason TEXT DEFAULT '',
            banned_by INTEGER NOT NULL REFERENCES users(id),
            banned_at TEXT NOT NULL,
            expires_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_bans_user ON bans(user_id);

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            sort_order INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL REFERENCES categories(id),
            user_id INTEGER NOT NULL REFERENCES users(id),
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_pinned INTEGER NOT NULL DEFAULT 0,
            is_locked INTEGER NOT NULL DEFAULT 0,
            reply_count INTEGER NOT NULL DEFAULT 0,
            last_reply_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_threads_category ON threads(category_id);
        CREATE INDEX IF NOT EXISTS idx_threads_user ON threads(user_id);

        CREATE TABLE IF NOT EXISTS replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id INTEGER NOT NULL REFERENCES threads(id),
            user_id INTEGER NOT NULL REFERENCES users(id),
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_replies_thread ON replies(thread_id);
    """)

    # Seed categories
    for slug, name, desc, order in CATEGORIES:
        cur.execute(
            "INSERT OR IGNORE INTO categories (slug, name, description, sort_order) VALUES (?, ?, ?, ?)",
            (slug, name, desc, order),
        )

    conn.commit()
    conn.close()


# ── User helpers ──

def upsert_user(google_id: str, email: str, display_name: str, avatar_url: str, admin_emails: list[str]) -> dict:
    """Insert or update a user from Google OAuth. Returns user dict."""
    conn = get_forum_db()
    now = datetime.now(timezone.utc).isoformat()
    is_admin = 1 if email.lower() in [e.lower() for e in admin_emails] else 0

    conn.execute(
        """INSERT INTO users (google_id, email, display_name, avatar_url, is_admin, created_at, last_login)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(google_id) DO UPDATE SET
               display_name = excluded.display_name,
               avatar_url = excluded.avatar_url,
               last_login = excluded.last_login,
               is_admin = MAX(users.is_admin, excluded.is_admin)""",
        (google_id, email, display_name, avatar_url, is_admin, now, now),
    )
    conn.commit()

    user = conn.execute("SELECT * FROM users WHERE google_id = ?", (google_id,)).fetchone()
    conn.close()
    return dict(user)


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_forum_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def is_banned(user_id: int) -> bool:
    conn = get_forum_db()
    now = datetime.now(timezone.utc).isoformat()
    row = conn.execute(
        "SELECT id FROM bans WHERE user_id = ? AND (expires_at IS NULL OR expires_at > ?)",
        (user_id, now),
    ).fetchone()
    conn.close()
    return row is not None


# ── Category helpers ──

def list_categories() -> list[dict]:
    conn = get_forum_db()
    rows = conn.execute("""
        SELECT c.*, COUNT(t.id) as thread_count,
               MAX(COALESCE(t.last_reply_at, t.created_at)) as latest_activity
        FROM categories c
        LEFT JOIN threads t ON t.category_id = c.id
        GROUP BY c.id
        ORDER BY c.sort_order
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_category_by_slug(slug: str) -> dict | None:
    conn = get_forum_db()
    row = conn.execute("SELECT * FROM categories WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Thread helpers ──

def list_threads(category_id: int, page: int = 1, per_page: int = 20) -> dict:
    conn = get_forum_db()
    offset = (page - 1) * per_page

    total = conn.execute(
        "SELECT COUNT(*) FROM threads WHERE category_id = ?", (category_id,)
    ).fetchone()[0]

    rows = conn.execute("""
        SELECT t.*, u.display_name as author_name, u.avatar_url as author_avatar
        FROM threads t
        JOIN users u ON u.id = t.user_id
        WHERE t.category_id = ?
        ORDER BY t.is_pinned DESC, COALESCE(t.last_reply_at, t.created_at) DESC
        LIMIT ? OFFSET ?
    """, (category_id, per_page, offset)).fetchall()
    conn.close()

    return {"items": [dict(r) for r in rows], "page": page, "per_page": per_page, "total": total}


def get_thread(thread_id: int) -> dict | None:
    conn = get_forum_db()
    row = conn.execute("""
        SELECT t.*, u.display_name as author_name, u.avatar_url as author_avatar,
               c.slug as category_slug, c.name as category_name
        FROM threads t
        JOIN users u ON u.id = t.user_id
        JOIN categories c ON c.id = t.category_id
        WHERE t.id = ?
    """, (thread_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_thread(category_id: int, user_id: int, title: str, body: str) -> int:
    conn = get_forum_db()
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO threads (category_id, user_id, title, body, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (category_id, user_id, title, body, now, now),
    )
    conn.commit()
    thread_id = cur.lastrowid
    conn.close()
    return thread_id


def delete_thread(thread_id: int):
    conn = get_forum_db()
    conn.execute("DELETE FROM replies WHERE thread_id = ?", (thread_id,))
    conn.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
    conn.commit()
    conn.close()


def toggle_pin(thread_id: int) -> bool:
    conn = get_forum_db()
    conn.execute("UPDATE threads SET is_pinned = 1 - is_pinned WHERE id = ?", (thread_id,))
    conn.commit()
    row = conn.execute("SELECT is_pinned FROM threads WHERE id = ?", (thread_id,)).fetchone()
    conn.close()
    return bool(row["is_pinned"]) if row else False


def toggle_lock(thread_id: int) -> bool:
    conn = get_forum_db()
    conn.execute("UPDATE threads SET is_locked = 1 - is_locked WHERE id = ?", (thread_id,))
    conn.commit()
    row = conn.execute("SELECT is_locked FROM threads WHERE id = ?", (thread_id,)).fetchone()
    conn.close()
    return bool(row["is_locked"]) if row else False


# ── Reply helpers ──

def list_replies(thread_id: int, page: int = 1, per_page: int = 50) -> dict:
    conn = get_forum_db()
    offset = (page - 1) * per_page

    total = conn.execute(
        "SELECT COUNT(*) FROM replies WHERE thread_id = ?", (thread_id,)
    ).fetchone()[0]

    rows = conn.execute("""
        SELECT r.*, u.display_name as author_name, u.avatar_url as author_avatar
        FROM replies r
        JOIN users u ON u.id = r.user_id
        WHERE r.thread_id = ?
        ORDER BY r.created_at ASC
        LIMIT ? OFFSET ?
    """, (thread_id, per_page, offset)).fetchall()
    conn.close()

    return {"items": [dict(r) for r in rows], "page": page, "per_page": per_page, "total": total}


def create_reply(thread_id: int, user_id: int, body: str) -> int:
    conn = get_forum_db()
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO replies (thread_id, user_id, body, created_at) VALUES (?, ?, ?, ?)",
        (thread_id, user_id, body, now),
    )
    # Update denormalized fields on thread
    conn.execute(
        "UPDATE threads SET reply_count = reply_count + 1, last_reply_at = ?, updated_at = ? WHERE id = ?",
        (now, now, thread_id),
    )
    conn.commit()
    reply_id = cur.lastrowid
    conn.close()
    return reply_id


def delete_reply(reply_id: int):
    conn = get_forum_db()
    row = conn.execute("SELECT thread_id FROM replies WHERE id = ?", (reply_id,)).fetchone()
    if row:
        conn.execute("DELETE FROM replies WHERE id = ?", (reply_id,))
        conn.execute(
            "UPDATE threads SET reply_count = MAX(0, reply_count - 1) WHERE id = ?",
            (row["thread_id"],),
        )
        conn.commit()
    conn.close()


# ── Ban helpers ──

def ban_user(user_id: int, banned_by: int, reason: str = "", duration_days: int | None = None):
    conn = get_forum_db()
    now = datetime.now(timezone.utc)
    expires = None
    if duration_days:
        from datetime import timedelta
        expires = (now + timedelta(days=duration_days)).isoformat()
    conn.execute(
        "INSERT INTO bans (user_id, banned_by, reason, banned_at, expires_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, banned_by, reason, now.isoformat(), expires),
    )
    conn.commit()
    conn.close()


def unban_user(user_id: int):
    conn = get_forum_db()
    conn.execute("DELETE FROM bans WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
