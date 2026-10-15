"""Generated types follow runtime signatures and reject invalid public usage."""

import ast
import importlib.util
import inspect
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import WPP_Whatsapp
from WPP_Whatsapp.core.service_registry import service_definitions
from WPP_Whatsapp.core.services import ServiceHub

PACKAGE_ROOT = Path(WPP_Whatsapp.__file__).resolve().parent


def test_generated_sync_async_signatures_match_every_runtime_operation():
    tree = ast.parse((PACKAGE_ROOT / "core/service_types.pyi").read_text(encoding="utf-8"))
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    hub = ServiceHub(SimpleNamespace())
    for definition in service_definitions():
        service = getattr(hub, definition.name)
        sync = {
            node.name: node
            for node in classes["Sync" + definition.name.title()].body
            if isinstance(node, ast.FunctionDef)
        }
        native = {
            node.name: node
            for node in classes["Async" + definition.name.title()].body
            if isinstance(node, ast.AsyncFunctionDef)
        }
        assert sync.keys() == native.keys()
        for name in definition.operations():
            parameters = inspect.signature(getattr(service, name)).parameters
            stub = native[name].args
            names = [node.arg for node in [*stub.posonlyargs, *stub.args]][1:]
            if stub.vararg:
                names.append(stub.vararg.arg)
            names += [node.arg for node in stub.kwonlyargs]
            if stub.kwarg:
                names.append(stub.kwarg.arg)
            assert names == list(parameters), (definition.name, name)
            assert ast.dump(sync[name].args) == ast.dump(native[name].args)


@pytest.mark.skipif(importlib.util.find_spec("mypy") is None, reason="Development Mypy required")
def test_public_native_and_sync_types_accept_valid_calls_and_reject_invalid_calls(tmp_path):
    valid = tmp_path / "valid.py"
    valid.write_text(
        """
from typing import Optional
from typing_extensions import assert_type
from WPP_Whatsapp import AsyncClient, Whatsapp, DeliveryReceipt, Message
async def use(native: AsyncClient, legacy: Whatsapp) -> None:
    assert_type(await native.messages.send_text("chat", "body"), DeliveryReceipt)
    assert_type(legacy.services.messages.send_text("chat", "body"), DeliveryReceipt)
    assert_type(await native.typed.get_message("full-id"), Optional[Message])
    assert_type(legacy.services.typed.get_message("full-id"), Optional[Message])
    await native.groups.get_group_members("group")
""",
        encoding="utf-8",
    )
    command = [sys.executable, "-m", "mypy", "--follow-imports=silent", "--no-incremental"]
    result = subprocess.run(command + [str(valid)], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    invalid = tmp_path / "invalid.py"
    invalid.write_text(
        """
from WPP_Whatsapp import AsyncClient, Whatsapp
async def use(native: AsyncClient, legacy: Whatsapp) -> None:
    await native.messages.send_text(123, "body")
    legacy.services.messages.send_text("chat", 123)
    await native.services.groups.nonexistent_operation()
""",
        encoding="utf-8",
    )
    result = subprocess.run(command + [str(invalid)], capture_output=True, text=True, timeout=60)
    assert result.returncode != 0
    assert result.stdout.count("[arg-type]") == 2 and "[attr-defined]" in result.stdout
