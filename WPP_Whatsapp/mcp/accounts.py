"""Administrator-owned account configuration and verified-principal authorization."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_access_token

from .runtime import SessionRuntime

SCOPES = frozenset({"read", "send", "session", "events", "diagnostics"})


@dataclass(frozen=True)
class AccountConfig:
    session: str
    token_directory: str = "tokens"
    wa_js_version: Optional[str] = None
    options: dict[str, Any] = field(default_factory=dict)
    read_only: bool = False
    media_root: Optional[str] = None
    client: Any = field(default=None, repr=False, compare=False)


def validate_accounts(accounts: Mapping[str, AccountConfig]) -> None:
    if not accounts or len(accounts) > 32:
        raise ValueError("Configure between 1 and 32 accounts")
    profiles, clients, sessions = set(), set(), set()
    for key, config in accounts.items():
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", key):
            raise ValueError(
                "Account IDs must contain only letters, digits, underscores or hyphens"
            )
        if not isinstance(config, AccountConfig):
            raise TypeError("Accounts must contain AccountConfig values")
        if not isinstance(config.options, dict) or type(config.read_only) is not bool:
            raise TypeError("Account options must be a dict and read_only must be boolean")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", config.session):
            raise ValueError("Account session names must be safe single path segments")
        profile = str(
            Path(
                config.options.get("user_data_dir") or Path(config.token_directory) / config.session
            ).resolve()
        ).casefold()
        if config.client is not None:
            profile = str(
                Path(
                    getattr(config.client, "user_data_dir", None)
                    or Path(getattr(config.client, "token_directory", config.token_directory))
                    / config.client.session
                ).resolve()
            ).casefold()
            if id(config.client) in clients:
                raise ValueError("Accounts must not share a client")
            clients.add(id(config.client))
        if profile in profiles:
            raise ValueError("Accounts must not share a browser profile")
        profiles.add(profile)
        session = config.client.session if config.client is not None else config.session
        if session in sessions:
            raise ValueError("Accounts must not share a session name")
        sessions.add(session)


class AccountManager:
    def __init__(
        self,
        runtimes: dict[str, SessionRuntime],
        default: str,
        policy: Optional[Mapping[str, Mapping[str, set[str]]]] = None,
    ):
        self.runtimes, self.default, self.policy = runtimes, default, policy

    def allowed(self, account_id: str, scope: str) -> bool:
        if self.policy is None:
            return account_id in self.runtimes
        token = get_access_token()
        if token is None:
            return False
        principal = token.claims.get("sub") or token.client_id
        if not isinstance(principal, str):
            return False
        grants = self.policy.get(principal, {}).get(account_id, set())
        return scope in grants and f"whatsapp:{scope}" in token.scopes

    def select(self, account_id: Optional[str], scope: str = "read") -> SessionRuntime:
        key = account_id if account_id is not None else self.default
        if key not in self.runtimes or not self.allowed(key, scope):
            raise ToolError("Account or permission unavailable")
        runtime = self.runtimes[key]
        if scope == "send" and runtime.read_only:
            raise ToolError("This account is read-only")
        return runtime

    def visible(self) -> list[str]:
        return [key for key in self.runtimes if self.allowed(key, "read")]
