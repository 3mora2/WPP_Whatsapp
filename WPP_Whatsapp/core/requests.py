"""Canonical request identities. Persist digests, never request bodies or filenames."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def fingerprint(operation: str, request: Any) -> str:
    def default(value: Any) -> str:
        if isinstance(value, Path):
            return str(value)
        raise TypeError("Tracked request arguments must be JSON-compatible")

    encoded = json.dumps(
        [operation, request],
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        default=default,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
