"""Atomic delivery metadata stores; they never receive message contents."""

from __future__ import annotations

import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Protocol

from .delivery_models import DeliveryReceipt, DeliveryState, ExpectedMessage
from .errors import OperationConflictError


class DeliveryStore(Protocol):
    blocking: bool

    def get(self, operation_id: str) -> Optional[DeliveryReceipt]: ...

    def claim(self, receipt: DeliveryReceipt) -> Optional[DeliveryReceipt]:
        """Reserve atomically; return the existing receipt if already reserved."""
        ...

    def claim_request(
        self, receipt: DeliveryReceipt, fingerprint: str
    ) -> Optional[DeliveryReceipt]: ...

    def save(self, receipt: DeliveryReceipt) -> None: ...

    def set_expected(self, operation_id: str, expected: ExpectedMessage) -> None: ...

    def expected(self, operation_id: str) -> Optional[ExpectedMessage]: ...

    def close(self) -> None: ...


class MemoryDeliveryStore:
    blocking = False

    def __init__(self) -> None:
        self._records: dict[str, DeliveryReceipt] = {}
        self._fingerprints: dict[str, str] = {}
        self._expected: dict[str, ExpectedMessage] = {}
        self._lock = threading.RLock()

    def get(self, operation_id: str) -> Optional[DeliveryReceipt]:
        with self._lock:
            return self._records.get(operation_id)

    def claim(self, receipt: DeliveryReceipt) -> Optional[DeliveryReceipt]:
        with self._lock:
            previous = self._records.get(receipt.operation_id)
            if previous is None:
                self._records[receipt.operation_id] = receipt
            return previous

    def save(self, receipt: DeliveryReceipt) -> None:
        with self._lock:
            self._records[receipt.operation_id] = receipt

    def claim_request(
        self, receipt: DeliveryReceipt, fingerprint: str
    ) -> Optional[DeliveryReceipt]:
        with self._lock:
            previous = self._records.get(receipt.operation_id)
            if previous is not None and self._fingerprints.get(receipt.operation_id) != fingerprint:
                raise OperationConflictError("Operation ID does not match the reserved request")
            if previous is None:
                self._records[receipt.operation_id] = receipt
                self._fingerprints[receipt.operation_id] = fingerprint
            return previous

    def close(self) -> None:
        pass

    def set_expected(self, operation_id: str, expected: ExpectedMessage) -> None:
        with self._lock:
            receipt = self._records.get(operation_id)
            if (
                receipt is None
                or receipt.state not in (DeliveryState.PENDING, DeliveryState.UNKNOWN)
                or operation_id in self._expected
            ):
                raise OperationConflictError("Expected message is already reserved or missing")
            self._expected[operation_id] = expected

    def expected(self, operation_id: str) -> Optional[ExpectedMessage]:
        with self._lock:
            return self._expected.get(operation_id)


