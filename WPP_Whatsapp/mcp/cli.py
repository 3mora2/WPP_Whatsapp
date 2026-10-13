"""Application entry point; stdout is reserved for the MCP stdio protocol."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional, Sequence

from . import create_server


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Run the WPP WhatsApp FastMCP server")
    parser.add_argument("--session", default="mcp", help="Saved WhatsApp browser profile name")
    parser.add_argument(
        "--token-directory", default="tokens", help="Private profile/storage directory"
    )
    parser.add_argument("--transport", choices=("stdio", "http"), default="stdio")
    parser.add_argument("--host", choices=("127.0.0.1", "localhost", "::1"), default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--headless", action="store_true", help="Use only with an already logged-in profile"
    )
    parser.add_argument(
        "--read-only", action="store_true", help="Omit sending and reconciliation tools"
    )
    parser.add_argument("--wa-js-version", default=None, help="WA-JS selection, e.g. bundled")
    parser.add_argument(
        "--delivery-store", default=None, help="Override the private SQLite metadata path"
    )
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    options = {"headless": args.headless}
    if args.delivery_store is not None:
        options["deliveryStore"] = args.delivery_store
    try:
        server = create_server(
            session=args.session,
            token_directory=args.token_directory,
            wa_js_version=args.wa_js_version,
            options=options,
            read_only=args.read_only,
        )
    except RuntimeError as error:
        parser.error(str(error))
    kwargs = {"host": args.host, "port": args.port} if args.transport == "http" else {}
    server.run(transport=args.transport, show_banner=False, **kwargs)
