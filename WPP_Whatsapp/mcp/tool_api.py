"""Common schemas, account selection and sanitized tool failures."""

from __future__ import annotations

from typing import Annotated, Awaitable, Callable, TypeVar

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import Field

from WPP_Whatsapp.core.errors import SessionNotReadyError

from .runtime import SessionRuntime

Identifier = Annotated[str, Field(min_length=1, max_length=512)]
OperationId = Annotated[str, Field(min_length=1, max_length=128)]
Limit = Annotated[int, Field(ge=1, le=200)]
T = TypeVar("T")
READ = {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True}
SESSION = {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}


def _runtime(ctx: Context, account_id=None, scope="read") -> SessionRuntime:
    return ctx.lifespan_context["accounts"].select(account_id, scope)


async def _call(
    runtime: SessionRuntime, action: Callable[[], Awaitable[T]], *, ready=True, exclusive=False
) -> T:
    try:
        return await runtime.run(action, ready=ready, exclusive=exclusive)
    except SessionNotReadyError:
        raise ToolError("Connect WhatsApp and finish login in the browser first") from None
    except ToolError:
        raise
    except Exception as error:
        raise ToolError(f"WhatsApp operation failed ({type(error).__name__})") from None


def _identifier(value: str) -> str:
    if not value.strip():
        raise ToolError("Identifiers must not be blank")
    return value
