# Runnable examples

Install from the checkout with `python -m pip install -e .`, then run from the
repository root. Chrome is used by default. Login uses the browser QR and a
saved profile; do not run two examples against the same profile at once.

| Program | Purpose | Run |
| --- | --- | --- |
| [receive_message.py](receive_message.py) | Receive IDs without auto-reply | `python examples/receive_message.py` |
| [get_qrcode.py](get_qrcode.py) | Browser login and a QR-ready callback | `python examples/get_qrcode.py` |
| [get_messages.py](get_messages.py) | Read a requested chat | `python examples/get_messages.py CHAT_ID` |
| [download.py](download.py) | Decode media for a requested message to a chosen output | `python examples/download.py MESSAGE_ID OUTPUT_PATH` |
| [context_manager_example.py](context_manager_example.py) | Sync or native-async reads with cleanup | `python examples/context_manager_example.py --mode async` |
| [native_async.py](native_async.py) | Native async receive/lookup | `python examples/native_async.py` |
| [mcp_server.py](mcp_server.py) | Embeddable stdio FastMCP server | `python examples/mcp_server.py` |
| [reliable_mcp.py](reliable_mcp.py) | Read-only MCP with durable events and opt-in recovery | `python examples/reliable_mcp.py` |
| [fastapi_app.py](fastapi_app.py) | Authenticated local HTTP with explicit sends and operation IDs | Set `WPP_API_TOKEN`, install `.[web]`, run `uvicorn examples.fastapi_app:create_app --factory --host 127.0.0.1` |

The MCP example requires Python 3.10+ and `python -m pip install -e ".[mcp]"`.
Other examples support the core Python 3.9+ contract. They do not automatically
send messages. Read/download examples expose the selected data locally; choose
your IDs and output location deliberately.

Use Ctrl+C to leave listeners and close their owned browser. QR callbacks should
not log the login payload. See [quick start](../docs/QUICKSTART.md),
[configuration](../docs/CONFIGURATION.md) and [application templates](../scripts/README.md).
