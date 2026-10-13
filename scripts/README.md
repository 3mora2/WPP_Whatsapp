# Application templates

These are editable applications, not additional library APIs or production
services. Install with `python -m pip install -e .` and run from the repository
root. Review their recipient access, sample business responses and storage
requirements before enabling replies.

| Program | Purpose | Behavior |
| --- | --- | --- |
| [advanced_message_handler.py](advanced_message_handler.py) | Async legacy command routing/middleware | Replies to supported commands from incoming direct messages. |
| [customer_service_bot.py](customer_service_bot.py) | Sync callback/FAQ/ticket example | Replies using sample business text; tickets/analytics are in memory. |
| [bulk_sender.py](bulk_sender.py) | Native async paced sending with durable receipts | Requires recipients, content and a stable operation-prefix argument. |

```bash
python scripts/advanced_message_handler.py
python scripts/customer_service_bot.py
python scripts/bulk_sender.py --help
```

The first two commands start listeners which can send replies. The bulk
template does not send on connection events and never automatically retries an
uncertain send. Reuse its operation prefix and recipient ordering when resuming
the same intended batch. Changing an operation ID removes duplicate protection.
Local pacing is not a platform quota or a guarantee against account restrictions.

Keep the browser profile and any delivery database private. Close the owning
context before reuse. Replace sample FAQ/SLA/contact text in the customer-service
template; it does not connect to an actual ticketing or human-handoff system.

See [basic examples](../examples/README.md), [API reference](../docs/API_REFERENCE.md),
[delivery semantics](../docs/ARCHITECTURE.md#sending-and-uncertain-results) and
[usage practices](../docs/BEST_PRACTICES.md).
