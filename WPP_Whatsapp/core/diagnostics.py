"""Allowlisted support reports: never serialize exceptions, options or browser data."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Optional


@dataclass(frozen=True)
class DiagnosticFailure:
    phase: str
    category: str


def classify_failure(phase: str, error: BaseException) -> DiagnosticFailure:
    from .errors import BridgeError, ProfileInUseError, RuntimeCompatibilityError

    if isinstance(error, ProfileInUseError):
        category = "profile_in_use"
    elif isinstance(error, RuntimeCompatibilityError):
        category = "runtime_incompatible"
    elif isinstance(error, BridgeError):
        category = "browser_operation"
    elif phase == "browser_operation":
        category = "browser_operation"
    elif isinstance(error, TimeoutError):
        category = "timeout"
    else:
        category = "operation_failed"
    return DiagnosticFailure(phase, category)


def snapshot(state, context=None, failure: Optional[DiagnosticFailure] = None) -> dict:
    try:
        package_version = version("WPP_Whatsapp")
    except PackageNotFoundError:
        package_version = "source"
    bridge = getattr(context, "bridge", None)
    failure = failure or getattr(bridge, "last_failure", None)
    dispatcher = getattr(context, "_dispatcher", None)
    capabilities = getattr(context, "runtime_capabilities", {}) or {}
    # Values from the runtime are copied only when their expected type is verified.
    return {
        "schema_version": 1,
        "package_version": package_version,
        "state": state.value,
        "ready": state.value == "ready",
        "failure": asdict(failure) if failure else None,
        "bridge": {
            key: value
            for key, value in getattr(bridge, "metrics", {}).items()
            if key in {"calls", "failures", "duration_seconds"} and type(value) in (int, float)
        },
        "events": {
            key: value
            for key, value in getattr(dispatcher, "stats", {}).items()
            if key in {"submitted", "delivered", "rejected", "duplicates", "callback_errors"}
            and type(value) is int
        },
        "operations": {
            key: value
            for key, value in getattr(
                getattr(context, "_work_controller", None), "stats", {}
            ).items()
            if key
            in {"active", "waiting", "rejected", "completed", "queue_seconds", "duration_seconds"}
            and type(value) in (int, float)
        },
        "capabilities": {
            key: value
            for key, value in capabilities.items()
            if key in {"ready", "history", "events", "auth"} and type(value) is bool
        },
    }
