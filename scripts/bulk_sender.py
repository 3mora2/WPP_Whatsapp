"""Paced sends with stable operation IDs and a durable ledger; no automatic retries."""

import argparse
import asyncio

from WPP_Whatsapp import AsyncClient
from WPP_Whatsapp.core.errors import DeliveryUncertainError
from WPP_Whatsapp.utils.rate_limiter import RateLimiter


async def send_batch(args):
    limiter = RateLimiter(calls=20, period=60, delay_between_calls=2)
    async with AsyncClient(
        args.session,
        autoClose=0,
        deliveryStore=args.delivery_store,
    ) as client:
        for index, recipient in enumerate(args.recipients):
            operation_id = f"{args.operation_prefix}:{index}"
            try:
                async with limiter:
                    receipt = await client.messages.send_text(
                        recipient, args.text, operation_id=operation_id
                    )
                print(operation_id, receipt.state.value)
            except DeliveryUncertainError:
                print("Unknown send:", operation_id, "Inspect/reconcile before continuing.")
                raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recipients", nargs="+", help="Explicit WhatsApp chat IDs")
    parser.add_argument("--text", required=True)
    parser.add_argument(
        "--operation-prefix",
        required=True,
        help="Stable identifier for this batch; reuse with the same recipient order",
    )
    parser.add_argument("--session", default="bulk-example")
    parser.add_argument("--delivery-store", default="tokens/bulk-example.sqlite3")
    args = parser.parse_args()
    if not args.text.strip() or not args.operation_prefix.strip():
        parser.error("Text and operation prefix must not be blank")
    if len(f"{args.operation_prefix}:{len(args.recipients) - 1}") > 128:
        parser.error("Operation IDs must fit within 128 characters")
    asyncio.run(send_batch(args))


if __name__ == "__main__":
    main()
