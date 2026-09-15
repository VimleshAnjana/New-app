"""
database.py
Medicine Scanner app - local storage layer (SQLite).
Stores every scanned / manually added medicine entry.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Dict

DB_PATH = os.path.join(os.path.dirname(__file__), "medicine_scanner.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't already exist."""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            batch_no TEXT NOT NULL,
            expiry TEXT,
            strips INTEGER NOT NULL DEFAULT 1,
            per_strip INTEGER NOT NULL DEFAULT 1,
            source TEXT DEFAULT 'scan',      -- 'scan' or 'manual'
            created_at TEXT NOT NULL
        )
        """
    )
    # "Sent by" names - saved once, reusable from a dropdown every time after
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sender_names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """
    )
    conn.commit()
    conn.close()


def add_sender_name(name: str) -> None:
    """Save a new 'Sent by' name so it appears in the dropdown next time too."""
    name = name.strip()
    if not name:
        return
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO sender_names (name) VALUES (?)", (name,)
    )
    conn.commit()
    conn.close()


def get_sender_names() -> List[str]:
    conn = get_connection()
    rows = conn.execute("SELECT name FROM sender_names ORDER BY name").fetchall()
    conn.close()
    return [r["name"] for r in rows]


def add_medicine(name: str, batch_no: str, expiry: str,
                  strips: int, per_strip: int, source: str = "scan") -> int:
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO medicines (name, batch_no, expiry, strips, per_strip, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (name.strip(), batch_no.strip(), expiry, strips, per_strip, source,
         datetime.now().isoformat()),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_medicine(item_id: int, name: str, batch_no: str, expiry: str,
                     strips: int, per_strip: int) -> None:
    conn = get_connection()
    conn.execute(
        """
        UPDATE medicines
        SET name = ?, batch_no = ?, expiry = ?, strips = ?, per_strip = ?
        WHERE id = ?
        """,
        (name.strip(), batch_no.strip(), expiry, strips, per_strip, item_id),
    )
    conn.commit()
    conn.close()


def delete_medicine(item_id: int) -> None:
    """Delete a single wrongly-scanned / wrongly-added medicine entry."""
    conn = get_connection()
    conn.execute("DELETE FROM medicines WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def get_all_medicines(days: Optional[int] = 30) -> List[Dict]:
    """
    Return medicines added in the last `days` days (used for the
    home screen list and the Reports / PDF export, default 1 month).
    Pass days=None for the full history.
    """
    conn = get_connection()
    if days is None:
        rows = conn.execute(
            "SELECT * FROM medicines ORDER BY created_at DESC"
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT * FROM medicines
            WHERE created_at >= datetime('now', ?)
            ORDER BY created_at DESC
            """,
            (f"-{days} days",),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_medicine(item_id: int) -> Optional[Dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM medicines WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    return dict(row) if row else None
