# Installation

## Requirements

Use Python 3.9+ for the core; use Python 3.10+ for FastMCP. Chrome is selected
by default. Node.js 18+ is needed for executable JavaScript **development tests**,
not for ordinary library installation.

## pip

```bash
python -m venv .venv
```

Activate with `.venv\Scripts\Activate.ps1` in PowerShell or
`source .venv/bin/activate` in a POSIX shell, then install the desired extras:

```bash
python -m pip install --upgrade pip
python -m pip install --upgrade WPP_Whatsapp
python -m pip install --upgrade "WPP_Whatsapp[mcp]"
python -m pip install --upgrade "WPP_Whatsapp[stealth]"
```

Extras can be combined: `WPP_Whatsapp[mcp,stealth]`. They are optional; MCP
does not raise the core package's minimum Python version. Attempting to start
the MCP server on Python 3.9 produces a Python-version error.

## uv

In your own project, use `uv add WPP_Whatsapp` or `uv add "WPP_Whatsapp[mcp]"`.
In a repository checkout, use:

```bash
uv sync --extra dev --extra mcp --python 3.12
uv run wpp-whatsapp-mcp --help
```

For pip-based development: `python -m pip install -e ".[dev,mcp]"`.

## Browser

Install Chrome normally, or install Playwright Chromium:

```bash
python -m playwright install chromium
```

For a Linux host requiring browser system libraries, Playwright also provides
`python -m playwright install --with-deps chromium` (requires host package permissions).
Select the installed Playwright browser explicitly:

```python
from WPP_Whatsapp import Create

with Create("mybot", browser="chromium", channel=None, autoClose=0) as client:
    print("Chats:", len(client.listChats({"count": 5})))
```

For `AsyncClient`, `channel=None` selects Playwright Chromium. Saved profiles
need a writable storage directory; they are directories, not `.token` files.
See [configuration](CONFIGURATION.md) for profile ownership and paths.

## Optional media tooling and verification

Install FFmpeg on PATH for GIF/video conversion paths that require it. It is
not required for basic text/history/MCP operations. Do not assume every media
operation has the same file-size or format limits.

```bash
python -m pip show WPP_Whatsapp
python -m WPP_Whatsapp.mcp --help
```

Use the interpreter where you installed the package. See [quick start](QUICKSTART.md)
for login and [troubleshooting](TROUBLESHOOTING.md) for interpreter/browser errors.
