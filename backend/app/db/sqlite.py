from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any


_INIT_LOCK = Lock()


def _connect(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with _INIT_LOCK:
        connection = _connect(path)
        try:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    payload_json TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                );
                """
            )
            connection.commit()
        finally:
            connection.close()


def upsert_session(db_path: str | Path, session_id: str) -> None:
    connection = _connect(db_path)
    try:
        connection.execute(
            """
            INSERT INTO sessions (id, created_at, updated_at)
            VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
            """,
            (session_id,),
        )
        connection.commit()
    finally:
        connection.close()


def insert_message(
    db_path: str | Path,
    *,
    session_id: str,
    role: str,
    content: str,
    payload: dict[str, Any] | None = None,
) -> None:
    connection = _connect(db_path)
    try:
        connection.execute(
            """
            INSERT INTO messages (session_id, role, content, payload_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                content,
                json.dumps(payload) if payload is not None else None,
            ),
        )
        connection.commit()
    finally:
        connection.close()

