"""Bounded operational measurements; labels never contain account or message IDs."""

from __future__ import annotations

import math
import os
from pathlib import Path

import psutil


def find_browser_roots(profile):
    if profile is None:
        return {}
    target = str(Path(profile).resolve()).casefold()
    roots = {}
    for process in psutil.Process().children(recursive=True):
        try:
            for arg in process.cmdline():
                if (
                    arg.startswith("--user-data-dir=")
                    and str(Path(arg.split("=", 1)[1]).resolve()).casefold() == target
                ):
                    roots[process.pid] = process.create_time()
        except (psutil.Error, OSError):
            continue
    return roots


def process_snapshot(roots):
    current = psutil.Process()
    browsers = {}
    for pid, created in roots.items():
        try:
            process = psutil.Process(pid)
            if process.create_time() != created:
                continue
            browsers[pid] = process
            browsers.update({child.pid: child for child in process.children(recursive=True)})
        except psutil.Error:
            continue
    rss, count = 0, 0
    for process in browsers.values():
        try:
            rss += process.memory_info().rss
            count += 1
        except psutil.Error:
            continue
    return {
        "python_rss_bytes": current.memory_info().rss,
        "python_handles": current.num_handles() if os.name == "nt" else current.num_fds(),
        "owned_browser_rss_bytes": rss,
        "owned_browser_processes": count,
    }


def prometheus(snapshot: dict) -> str:
    """Render numeric allowlisted measurements for an application-owned HTTP endpoint."""
    from .commands import COMMANDS

    lines = []

    def emit(name, value, labels=""):
        if type(value) in (int, float) and math.isfinite(value):
            lines.append(f"wpp_{name}{labels} {value}")

    for section, keys in {
        "bridge": ("calls", "failures", "duration_seconds"),
        "operations": (
            "active",
            "waiting",
            "rejected",
            "completed",
            "queue_seconds",
            "duration_seconds",
        ),
        "events": ("submitted", "delivered", "rejected", "duplicates", "callback_errors"),
        "process": (
            "python_rss_bytes",
            "python_handles",
            "owned_browser_rss_bytes",
            "owned_browser_processes",
        ),
        "recovery": ("attempts", "successes", "exhausted"),
    }.items():
        for key in keys:
            emit(section + "_" + key, snapshot.get(section, {}).get(key))
    for command, measurements in snapshot.get("commands", {}).items():
        if command not in COMMANDS:
            continue
        labels = '{command="' + command + '"}'
        for key in ("calls", "failures", "duration_seconds", "max_seconds"):
            emit("command_" + key, measurements.get(key), labels)
    return "\n".join(lines) + "\n"