class SQLiteDeliveryStore:
    blocking = True
    SCHEMA = """CREATE TABLE IF NOT EXISTS deliveries (
        namespace TEXT NOT NULL, id TEXT NOT NULL, state TEXT NOT NULL,
        message_id TEXT, updated REAL NOT NULL, PRIMARY KEY(namespace, id)
    )"""

    def __init__(self, path, namespace: str = "default") -> None:
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.namespace = namespace
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(str(self.path), check_same_thread=False)
        self._closed = False
        try:
            with self._connection:
                self._connection.execute(self.SCHEMA)
                columns = {
                    row[1] for row in self._connection.execute("PRAGMA table_info(deliveries)")
                }
                for name, declaration in {
                    "fingerprint": "TEXT",
                    "expected_id": "TEXT",
                    "chat_id": "TEXT",
                    "message_type": "TEXT",
                    "tombstone": "INTEGER NOT NULL DEFAULT 0",
                }.items():
                    if name in columns:
                        continue
                    try:
                        self._connection.execute(
                            f"ALTER TABLE deliveries ADD COLUMN {name} {declaration}"
                        )
                    except sqlite3.OperationalError:
                        # Another process can finish the additive migration first.
                        columns = {
                            row[1]
                            for row in self._connection.execute("PRAGMA table_info(deliveries)")
                        }
                        if name not in columns:
                            raise
        except BaseException:
            self._connection.close()
            raise

    def get(self, operation_id: str) -> Optional[DeliveryReceipt]:
        with self._lock, self._reader() as connection:
            row = connection.execute(
                "SELECT state,message_id FROM deliveries WHERE namespace=? AND id=?",
                (self.namespace, operation_id),
            ).fetchone()
            return DeliveryReceipt(operation_id, DeliveryState(row[0]), row[1]) if row else None

    @contextmanager
    def _reader(self):
        if not self._closed:
            yield self._connection
            return
        # Closed trackers remain inspectable without retaining a live handle or
        # recreating/migrating their database. Never reopen them for writes.
        connection = sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True)
        try:
            yield connection
        finally:
            connection.close()

    def claim(self, receipt: DeliveryReceipt) -> Optional[DeliveryReceipt]:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "INSERT OR IGNORE INTO deliveries(namespace,id,state,message_id,updated) VALUES (?, ?, ?, NULL, ?)",
                (self.namespace, receipt.operation_id, receipt.state.value, time.time()),
            )
            if cursor.rowcount == 0:
                self._check_tombstone(receipt.operation_id)
                return self.get(receipt.operation_id)
            return None

    def claim_request(
        self, receipt: DeliveryReceipt, fingerprint: str
    ) -> Optional[DeliveryReceipt]:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "INSERT OR IGNORE INTO deliveries(namespace,id,state,updated,fingerprint) VALUES (?,?,?,?,?)",
                (
                    self.namespace,
                    receipt.operation_id,
                    receipt.state.value,
                    time.time(),
                    fingerprint,
                ),
            )
            if cursor.rowcount:
                return None
            self._check_tombstone(receipt.operation_id)
            row = self._connection.execute(
                "SELECT fingerprint FROM deliveries WHERE namespace=? AND id=?",
                (self.namespace, receipt.operation_id),
            ).fetchone()
            if row[0] != fingerprint:
                raise OperationConflictError("Operation ID does not match the reserved request")
            return self.get(receipt.operation_id)

    def save(self, receipt: DeliveryReceipt) -> None:
        with self._lock, self._connection:
            self._check_tombstone(receipt.operation_id)
            cursor = self._connection.execute(
                """INSERT INTO deliveries(namespace,id,state,message_id,updated) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(namespace,id) DO UPDATE SET state=excluded.state,
                message_id=excluded.message_id,updated=excluded.updated WHERE deliveries.tombstone=0""",
                (
                    self.namespace,
                    receipt.operation_id,
                    receipt.state.value,
                    receipt.message_id,
                    time.time(),
                ),
            )
            if cursor.rowcount != 1:
                raise OperationConflictError(
                    "Operation metadata was compacted; ID remains reserved"
                )

    def _check_tombstone(self, operation_id: str) -> None:
        row = self._connection.execute(
            "SELECT tombstone FROM deliveries WHERE namespace=? AND id=?",
            (self.namespace, operation_id),
        ).fetchone()
        if row and row[0]:
            raise OperationConflictError("Operation metadata was compacted; ID remains reserved")

    def set_expected(self, operation_id: str, expected: ExpectedMessage) -> None:
        with self._lock, self._connection:
            self._check_tombstone(operation_id)
            cursor = self._connection.execute(
                """UPDATE deliveries SET expected_id=?, chat_id=?, message_type=?,updated=?
                WHERE namespace=? AND id=? AND expected_id IS NULL
                AND state IN ('pending','unknown') AND tombstone=0""",
                (
                    expected.message_id,
                    expected.chat_id,
                    expected.type,
                    time.time(),
                    self.namespace,
                    operation_id,
                ),
            )
            if cursor.rowcount != 1:
                raise OperationConflictError("Expected message is already reserved or missing")

    def expected(self, operation_id: str) -> Optional[ExpectedMessage]:
        with self._lock, self._reader() as connection:
            row = connection.execute(
                "SELECT expected_id,chat_id,message_type FROM deliveries WHERE namespace=? AND id=?",
                (self.namespace, operation_id),
            ).fetchone()
            return ExpectedMessage(*row) if row and row[0] else None

    def list_operations(self, *, state=None, after="", limit=50) -> list[dict]:
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("Operation limit must be between 1 and 200")
        if state is not None:
            state = DeliveryState(state).value
        with self._lock, self._reader() as connection:
            rows = connection.execute(
                """SELECT id,state,message_id,updated,tombstone,expected_id FROM deliveries
                WHERE namespace=? AND id>? AND (? IS NULL OR state=?) ORDER BY id LIMIT ?""",
                (self.namespace, after, state, state, limit),
            ).fetchall()
            return [
                dict(
                    zip(
                        (
                            "operation_id",
                            "state",
                            "message_id",
                            "updated",
                            "compacted",
                            "expected_message_id",
                        ),
                        row,
                    )
                )
                for row in rows
            ]

    def compact(self, before: float, *, dry_run: bool = False) -> int:
        """Discard old terminal metadata while retaining IDs and fingerprints forever."""
        import math

        if type(before) not in (int, float) or not math.isfinite(before):
            raise ValueError("A finite cutoff timestamp is required")
        with self._lock, self._connection:
            if dry_run:
                return self._connection.execute(
                    """SELECT COUNT(*) FROM deliveries WHERE namespace=? AND updated<?
                    AND state IN ('confirmed','failed') AND tombstone=0""",
                    (self.namespace, before),
                ).fetchone()[0]
            cursor = self._connection.execute(
                """UPDATE deliveries SET message_id=NULL,expected_id=NULL,chat_id=NULL,
                message_type=NULL,tombstone=1 WHERE namespace=? AND updated<?
                AND state IN ('confirmed','failed') AND tombstone=0""",
                (self.namespace, before),
            )
            return cursor.rowcount

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._connection.close()
                self._closed = True
