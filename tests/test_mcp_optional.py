"""The optional server must not change the base library's Python/dependency contract."""

import builtins
from unittest.mock import patch

import pytest

from WPP_Whatsapp.mcp import create_server


def test_python39_has_actionable_mcp_version_error():
    with patch("WPP_Whatsapp.mcp.sys.version_info", (3, 9)):
        with pytest.raises(RuntimeError, match="Python 3.10"):
            create_server()


def test_missing_optional_dependency_has_actionable_install_error():
    original = builtins.__import__

    def without_fastmcp(name, *args, **kwargs):
        if name == "fastmcp":
            raise ModuleNotFoundError("missing", name="fastmcp")
        return original(name, *args, **kwargs)

    with (
        patch("WPP_Whatsapp.mcp.sys.version_info", (3, 12)),
        patch("builtins.__import__", without_fastmcp),
    ):
        with pytest.raises(RuntimeError, match=r"WPP_Whatsapp\[mcp\]"):
            create_server()
