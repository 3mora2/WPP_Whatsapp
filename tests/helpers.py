"""Bounded synchronization helpers for tests with background work."""

import asyncio
from types import SimpleNamespace

from WPP_Whatsapp.core.lifecycle import SessionLifecycle, SessionState


def ready_context(**operations):
    async def direct(task):
        return await task

    lifecycle = SessionLifecycle()
    lifecycle.transition(SessionState.STARTING)
    lifecycle.transition(SessionState.READY)
    return SimpleNamespace(
        session="fault-test",
        options={},
        lifecycle=lifecycle,
        ThreadsafeBrowser=SimpleNamespace(create_task=direct),
        **operations,
    )


async def eventually(predicate, timeout=1):
    async def wait():
        while not predicate():
            await asyncio.sleep(0.001)

    await asyncio.wait_for(wait(), timeout)
