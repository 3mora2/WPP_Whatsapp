"""Lazy, bounded SQLite event journal; cursors survive restart and retention."""

from __future__ import annotations

import json
import math
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional


class SQLiteEventStore:
    def __init__(self, path, namespace: str, capacity: int, retention: float):
        if type(capacity) is not int or capacity < 1:
            raise ValueError("Event capacity must be a positive integer")
        if type(retention) not in (int, float) or not math.isfinite(retention) or retention <= 0:
            raise ValueError("Event retention must be finite and positive")
        self.path, self.namespace = Path(path), namespace
        self.capacity, self.retention = capacity, retention
        self._lock = threading.RLock()
        self._connection: Optional[sqlite3.Connection] = None
        self._closed = False

    def _db(self) -> sqlite3.Connection:
        if self._closed:
            raise RuntimeError("Event store is closed")
        if self._connection is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(str(self.path), check_same_thread=False)
            self._connection.executescript("""
                CREATE TABLE IF NOT EXISTS event_cursors(namespace TEXT PRIMARY KEY, sequence INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS events(namespace TEXT NOT NULL, sequence INTEGER NOT NULL,
                    message_id TEXT, created REAL NOT NULL, payload TEXT NOT NULL,
                    PRIMARY KEY(namespace, sequence), UNIQUE(namespace,message_id));
                CREATE TABLE IF NOT EXISTS event_consumers(namespace TEXT NOT NULL, id TEXT NOT NULL,
                    cursor INTEGER NOT NULL DEFAULT 0, sequence INTEGER, token TEXT,
                    lease_until REAL NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0,
                    retry_at REAL NOT NULL DEFAULT 0, payload TEXT, max_attempts INTEGER NOT NULL,
                    lost INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY(namespace,id));
                CREATE TABLE IF NOT EXISTS event_dead_letters(namespace TEXT NOT NULL,
                    consumer TEXT NOT NULL, sequence INTEGER NOT NULL, attempts INTEGER NOT NULL,
                    category TEXT NOT NULL, payload TEXT NOT NULL, created REAL NOT NULL,
                    PRIMARY KEY(namespace,consumer,sequence));
            """)
        return self._connection

    def _sequence(self, db: sqlite3.Connection) -> int:
        row = db.execute(
            "SELECT sequence FROM event_cursors WHERE namespace=?", (self.namespace,)
        ).fetchone()
        return row[0] if row else 0

    @property
    def sequence(self) -> int:
        with self._lock:
            return self._sequence(self._db())

    def _prune(self, db: sqlite3.Connection, sequence: int) -> None:
        db.execute(
            "DELETE FROM events WHERE namespace=? AND (sequence<=? OR created<?)",
            (self.namespace, sequence - self.capacity, time.time() - self.retention),
        )

    def append(self, event: dict[str, Any]) -> None:
        with self._lock:
            db = self._db()
            # Cross-process writers reserve sequence and dedup atomically.
            db.execute("BEGIN IMMEDIATE")
            try:
                sequence = self._sequence(db)
                self._prune(db, sequence)
                ident = event["message"].get("id")
                ident = ident if isinstance(ident, str) and ident else None
                if (
                    ident is not None
                    and db.execute(
                        "SELECT 1 FROM events WHERE namespace=? AND message_id=?",
                        (self.namespace, ident),
                    ).fetchone()
                ):
                    db.commit()
                    return
                sequence += 1
                payload = {**event, "sequence": sequence}
                db.execute(
                    "INSERT INTO events VALUES(?,?,?,?,?)",
                    (
                        self.namespace,
                        sequence,
                        ident,
                        time.time(),
                        json.dumps(payload, allow_nan=False),
                    ),
                )
                db.execute(
                    "INSERT INTO event_cursors VALUES(?,?) ON CONFLICT(namespace) DO UPDATE SET sequence=excluded.sequence",
                    (self.namespace, sequence),
                )
                self._prune(db, sequence)
                db.commit()
            except BaseException:
                db.rollback()
                raise

    def read(self, after: int, limit: int) -> dict:
        if type(limit) is not int or limit < 1:
            raise ValueError("Event limit must be a positive integer")
        with self._lock:
            db = self._db()
            with db:
                sequence = self._sequence(db)
                if type(after) is not int or not 0 <= after <= sequence:
                    raise ValueError("Invalid event cursor")
                self._prune(db, sequence)
                rows = db.execute(
                    "SELECT payload FROM events WHERE namespace=? AND sequence>? ORDER BY sequence LIMIT ?",
                    (self.namespace, after, limit),
                ).fetchall()
                selected = [json.loads(row[0]) for row in rows]
                cursor = selected[-1]["sequence"] if selected else sequence
                return {
                    "events": selected,
                    "lost": max(0, cursor - after - len(selected)),
                    "cursor": cursor,
                }

    def close(self) -> None:
        with self._lock:
            self._closed = True
            if self._connection is not None:
                self._connection.close()
                self._connection = None
