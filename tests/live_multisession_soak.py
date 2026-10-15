"""Opt-in two-account read-only endurance. No outgoing sends; reports omit IDs/bodies."""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from WPP_Whatsapp import AsyncClient, SessionState  # noqa: E402
from WPP_Whatsapp.mcp.event_buffer import EventBuffer  # noqa: E402


async def run(args):
    logging.getLogger("WPP_Whatsapp").setLevel(logging.WARNING)
    clients = [
        AsyncClient(
            session,
            token_directory=str(ROOT / "tokens"),
            wait_for_login=False,
            autoClose=0,
            logQR=False,
            reconnectAttempts=3,
            reconnectAttemptTimeout=60,
            deliveryStore=str(ROOT / "tokens/.deliveries" / (session + ".sqlite3")),
        )
        for session in (args.first, args.second)
    ]
    buffers = [
        EventBuffer(
            path=ROOT / "tokens/.events" / (client.session + ".sqlite3"), namespace=client.session
        )
        for client in clients
    ]
    report = {
        "sends_performed": 0,
        "requested_seconds": args.seconds,
        "samples": 0,
        "recoveries": 0,
        "fresh_group_callbacks": [0, 0],
        "callback_lookup_matches": [0, 0],
        "callback_errors": [0, 0],
        "samples_data": [],
        "state_changes": [],
        "transient_outages": 0,
        "source_candidate": "2.4.0",
    }

    def save():
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")

    for index, client in enumerate(clients):

        async def state_changed(state, account=index):
            # Connection enum strings only; never include browser errors or IDs.
            if isinstance(state, str) and state.isupper() and state.replace("_", "").isalpha():
                report["state_changes"].append(
                    {"account": account, "state": state, "time": round(time.monotonic(), 2)}
                )
                report["state_changes"] = report["state_changes"][-1000:]

        client.events.on("onStateChange", state_changed)

        async def receive(message, account=index):
            try:
                await buffers[account].append(message)
                ident = message.get("id", "")
                if (
                    report.get("phase") == "running"
                    and isinstance(ident, str)
                    and "@g.us_" in ident
                    and not message.get("fromMe")
                ):
                    report["fresh_group_callbacks"][account] += 1
                    found = await clients[account].messages.get_message(ident)
                    report["callback_lookup_matches"][account] += int(found.get("id") == ident)
                    save()
            except Exception:
                report["callback_errors"][account] += 1

        client.events.on_message(receive)
    try:
        await asyncio.gather(*(client.connect() for client in clients))
        print("Both library-owned browser windows are open; waiting for login", flush=True)
        deadline = time.monotonic() + 900
        while any(client.state != SessionState.READY for client in clients):
            if time.monotonic() >= deadline:
                raise TimeoutError("Account login did not complete")
            await asyncio.sleep(1)
        ids = [
            await client.browser.page_evaluate(
                "() => WPP.conn.getMyUserId().toString()", page=client._context.page
            )
            for client in clients
        ]
        report["different_real_accounts"] = ids[0] != ids[1]
        assert report["different_real_accounts"], "Use two different accounts"
        del ids
        print("Two different accounts ready; incoming listeners active", flush=True)
        report["phase"] = "running"
        save()
        started = time.monotonic()
        next_recovery = args.recover_every
        import psutil

        process = psutil.Process()
        # Only browser descendants of this owned Python process are measured.
        while time.monotonic() - started < args.seconds:
            if any(client.state != SessionState.READY for client in clients):
                report["transient_outages"] += 1
                report["last_outage_states"] = [client.state.value for client in clients]
                save()
                deadline = time.monotonic() + 240
                while any(client.state != SessionState.READY for client in clients):
                    if time.monotonic() >= deadline:
                        raise TimeoutError(
                            "An account did not recover readiness within 240 seconds"
                        )
                    await asyncio.sleep(1)
            measurements = await asyncio.gather(*(client.metrics() for client in clients))
            browser_rss = sum(item["process"]["owned_browser_rss_bytes"] for item in measurements)
            report["samples"] += 1
            sample = {
                "elapsed": round(time.monotonic() - started, 2),
                "python_rss": process.memory_info().rss,
                "browser_rss": browser_rss,
                "python_handles": process.num_handles()
                if sys.platform == "win32"
                else process.num_fds(),
                "tasks": len(asyncio.all_tasks()),
                "states": [client.state.value for client in clients],
                "recovery": [client.diagnostics()["recovery"] for client in clients],
            }
            report["samples_data"].append(sample)
            report["samples_data"] = report["samples_data"][-1000:]
            report["elapsed_seconds"] = sample["elapsed"]
            if args.recover_every and sample["elapsed"] >= next_recovery:
                await clients[0].reconnect()
                assert clients[1].state == SessionState.READY
                deadline = time.monotonic() + 120
                while clients[0].state != SessionState.READY:
                    assert clients[1].state == SessionState.READY
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Manual reconnect did not regain readiness")
                    await asyncio.sleep(1)
                report["recoveries"] += 1
                next_recovery += args.recover_every
            save()
            await asyncio.sleep(
                min(args.interval, max(0, args.seconds - (time.monotonic() - started)))
            )
        report["completed"] = True
    except BaseException as error:
        report["failed_category"] = type(error).__name__
        report["final_states"] = [client.state.value for client in clients]
        report["final_diagnostics"] = [client.diagnostics() for client in clients]
        raise
    finally:
        await asyncio.gather(*(client.close() for client in clients), return_exceptions=True)
        await asyncio.gather(*(buffer.close() for buffer in buffers))
        report["closed"] = all(client.state == SessionState.CLOSED for client in clients)
        save()
        print(
            json.dumps({key: value for key, value in report.items() if key != "samples_data"}),
            flush=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", default="live-smoke-81-84")
    parser.add_argument("--second", default="live-isolation-2")
    parser.add_argument("--seconds", type=int, default=7200)
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--recover-every", type=int, default=720)
    parser.add_argument("--report", type=Path, default=ROOT / "archive/two-account-endurance.json")
    args = parser.parse_args()
    if (
        args.seconds <= 0
        or args.interval <= 0
        or args.recover_every < 0
        or args.first == args.second
    ):
        parser.error("Use different sessions and valid positive duration/interval")
    asyncio.run(run(args))
