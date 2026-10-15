"""Local delivery administration. No command ever resends a message."""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from dataclasses import asdict
from pathlib import Path

from .delivery_store import SQLiteDeliveryStore


async def _recover(args):
    from .client import AsyncClient

    async with AsyncClient(
        args.namespace,
        token_directory=args.token_directory,
        deliveryStore=str(args.store.resolve()),
        logQR=False,
        autoClose=0,
    ) as client:
        return asdict(await client.messages.recover(args.operation_id))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--namespace", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list")
    listing.add_argument("--state", choices=("pending", "confirmed", "failed", "unknown"))
    listing.add_argument("--after", default="")
    listing.add_argument("--limit", type=int, default=50)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("operation_id")
    compact = commands.add_parser("compact")
    compact.add_argument("--older-than-days", type=float, required=True)
    compact.add_argument("--apply", action="store_true", help="Default is a count-only preview")
    recover = commands.add_parser("recover")
    recover.add_argument("operation_id")
    recover.add_argument("--token-directory", default="tokens")
    args = parser.parse_args(argv)
    if not args.store.is_file():
        parser.error("The delivery store must already exist")
    if args.command == "recover":
        result = asyncio.run(_recover(args))
    else:
        store = SQLiteDeliveryStore(args.store, args.namespace)
        try:
            if args.command == "list":
                result = store.list_operations(state=args.state, after=args.after, limit=args.limit)
            elif args.command == "inspect":
                receipt, expected = store.get(args.operation_id), store.expected(args.operation_id)
                result = {
                    "receipt": asdict(receipt) if receipt else None,
                    "expected": asdict(expected) if expected else None,
                }
            else:
                import math

                if not math.isfinite(args.older_than_days) or args.older_than_days < 0:
                    parser.error("Age must be finite and nonnegative")
                before = time.time() - args.older_than_days * 86400
                result = {
                    "count": store.compact(before, dry_run=not args.apply),
                    "applied": args.apply,
                }
        finally:
            store.close()
    print(json.dumps(result))


if __name__ == "__main__":
    main()
