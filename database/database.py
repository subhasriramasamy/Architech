"""
database.py
-------------
SQLite persistence layer for ScamCheck's Analysis History page.

Stores one row per completed analysis: timestamp, company/opportunity
label, score, risk level, and a JSON-encoded list of the major indicators
so the history page can reconstruct a summary without re-running analysis.
"""

import sqlite3
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scamcheck.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create app tables if they do not already exist."""
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                opportunity_label TEXT,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                indicators TEXT,
                source TEXT,
                raw_text TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def register_user(username: str, email: str, password: str) -> Dict[str, object]:
    """Create a new user account and return a status payload."""
    username = (username or "").strip()
    email = (email or "").strip().lower()
    password = password or ""

    if not username or not email or not password:
        return {"success": False, "message": "Username, email, and password are required."}
    if len(password) < 6:
        return {"success": False, "message": "Password must be at least 6 characters long."}

    import hashlib

    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    conn = get_connection()
    try:
        try:
            conn.execute(
                "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, datetime('now'))",
                (username, email, password_hash),
            )
            conn.commit()
            return {"success": True, "message": "Account created successfully."}
        except sqlite3.IntegrityError:
            return {"success": False, "message": "A user with that username or email already exists."}
    finally:
        conn.close()


def authenticate_user(username_or_email: str, password: str) -> Optional[Dict[str, str]]:
    """Validate credentials and return the logged-in user info."""
    username_or_email = (username_or_email or "").strip()
    password = password or ""
    if not username_or_email or not password:
        return None

    import hashlib

    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT username, email FROM users
            WHERE (username = ? OR email = ?) AND password_hash = ?
            LIMIT 1
            """,
            (username_or_email, username_or_email.lower(), password_hash),
        ).fetchone()
        if row is None:
            return None
        return {"username": row["username"], "email": row["email"]}
    finally:
        conn.close()


def save_analysis(opportunity_label: str, risk_score: int, risk_level: str,
                   indicators: List[str], source: str = "text",
                   raw_text: str = "") -> int:
    """Insert a completed analysis and return its new row id."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO analyses
                (timestamp, opportunity_label, risk_score, risk_level, indicators, source, raw_text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                opportunity_label or "Untitled Opportunity",
                risk_score,
                risk_level,
                json.dumps(indicators),
                source,
                raw_text,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def fetch_all_analyses() -> List[Dict]:
    """Return every stored analysis, most recent first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM analyses ORDER BY id DESC"
        ).fetchall()
        results = []
        for row in rows:
            record = dict(row)
            try:
                record["indicators"] = json.loads(record["indicators"] or "[]")
            except (json.JSONDecodeError, TypeError):
                record["indicators"] = []
            results.append(record)
        return results
    finally:
        conn.close()


def fetch_analysis_by_id(analysis_id: int) -> Optional[Dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
        ).fetchone()
        if row is None:
            return None
        record = dict(row)
        try:
            record["indicators"] = json.loads(record["indicators"] or "[]")
        except (json.JSONDecodeError, TypeError):
            record["indicators"] = []
        return record
    finally:
        conn.close()


def clear_history() -> None:
    """Delete all stored analyses (used by an optional 'reset demo data' action)."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM analyses")
        conn.commit()
    finally:
        conn.close()
