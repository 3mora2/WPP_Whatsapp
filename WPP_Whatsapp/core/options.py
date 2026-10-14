"""Validate public session options without discarding extension/browser options."""

from __future__ import annotations

import math
import os
from typing import Any, Mapping

TIMEOUT_OPTIONS = frozenset(
    {
        "autoClose",
        "deviceSyncTimeout",
        "navigationTimeout",
        "runtimeReadyTimeout",
        "pageLoadTimeout",
        "operationTimeout",
        "reconnectInitialDelay",
        "reconnectMaxDelay",
        "reconnectAttemptTimeout",
        "eventRetentionSeconds",
    }
)
PATH_OPTIONS = frozenset({"deliveryStore", "runtimeCacheDir", "eventStore"})


def validate_options(options: Mapping[str, Any], **overrides: Any) -> dict[str, Any]:
    """Return an independent copy; reject invalid known settings before startup.

    Legacy aliases and Playwright options are deliberately preserved. Overrides
    participate in validation without being inserted into the returned mapping.
    """
    values = {**options, **overrides}
    for name in ("reconnectInitialDelay", "reconnectMaxDelay"):
        if name in values and type(values[name]) not in (int, float):
            raise ValueError(f"{name} must be a nonnegative number")
    for name in ("maxConcurrentOperations", "maxPendingOperations", "eventBufferSize"):
        if name in values and (type(values[name]) is not int or values[name] < 1):
            raise ValueError(f"{name} must be a positive integer")
    for name in ("reconnectAttempts", "sendRateCalls"):
        if name in values and (type(values[name]) is not int or values[name] < 0):
            raise ValueError(f"{name} must be a nonnegative integer")
    for name in ("sendRatePeriod", "reconnectAttemptTimeout", "eventRetentionSeconds"):
        if name in values and (
            type(values[name]) not in (int, float)
            or not math.isfinite(values[name])
            or values[name] <= 0
        ):
            raise ValueError(f"{name} must be a finite positive number")
    if values.get("maxPendingOperations", 64) < values.get("maxConcurrentOperations", 4):
        raise ValueError("maxPendingOperations must cover all concurrent operations")
    for name in TIMEOUT_OPTIONS & values.keys():
        value = values[name]
        if name == "autoClose" and value is None:
            continue  # Existing Whatsapp constructor uses its legacy default.
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be a finite nonnegative number")
    if "eventQueueSize" in values:
        size = values["eventQueueSize"]
        if not isinstance(size, int) or isinstance(size, bool) or size < 1:
            raise ValueError("eventQueueSize must be a positive integer")
    for name in PATH_OPTIONS & values.keys():
        value = values[name]
        if value is not None and (
            not isinstance(value, (str, os.PathLike)) or not os.fspath(value)
        ):
            raise ValueError(f"{name} must be a nonempty filesystem path or None")
    return dict(options)
