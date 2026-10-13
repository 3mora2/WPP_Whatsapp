# WPP_Whatsapp package

Public entry points: `Create`, `Whatsapp`, `MultiCreate`, `AsyncClient`,
`DeliveryReceipt`, `DeliveryState` and `SessionState`.

`Create` returns a legacy client from `start()` or its context manager. Native
asyncio code uses `AsyncClient` and composed services. Synchronous callbacks
run off the browser loop; async callbacks must await async operations.
Profiles have one owner and cleanup is idempotent.

Optional FastMCP support is installed with `WPP_Whatsapp[mcp]` on Python 3.10+.
Run `wpp-whatsapp-mcp` or `python -m WPP_Whatsapp.mcp`. The core supports Python 3.9+.

See the [project documentation](https://github.com/3mora2/WPP_Whatsapp/tree/main/docs),
[API reference](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/API_REFERENCE.md),
and [FastMCP guide](https://github.com/3mora2/WPP_Whatsapp/blob/main/docs/FASTMCP.md).
Bundled JavaScript provenance and licenses are in [js_lib/UPSTREAM.md](js_lib/UPSTREAM.md).
