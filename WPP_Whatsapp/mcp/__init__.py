"""Optional FastMCP integration; importing it does not require FastMCP."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from fastmcp import FastMCP

    from WPP_Whatsapp import AsyncClient

__all__ = ["create_server"]


def create_server(
    client: Optional[AsyncClient] = None,
    *,
    session: str = "mcp",
    token_directory: str = "tokens",
    wa_js_version: Optional[str] = None,
    options: Optional[dict[str, Any]] = None,
    read_only: bool = False,
    auth: Any = None,
    accounts: Optional[dict] = None,
    default_account: Optional[str] = None,
    access_policy: Optional[dict] = None,
    media_root: Optional[str] = None,
) -> FastMCP:
    """Create a FastMCP server without starting a browser or changing global logging.

    A supplied client remains owned by its caller. Otherwise the server creates
    a client per lifespan and closes it during shutdown. Authentication through
    QR remains in the visible browser; tools never return credentials or QR data.
    """
    if sys.version_info < (3, 10):
        raise RuntimeError("FastMCP requires Python 3.10+; the core library supports Python 3.9+")
    try:
        from fastmcp import FastMCP as _FastMCP  # noqa: F401
    except ModuleNotFoundError as error:
        if error.name != "fastmcp":
            raise
        raise RuntimeError('Install MCP support with: pip install "WPP_Whatsapp[mcp]"') from None
    from .server import build_server

    return build_server(
        client,
        session=session,
        token_directory=token_directory,
        wa_js_version=wa_js_version,
        options=options,
        read_only=read_only,
        auth=auth,
        accounts=accounts,
        default_account=default_account,
        access_policy=access_policy,
        media_root=media_root,
    )
