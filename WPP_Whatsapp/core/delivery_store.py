"""Atomic delivery metadata stores; they never receive message contents."""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional, Protocol

from .delivery_models import DeliveryReceipt, DeliveryState
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

    def close(self) -> None: ...


class MemoryDeliveryStore:
    blocking = False

    def __init__(self) -> None:
        self._records: dict[str, DeliveryReceipt] = {}
        self._fingerprints: dict[str, str] = {}
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


class SQLiteDeliveryStore:
    blocking = True
    SCHEMA = """CREATE TABLE IF NOT EXISTS deliveries (
        namespace TEXT NOT NULL, id TEXT NOT NULL, state TEXT NOT NULL,
        message_id TEXT, updated REAL NOT NULL, PRIMARY KEY(namespace, id)
    )"""

    def __init__(self, path, namespace: str = "default") -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.namespace = namespace
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(str(path), check_same_thread=False)
        try:
            with self._connection:
                self._connection.execute(self.SCHEMA)
                columns = {
                    row[1] for row in self._connection.execute("PRAGMA table_info(deliveries)")
                }
                if "fingerprint" not in columns:
                    try:
                        self._connection.execute(
                            "ALTER TABLE deliveries ADD COLUMN fingerprint TEXT"
                        )
                    except sqlite3.OperationalError:
                        # Another process can finish the additive migration first.
                        columns = {
                            row[1]
                            for row in self._connection.execute("PRAGMA table_info(deliveries)")
                        }
                        if "fingerprint" not in columns:
                            raise
        except BaseException:
            self._connection.close()
            raise

    def get(self, operation_id: str) -> Optional[DeliveryReceipt]:
        with self._lock:
            row = self._connection.execute(
                "SELECT state,message_id FROM deliveries WHERE namespace=? AND id=?",
                (self.namespace, operation_id),
            ).fetchone()
            return DeliveryReceipt(operation_id, DeliveryState(row[0]), row[1]) if row else None

    def claim(self, receipt: DeliveryReceipt) -> Optional[DeliveryReceipt]:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "INSERT OR IGNORE INTO deliveries(namespace,id,state,message_id,updated) VALUES (?, ?, ?, NULL, ?)",
                (self.namespace, receipt.operation_id, receipt.state.value, time.time()),
            )
            return self.get(receipt.operation_id) if cursor.rowcount == 0 else None

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
            row = self._connection.execute(
                "SELECT fingerprint FROM deliveries WHERE namespace=? AND id=?",
                (self.namespace, receipt.operation_id),
            ).fetchone()
            if row[0] != fingerprint:
                raise OperationConflictError("Operation ID does not match the reserved request")
            return self.get(receipt.operation_id)

    def save(self, receipt: DeliveryReceipt) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """INSERT INTO deliveries(namespace,id,state,message_id,updated) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(namespace,id) DO UPDATE SET state=excluded.state,
                message_id=excluded.message_id,updated=excluded.updated""",
                (
                    self.namespace,
                    receipt.operation_id,
                    receipt.state.value,
                    receipt.message_id,
                    time.time(),
                ),
            )

    def close(self) -> None:
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None
