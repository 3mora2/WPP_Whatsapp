"""Synthetic endurance/latency probe. Never opens WhatsApp or sends messages."""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import tempfile
import time
import tracemalloc
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from WPP_Whatsapp.core.event_store import SQLiteEventStore  # noqa: E402
from WPP_Whatsapp.core.work import WorkController  # noqa: E402


async def measure(iterations, cycles):
    work = WorkController({"maxConcurrentOperations": 4, "maxPendingOperations": 16})
    latencies = deque(maxlen=1024)
    tracemalloc.start()
    with tempfile.TemporaryDirectory(prefix="wpp-soak-") as directory:
        path = Path(directory) / "events.db"
        baseline = None
        started = time.perf_counter()
        for cycle in range(cycles):
            store = SQLiteEventStore(path, "synthetic", 256, 3600)
            initial = await asyncio.to_thread(lambda active=store: active.sequence)

            async def operation(index, active=store, generation=cycle):
                tick = time.perf_counter()
                async with work.slot():
                    await asyncio.to_thread(
                        active.append,
                        {"message": {"id": f"{generation}-{index}", "body": "synthetic"}},
                    )
                latencies.append(time.perf_counter() - tick)

            for start in range(0, iterations, 8):
                await asyncio.gather(
                    *(operation(index) for index in range(start, min(iterations, start + 8)))
                )
            page = await asyncio.to_thread(store.read, 0, 256)
            assert store.sequence == initial + iterations and len(page["events"]) <= 256
            await asyncio.to_thread(store.close)
            if baseline is None:
                baseline = tracemalloc.get_traced_memory()[0]
            print(f"Completed synthetic cycle {cycle + 1}/{cycles}", flush=True)
        elapsed = time.perf_counter() - started
        current, peak = tracemalloc.get_traced_memory()
        ordered = sorted(latencies)
        result = {
            "synthetic": True,
            "operations": iterations * cycles,
            "restart_cycles": cycles,
            "seconds": round(elapsed, 2),
            "p50_ms": round(statistics.median(ordered) * 1000, 2),
            "p95_ms": round(ordered[int((len(ordered) - 1) * 0.95)] * 1000, 2),
            "python_peak_bytes": peak,
            "python_growth_after_warmup": current - baseline,
            "operations_idle": work.stats["active"] == work.stats["waiting"] == 0,
        }
    tracemalloc.stop()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--cycles", type=int, default=5)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not 1 <= args.iterations <= 100000 or not 1 <= args.cycles <= 100:
        parser.error("Iterations must be 1..100000 and cycles 1..100")
    result = asyncio.run(measure(args.iterations, args.cycles))
    if args.report:
        args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
