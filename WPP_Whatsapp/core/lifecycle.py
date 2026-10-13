from __future__ import annotations

import math
import time
from enum import Enum

from .errors import SessionClosedError, SessionNotReadyError


class SessionState(str, Enum):
    NEW = "new"
    STARTING = "starting"
    WAITING_QR = "waiting_qr"
    SYNCING = "syncing"
    READY = "ready"
    RECONNECTING = "reconnecting"
    CLOSING = "closing"
    CLOSED = "closed"
    FAILED = "failed"


class Deadline:
    """Monotonic deadline. Zero disables it; public timeout units are explicit."""

    def __init__(self, seconds=0):
        if isinstance(seconds, bool):
            seconds = int(seconds)
        if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Timeout must be a finite nonnegative number")
        self.end = time.monotonic() + seconds if seconds else None

    @classmethod
    def milliseconds(cls, value):
        return cls(value / 1000)

    @property
    def expired(self):
        return self.end is not None and time.monotonic() >= self.end

    @property
    def remaining(self):
        return max(0, self.end - time.monotonic()) if self.end is not None else None


class SessionLifecycle:
    def __init__(self):
        self.state = SessionState.NEW
        self.history = [(self.state.value, time.monotonic())]

    def transition(self, state):
        state = SessionState(state)
        if state == self.state:
            return
        if self.state == SessionState.CLOSED and state != SessionState.STARTING:
            raise SessionClosedError("Session is closed")
        if self.state == SessionState.CLOSING and state != SessionState.CLOSED:
            raise SessionClosedError("Session is closing")
        if self.state in (SessionState.NEW, SessionState.FAILED) and state not in (
            SessionState.STARTING,
            SessionState.CLOSING,
            SessionState.CLOSED,
            SessionState.FAILED,
        ):
            raise SessionNotReadyError("Start the session before changing its connection state")
        self.state = state
        self.history.append((state.value, time.monotonic()))
        self.history = self.history[-100:]

    def require_ready(self):
        if self.state in (SessionState.CLOSED, SessionState.CLOSING):
            raise SessionClosedError("Session is closed")
        if self.state != SessionState.READY:
            raise SessionNotReadyError(f"Session is {self.state.value}")
