"""Delivery recovery, durable event consumers and numeric operational metrics."""

from dataclasses import asdict
from typing import Annotated, Literal, Optional

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import Field

from WPP_Whatsapp.core.consumers import DurableConsumer, EventLease
from WPP_Whatsapp.core.metrics import prometheus

from .tool_api import READ, SESSION, Identifier, Limit, OperationId, _call, _runtime


def register_operations(server, *, read_only):
    def consumer(runtime, ident):
        if runtime.events.store is None:
            raise ToolError("Configure eventStore for durable consumers first")
        return DurableConsumer(runtime.events.store, ident)

    @server.tool(annotations=READ)
    async def whatsapp_list_operations(
        ctx: Context,
        state: Optional[Literal["pending", "confirmed", "unknown", "failed"]] = None,
        after: str = "",
        limit: Limit = 50,
        account_id: Optional[Identifier] = None,
    ) -> list[dict]:
        """List bounded delivery metadata; never includes message contents or resends."""
        runtime = _runtime(ctx, account_id, "read")

        async def listing():
            tracker = (
                runtime.client.messages.deliveries if runtime.status()["ready"] else runtime.tracker
            )
            if tracker is None:
                raise ToolError("Connect first to access delivery metadata")
            runtime.tracker = tracker
            return await tracker.list_operations(state=state, after=after, limit=limit)

        return await _call(runtime, listing, ready=False)

    @server.tool(annotations={**READ, "openWorldHint": False})
    async def whatsapp_metrics(ctx: Context, account_id: Optional[Identifier] = None) -> str:
        """Prometheus numeric metrics, without account/message labels or message contents."""
        runtime = _runtime(ctx, account_id, "diagnostics")

        async def measure():
            return prometheus(await runtime.client.metrics())

        return await _call(runtime, measure, ready=False)

    @server.tool(annotations={**SESSION, "openWorldHint": False})
    async def whatsapp_claim_event(
        ctx: Context,
        consumer_id: OperationId,
        account_id: Optional[Identifier] = None,
    ) -> dict:
        """Lease one durable event for 60s; acknowledge explicitly. Side effects need deduplication."""
        runtime = _runtime(ctx, account_id, "events")

        async def claim():
            result = await consumer(runtime, consumer_id).claim()
            return {
                "lease": asdict(result["lease"]) if result["lease"] else None,
                "lost": result["lost"],
                "lost_total": result["lost_total"],
            }

        return await _call(runtime, claim, ready=False)

    @server.tool(annotations={**SESSION, "openWorldHint": False})
    async def whatsapp_complete_event(
        ctx: Context,
        consumer_id: OperationId,
        sequence: Annotated[int, Field(ge=1)],
        token: Annotated[str, Field(min_length=32, max_length=32)],
        outcome: Literal["ack", "fail", "renew"],
        account_id: Optional[Identifier] = None,
    ) -> dict:
        """Acknowledge or retry a valid lease. Stale tokens cannot advance the consumer."""
        runtime = _runtime(ctx, account_id, "events")

        async def finish():
            worker = consumer(runtime, consumer_id)
            lease = EventLease(consumer_id, sequence, token, 0, {})
            await getattr(worker, outcome)(lease)
            return {"completed": True}

        return await _call(runtime, finish, ready=False)

    @server.tool(annotations=READ)
    async def whatsapp_dead_letters(
        ctx: Context,
        consumer_id: OperationId,
        after: Annotated[int, Field(ge=0)] = 0,
        limit: Limit = 50,
        account_id: Optional[Identifier] = None,
    ) -> list[dict]:
        """Read private events that exhausted retries. Never automatically replays their effects."""
        runtime = _runtime(ctx, account_id, "events")
        return await _call(
            runtime,
            lambda: consumer(runtime, consumer_id).dead_letters(after=after, limit=limit),
            ready=False,
        )

    if read_only:
        return

    @server.tool(annotations={**SESSION, "idempotentHint": True})
    async def whatsapp_recover_delivery(
        ctx: Context,
        operation_id: OperationId,
        account_id: Optional[Identifier] = None,
    ) -> dict:
        """Confirm an uncertain operation by its persisted outgoing key/type/chat. Never sends."""
        runtime = _runtime(ctx, account_id, "send")

        async def recover():
            return asdict(await runtime.client.messages.recover(operation_id))

        return await _call(runtime, recover)
