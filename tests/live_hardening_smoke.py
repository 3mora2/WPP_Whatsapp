"""Opt-in live evidence recovery. Sends require explicit authorization for one text/file.

Fixed durable operation IDs prevent reruns from sending again. Reports omit IDs,
recipients and message bodies. Use only after other tests release this profile.
"""

import argparse
import asyncio
import hashlib
import json
import logging
import sys
import time
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from WPP_Whatsapp import AsyncClient  # noqa: E402
from WPP_Whatsapp.core.delivery import DeliveryTracker  # noqa: E402
from WPP_Whatsapp.core.delivery_models import DeliveryState  # noqa: E402
from WPP_Whatsapp.core.delivery_store import SQLiteDeliveryStore  # noqa: E402
from WPP_Whatsapp.core.errors import DeliveryUncertainError  # noqa: E402
from WPP_Whatsapp.core.metrics import process_snapshot  # noqa: E402

TEXT = "اختبار استرجاع العمليات WPP_Whatsapp 2.4.0"
FILE_BYTES = b"WPP_Whatsapp 2.4.0 evidence test\n"


class FaultStore(SQLiteDeliveryStore):
    def __init__(self, *args):
        super().__init__(*args)
        self.armed = None
        self.failures = 0

    def save(self, receipt):
        if self.armed == receipt.operation_id and receipt.state == DeliveryState.CONFIRMED:
            self.armed = None
            self.failures += 1
            raise OSError("Injected receipt commit failure")
        super().save(receipt)


async def run(args):
    logging.getLogger("WPP_Whatsapp").setLevel(logging.WARNING)
    if args.after_endurance:
        deadline = time.monotonic() + 8500
        print("Waiting for the owned two-account endurance run to release its profiles", flush=True)
        while True:
            try:
                result = json.loads(args.after_endurance.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError):
                result = {}
            if result.get("failed_category"):
                raise RuntimeError("Endurance failed; no authorized sends were attempted")
            if result.get("completed") and result.get("closed"):
                break
            if time.monotonic() >= deadline:
                raise TimeoutError("Endurance did not release its profiles")
            await asyncio.sleep(5)
    ledger = ROOT / "tokens/.deliveries/live-hardening-240.sqlite3"
    client = AsyncClient(
        args.session,
        token_directory=str(ROOT / "tokens"),
        autoClose=0,
        logQR=False,
        deliveryStore=str(ledger),
    )
    report = {
        "candidate": "2.4.0",
        "new_send_attempts": 0,
        "commit_failures_injected": 0,
        "evidence_recoveries": 0,
    }
    roots = {}
    try:
        await asyncio.wait_for(client.connect(), 120)
        roots = dict(client.browser.process_roots)
        chat = await client.browser.page_evaluate(
            """async () => {
            const chats = await WPP.chat.list({onlyGroups:true,count:100});
            return chats.find(c => !c.unreadCount && c.lastReceivedKey &&
                c.groupMetadata?.groupType !== 'COMMUNITY')?.id.toString();
        }""",
            page=client._context.page,
        )
        if not chat:
            raise RuntimeError("No already-read group is available")
        history = await client.messages.get_messages(chat, {"count": 10})
        assert history, "Already-read history was empty"
        found = await client.messages.get_message(history[0]["id"])
        report["already_read_history_count"] = len(history)
        report["history_lookup_matches"] = found.get("id") == history[0]["id"]
        assert report["history_lookup_matches"]
        del history, found, chat
        if args.allow_text_and_file:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            source = args.report.parent / "wpp-whatsapp-240-test.txt"
            source.write_bytes(FILE_BYTES)
            destination = args.report.parent / "wpp-whatsapp-240-received.txt"
            for kind in ("text", "file"):
                operation_id = "live-2.4.0-" + kind + "-evidence-20261014"
                store = FaultStore(ledger, args.session)
                tracker = DeliveryTracker(namespace=args.session, store=store)
                client._context._delivery_tracker = tracker
                previous = await tracker.get_async(operation_id)
                if previous is None:
                    store.armed = operation_id
                    report["new_send_attempts"] += 1
                    try:
                        if kind == "text":
                            await client.messages.send_text(
                                args.recipient + "@c.us", TEXT, operation_id=operation_id
                            )
                        else:
                            await client.messages.send_media(
                                args.recipient + "@c.us",
                                str(source),
                                operation_id=operation_id,
                                max_bytes=1024,
                            )
                    except DeliveryUncertainError:
                        pass
                    assert store.failures == 1, "Did not reach the injected receipt commit boundary"
                    report["commit_failures_injected"] += store.failures
                await tracker.aclose()
                # Reopen metadata from disk; recovery never calls a send operation.
                reopened = DeliveryTracker(ledger, args.session)
                client._context._delivery_tracker = reopened
                expected = await reopened.expected_async(operation_id)
                assert expected is not None, "Missing persisted pre-dispatch evidence"
                deadline = time.monotonic() + 30
                while True:
                    try:
                        receipt = await client.messages.recover(operation_id)
                        break
                    except ValueError:
                        if time.monotonic() >= deadline:
                            raise
                        await asyncio.sleep(0.5)
                assert receipt.message_id == expected.message_id
                assert await client.messages.recover(operation_id) == receipt
                report["evidence_recoveries"] += 1
                status = await client.messages.wait_for_delivery(
                    operation_id, target="server", timeout=30
                )
                report[kind + "_ack"] = status["ack"]
                report[kind + "_delivered"] = status["delivered"]
                if kind == "file":
                    if not destination.exists():
                        downloaded = await client.messages.download_media_to(
                            receipt.message_id, str(destination), max_bytes=1024
                        )
                        assert downloaded["sha256"] == hashlib.sha256(FILE_BYTES).hexdigest()
                    assert destination.read_bytes() == FILE_BYTES
                    report["file_download_matches"] = True
                await reopened.aclose()
        report["owned_browser_measured"] = (await client.metrics())["process"][
            "owned_browser_processes"
        ] > 0
        assert report["owned_browser_measured"], "Owned browser processes were not measured"
        report["passed"] = True
    except BaseException as error:
        report["failed_category"] = type(error).__name__
        raise
    finally:
        # Keep descendant identities before their parent exits, so an orphan
        # cannot disappear from the owned-browser cleanup check.
        for pid, created in list(roots.items()):
            try:
                parent = psutil.Process(pid)
                if parent.create_time() == created:
                    for child in parent.children(recursive=True):
                        roots[child.pid] = child.create_time()
            except psutil.Error:
                continue
        await client.close()
        deadline = time.monotonic() + 10
        while process_snapshot(roots)["owned_browser_processes"] and time.monotonic() < deadline:
            await asyncio.sleep(0.2)
        report["owned_browser_processes_after_close"] = process_snapshot(roots)[
            "owned_browser_processes"
        ]
        if report["owned_browser_processes_after_close"]:
            report["passed"] = False
            report["failed_category"] = "OwnedBrowserLeak"
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", default="live-smoke-81-84")
    parser.add_argument("--allow-text-and-file", action="store_true")
    parser.add_argument("--recipient")
    parser.add_argument("--after-endurance", type=Path)
    parser.add_argument("--report", type=Path, default=ROOT / "archive/live-hardening-240.json")
    args = parser.parse_args()
    if args.allow_text_and_file and (not args.recipient or not args.recipient.isdecimal()):
        parser.error("Explicit send authorization requires an international numeric recipient")
    asyncio.run(run(args))
