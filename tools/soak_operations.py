"""Synthetic delivery/consumer endurance; never opens a browser or sends WhatsApp messages."""

import argparse
import asyncio
import hashlib
import json
import statistics
import sys
import tempfile
import time
import tracemalloc
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from WPP_Whatsapp.core.consumers import DurableConsumer  # noqa: E402
from WPP_Whatsapp.core.delivery import DeliveryTracker  # noqa: E402
from WPP_Whatsapp.core.delivery_models import ExpectedMessage  # noqa: E402
from WPP_Whatsapp.core.errors import DeliveryUncertainError, OperationConflictError  # noqa: E402
from WPP_Whatsapp.core.event_store import SQLiteEventStore  # noqa: E402


async def measure(iterations, cycles):
    result = {
        "synthetic": True,
        "operations": 0,
        "event_retries": 0,
        "uncertain_recovered": 0,
        "duplicates_avoided": 0,
        "restart_cycles": cycles,
    }
    latencies = deque(maxlen=1024)
    tracemalloc.start()
    started, baseline = time.perf_counter(), None
    with tempfile.TemporaryDirectory(prefix="wpp-operations-") as directory:
        path = Path(directory)
        for cycle in range(cycles):
            tracker = DeliveryTracker(path / "deliveries", "synthetic")
            journal = SQLiteEventStore(path / "events", "synthetic", 256, 3600)
            consumer = DurableConsumer(journal, "worker", max_attempts=2, retry_delay=0)
            try:
                for index in range(iterations):
                    tick = time.perf_counter()
                    ident = f"{cycle:03}-{index:06}"
                    key = "true_1@c.us_SYNTHETIC_" + ident
                    digest = hashlib.sha256(ident.encode()).hexdigest()

                    async def prepare(message_id=key):
                        return ExpectedMessage(message_id, "1@c.us", "chat")

                    async def synthetic_send(message_id=key, number=index):
                        if number % 97 == 0:
                            raise ValueError("Synthetic result conversion failure")
                        return {"id": message_id}

                    try:
                        await tracker.send(
                            synthetic_send, ident, request_fingerprint=digest, prepare=prepare
                        )
                    except DeliveryUncertainError:
                        expected = await tracker.expected_async(ident)
                        assert expected and expected.message_id == key
                        # Synthetic evidence only. Real services require a WhatsApp lookup.
                        await tracker.reconcile_async(ident, key)
                        result["uncertain_recovered"] += 1
                    await asyncio.to_thread(
                        journal.append, {"message": {"id": ident, "body": "synthetic"}}
                    )
                    claimed = await consumer.claim()
                    assert claimed["lost_total"] == 0 and claimed["lease"] is not None
                    lease = claimed["lease"]
                    if index % 29 == 0:
                        await consumer.fail(lease)
                        lease = (await consumer.claim())["lease"]
                        assert lease and lease.attempt == 2
                        result["event_retries"] += 1
                    if index % 137 == 0:
                        await consumer.fail(lease)
                        if lease.attempt == 1:
                            lease = (await consumer.claim())["lease"]
                            result["event_retries"] += 1
                            await consumer.fail(lease)
                        assert (await consumer.claim())["lease"] is None
                    else:
                        await consumer.ack(lease)
                    assert len(tracker.records) <= 1000
                    result["operations"] += 1
                    if (index + 1) % 1000 == 0:
                        print(f"Completed {result['operations']} synthetic operations", flush=True)
                    latencies.append(time.perf_counter() - tick)
                ident = f"{cycle:03}-000000"

                async def must_not_dispatch():
                    raise AssertionError("Confirmed operation was replayed")

                digest = hashlib.sha256(ident.encode()).hexdigest()
                await tracker.send(must_not_dispatch, ident, request_fingerprint=digest)
                result["duplicates_avoided"] += 1
                assert len(await consumer.dead_letters(limit=200)) <= 200
                retained = (
                    journal._db()
                    .execute("SELECT COUNT(*) FROM event_dead_letters WHERE namespace='synthetic'")
                    .fetchone()[0]
                )
                assert retained <= 256
                result["dead_letters_retained"] = retained
            finally:
                await tracker.aclose()
                await asyncio.to_thread(journal.close)
            if baseline is None:
                baseline = tracemalloc.get_traced_memory()[0]
            print(f"Completed delivery/consumer cycle {cycle + 1}/{cycles}", flush=True)
        reopened = DeliveryTracker(path / "deliveries", "synthetic")
        try:
            await reopened.send(must_not_dispatch, ident, request_fingerprint=digest)
            result["duplicates_avoided"] += 1
            compacted = await asyncio.to_thread(reopened._store.compact, time.time() + 1)
            assert compacted == result["operations"]
            try:
                await reopened.send(must_not_dispatch, ident, request_fingerprint=digest)
            except OperationConflictError:
                result["duplicates_avoided"] += 1
            else:
                raise AssertionError("Compaction removed duplicate protection")
        finally:
            await reopened.aclose()
        current, peak = tracemalloc.get_traced_memory()
        ordered = sorted(latencies)
        result.update(
            seconds=round(time.perf_counter() - started, 2),
            p50_ms=round(statistics.median(ordered) * 1000, 2),
            p95_ms=round(ordered[int((len(ordered) - 1) * 0.95)] * 1000, 2),
            python_peak_bytes=peak,
            python_growth_after_warmup=current - baseline,
        )
    tracemalloc.stop()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not 1 <= args.iterations <= 100000 or not 1 <= args.cycles <= 100:
        parser.error("Iterations must be 1..100000 and cycles 1..100")
    result = asyncio.run(measure(args.iterations, args.cycles))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result), flush=True)
