"""Durable ordered consumers. Side effects require application-level idempotency."""

from __future__ import annotations

import asyncio
import json
import math
import time
import uuid
from dataclasses import dataclass
from typing import Any, NamedTuple, Optional, TypedDict

from .event_store import SQLiteEventStore


@dataclass(frozen=True)
class EventLease:
    consumer: str
    sequence: int
    token: str
    attempt: int
    event: dict[str, Any]
    lost: int = 0


class EventClaim(TypedDict):
    lease: Optional[EventLease]
    lost: int
    lost_total: int


class _ConsumerState(NamedTuple):
    cursor: int
    sequence: Optional[int]
    token: Optional[str]
    lease_until: float
    attempts: int
    retry_at: float
    payload: Optional[str]
    max_attempts: int
    lost: int


class DurableConsumer:
    """One outstanding event per consumer, leased atomically across processes.

    Explicit ack advances the cursor. Failure or lease expiry retries; exhausted
    events enter the private dead-letter table. Retention gaps are returned as
    `lost` and never interpreted as successfully processed events.
    """

    def __init__(
        self,
        store: SQLiteEventStore,
        consumer_id: str,
        *,
        lease_seconds: float = 60,
        max_attempts: int = 5,
        retry_delay: float = 1,
    ):
        if not isinstance(consumer_id, str) or not consumer_id or len(consumer_id) > 128:
            raise ValueError("Consumer ID must contain 1 to 128 characters")
        if type(max_attempts) is not int or not 1 <= max_attempts <= 100:
            raise ValueError("Maximum attempts must be between 1 and 100")
        for value in (lease_seconds, retry_delay):
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError("Lease and retry times must be finite and nonnegative")
        if lease_seconds <= 0:
            raise ValueError("Lease duration must be positive")
        self.store, self.id = store, consumer_id
        self.lease_seconds, self.max_attempts, self.retry_delay = (
            lease_seconds,
            max_attempts,
            retry_delay,
        )

    def _row(self, db) -> Optional[_ConsumerState]:
        row = db.execute(
            """SELECT cursor,sequence,token,lease_until,attempts,retry_at,payload,max_attempts,lost
            FROM event_consumers WHERE namespace=? AND id=?""",
            (self.store.namespace, self.id),
        ).fetchone()
        return _ConsumerState(*row) if row else None

    def _dead_letter(self, db, row: _ConsumerState, category: str):
        assert row.sequence is not None and row.payload is not None
        db.execute(
            "INSERT OR IGNORE INTO event_dead_letters VALUES(?,?,?,?,?,?,?)",
            (
                self.store.namespace,
                self.id,
                row.sequence,
                row.attempts,
                category,
                row.payload,
                time.time(),
            ),
        )
        self._advance(db, row.sequence)
        self._prune_dead_letters(db)

    def _prune_dead_letters(self, db):
        db.execute(
            """DELETE FROM event_dead_letters WHERE namespace=? AND consumer=?
            AND (created<? OR sequence NOT IN (SELECT sequence FROM event_dead_letters
            WHERE namespace=? AND consumer=? ORDER BY sequence DESC LIMIT ?))""",
            (
                self.store.namespace,
                self.id,
                time.time() - self.store.retention,
                self.store.namespace,
                self.id,
                self.store.capacity,
            ),
        )

    def _advance(self, db, sequence):
        db.execute(
            """UPDATE event_consumers SET cursor=?,sequence=NULL,token=NULL,
            lease_until=0,attempts=0,retry_at=0,payload=NULL WHERE namespace=? AND id=?""",
            (sequence, self.store.namespace, self.id),
        )

    def _claim(self) -> EventClaim:
        store = self.store
        with store._lock:
            db = store._db()
            db.execute("BEGIN IMMEDIATE")
            try:
                if (
                    self._row(db) is None
                    and db.execute(
                        "SELECT COUNT(*) FROM event_consumers WHERE namespace=?", (store.namespace,)
                    ).fetchone()[0]
                    >= 128
                ):
                    raise ValueError("This journal has reached its durable consumer capacity")
                db.execute(
                    "INSERT OR IGNORE INTO event_consumers(namespace,id,max_attempts) VALUES(?,?,?)",
                    (store.namespace, self.id, self.max_attempts),
                )
                row = self._row(db)
                assert row is not None
                if row.max_attempts != self.max_attempts:
                    raise ValueError("Consumer retry policy differs from its persisted policy")
                now, lost = time.time(), 0
                if row.sequence is not None and (row.lease_until > now or row.retry_at > now):
                    db.commit()
                    return {"lease": None, "lost": 0, "lost_total": row.lost}
                if row.sequence is not None and row.attempts >= self.max_attempts:
                    self._dead_letter(db, row, "lease_expired")
                    row = self._row(db)
                    assert row is not None
                if row.sequence is None:
                    highwater = store._sequence(db)
                    store._prune(db, highwater)
                    event = db.execute(
                        """SELECT sequence,payload FROM events WHERE namespace=?
                        AND sequence>? ORDER BY sequence LIMIT 1""",
                        (store.namespace, row.cursor),
                    ).fetchone()
                    sequence = event[0] if event else highwater + 1
                    lost = max(0, sequence - row.cursor - 1)
                    db.execute(
                        "UPDATE event_consumers SET lost=lost+? WHERE namespace=? AND id=?",
                        (lost, store.namespace, self.id),
                    )
                    if not event:
                        self._advance(db, highwater)
                        db.commit()
                        return {"lease": None, "lost": lost, "lost_total": row.lost + lost}
                    payload, attempt = event[1], 1
                else:
                    sequence, payload, attempt = row.sequence, row.payload, row.attempts + 1
                    lost = max(0, sequence - row.cursor - 1)
                assert payload is not None
                token = uuid.uuid4().hex
                db.execute(
                    """UPDATE event_consumers SET sequence=?,payload=?,attempts=?,token=?,
                    lease_until=?,retry_at=0 WHERE namespace=? AND id=?""",
                    (
                        sequence,
                        payload,
                        attempt,
                        token,
                        now + self.lease_seconds,
                        store.namespace,
                        self.id,
                    ),
                )
                db.commit()
                state = self._row(db)
                assert state is not None
                return {
                    "lease": EventLease(
                        self.id, sequence, token, attempt, json.loads(payload), lost
                    ),
                    "lost": lost,
                    "lost_total": state.lost,
                }
            except BaseException:
                db.rollback()
                raise

    async def claim(self) -> EventClaim:
        return await asyncio.to_thread(self._claim)

    def _finish(self, lease: EventLease, action: str):
        with self.store._lock:
            db = self.store._db()
            db.execute("BEGIN IMMEDIATE")
            try:
                row = self._row(db)
                if (
                    lease.consumer != self.id
                    or row is None
                    or row.sequence != lease.sequence
                    or row.token != lease.token
                    or row.lease_until <= time.time()
                ):
                    raise ValueError("Event lease is stale or belongs to another consumer")
                if row.max_attempts != self.max_attempts:
                    raise ValueError("Consumer retry policy differs from its persisted policy")
                if action == "renew":
                    db.execute(
                        """UPDATE event_consumers SET lease_until=?
                        WHERE namespace=? AND id=?""",
                        (time.time() + self.lease_seconds, self.store.namespace, self.id),
                    )
                elif action == "ack":
                    self._advance(db, lease.sequence)
                elif row.attempts >= self.max_attempts:
                    self._dead_letter(db, row, "handler_failed")
                else:
                    delay = min(3600, self.retry_delay * 2 ** (row.attempts - 1))
                    db.execute(
                        """UPDATE event_consumers SET token=NULL,lease_until=0,retry_at=?
                        WHERE namespace=? AND id=?""",
                        (time.time() + delay, self.store.namespace, self.id),
                    )
                db.commit()
            except BaseException:
                db.rollback()
                raise

    async def ack(self, lease: EventLease) -> None:
        await asyncio.to_thread(self._finish, lease, "ack")

    async def fail(self, lease: EventLease) -> None:
        """Record only a fixed failure category; never save exception text."""
        await asyncio.to_thread(self._finish, lease, "fail")

    async def renew(self, lease: EventLease) -> None:
        """Extend a still-valid lease while processing a long-running event."""
        await asyncio.to_thread(self._finish, lease, "renew")

    def _dead_letters(self, after: int, limit: int) -> list[dict]:
        if type(after) is not int or after < 0 or type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("Invalid dead-letter cursor or limit")
        with self.store._lock:
            with self.store._db() as db:
                self._prune_dead_letters(db)
            rows = (
                self.store._db()
                .execute(
                    """SELECT sequence,attempts,category,payload
                FROM event_dead_letters WHERE namespace=? AND consumer=? AND sequence>?
                ORDER BY sequence LIMIT ?""",
                    (self.store.namespace, self.id, after, limit),
                )
                .fetchall()
            )
            return [
                {
                    "sequence": row[0],
                    "attempts": row[1],
                    "category": row[2],
                    "event": json.loads(row[3]),
                }
                for row in rows
            ]

    async def dead_letters(self, *, after: int = 0, limit: int = 50) -> list[dict]:
        return await asyncio.to_thread(self._dead_letters, after, limit)
