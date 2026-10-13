"""Application entry point; stdout is reserved for the MCP stdio protocol."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional, Sequence

from . import create_server


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Run the WPP WhatsApp FastMCP server")
    parser.add_argument("--session", default="mcp", help="Saved WhatsApp browser profile name")
    parser.add_argument(
        "--token-directory", default="tokens", help="Private profile/storage directory"
    )
    parser.add_argument("--transport", choices=("stdio", "http"), default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--headless", action="store_true", help="Use only with an already logged-in profile"
    )
    parser.add_argument(
        "--read-only", action="store_true", help="Omit sending and reconciliation tools"
    )
    parser.add_argument("--wa-js-version", default=None, help="WA-JS selection, e.g. bundled")
    parser.add_argument("--media-root", help="Existing private directory for media files")
    parser.add_argument(
        "--accounts-config", type=Path, help="Administrator JSON map of account configs"
    )
    parser.add_argument("--default-account", help="Default ID in --accounts-config")
    parser.add_argument(
        "--access-policy", type=Path, help="JSON map: verified subject -> account -> scopes"
    )
    parser.add_argument(
        "--auth-jwks-uri", help="HTTPS JWKS endpoint for HTTP bearer JWT validation"
    )
    parser.add_argument("--auth-issuer", help="Required JWT issuer")
    parser.add_argument("--auth-audience", help="Required JWT audience")
    parser.add_argument(
        "--delivery-store", default=None, help="Override the private SQLite metadata path"
    )
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    auth_fields = (args.auth_jwks_uri, args.auth_issuer, args.auth_audience, args.access_policy)
    if any(auth_fields) and (not all(auth_fields) or args.transport != "http"):
        parser.error("HTTP authentication requires JWKS URI, issuer, audience and access policy")
    if args.host not in {"127.0.0.1", "localhost", "::1"} and not all(auth_fields):
        parser.error("Non-loopback HTTP requires verified authentication and an access policy")
    if args.auth_jwks_uri and not args.auth_jwks_uri.startswith("https://"):
        parser.error("JWKS URI must use HTTPS")
    auth, accounts, access_policy = None, None, None

    def load_config(path):
        if path.stat().st_size > 1024 * 1024:
            raise ValueError("Configuration exceeds size limit")
        return json.loads(path.read_text(encoding="utf-8"))

    try:
        if args.accounts_config is not None:
            from .accounts import AccountConfig

            definitions = load_config(args.accounts_config)
            if any("client" in value for value in definitions.values()):
                raise ValueError("CLI accounts cannot inject clients")
            accounts = {key: AccountConfig(**value) for key, value in definitions.items()}
        if args.access_policy is not None:
            from fastmcp.server.auth import JWTVerifier

            access_policy = load_config(args.access_policy)
            auth = JWTVerifier(
                jwks_uri=args.auth_jwks_uri,
                issuer=args.auth_issuer,
                audience=args.auth_audience,
                algorithm="RS256",
            )
    except (OSError, ValueError, TypeError, AttributeError, ImportError) as error:
        parser.error(f"Invalid MCP configuration ({type(error).__name__})")
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
            accounts=accounts,
            default_account=args.default_account,
            access_policy=access_policy,
            media_root=args.media_root,
            auth=auth,
        )
    except (RuntimeError, ValueError, TypeError) as error:
        parser.error(str(error))
    kwargs = {"host": args.host, "port": args.port} if args.transport == "http" else {}
    server.run(transport=args.transport, show_banner=False, **kwargs)
