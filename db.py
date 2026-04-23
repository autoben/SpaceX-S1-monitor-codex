"""SQLite-backed notification deduplication."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime


SCHEMA = """
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    identifier TEXT NOT NULL UNIQUE,
    title TEXT,
    notified_at TEXT NOT NULL,
    content TEXT
);
"""


class NotificationStore:
    def __init__(self, path: str) -> None:
        self.path = path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _initialize(self) -> None:
        with closing(self._connect()) as conn:
            conn.execute(SCHEMA)
            conn.commit()

    def has_notified(self, identifier: str) -> bool:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT 1 FROM notifications WHERE identifier = ? LIMIT 1",
                (identifier,),
            ).fetchone()
            return row is not None

    def record_notification(
        self,
        *,
        source: str,
        identifier: str,
        title: str,
        notified_at: datetime,
        content: str,
    ) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                """
                INSERT INTO notifications
                    (source, identifier, title, notified_at, content)
                VALUES (?, ?, ?, ?, ?)
                """,
                (source, identifier, title, notified_at.isoformat(), content),
            )
            conn.commit()

    def count(self) -> int:
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT COUNT(*) FROM notifications").fetchone()
            return int(row[0])
