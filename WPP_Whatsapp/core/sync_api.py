"""Shared implementation for reviewed legacy synchronous forwarding methods."""

from __future__ import annotations

import inspect
from functools import wraps


def sync_wrapper(async_name: str):
    """Preserve the declaration's signature/docstring and centralize dispatch.

    Apply only to wrappers that forward every argument unchanged, with the
    final timeout parameter used exclusively by run_threadsafe.
    """

    def decorate(declaration):
        signature = inspect.signature(declaration)

        @wraps(declaration)
        def execute(self, *args, **kwargs):
            bound = signature.bind(self, *args, **kwargs)
            bound.apply_defaults()
            values = dict(bound.arguments)
            values.pop("self")
            timeout = values.pop("timeout")
            return self.ThreadsafeBrowser.run_threadsafe(
                getattr(self, async_name), *values.values(), timeout_=timeout
            )

        execute.__signature__ = signature
        return execute

    return decorate
