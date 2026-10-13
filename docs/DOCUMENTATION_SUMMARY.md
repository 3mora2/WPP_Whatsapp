# Documentation maintenance map

The [documentation index](README.md) is the navigation entry point. This page
records maintenance responsibilities rather than claiming coverage or production
validation for examples.

| Content | Source of truth |
| --- | --- |
| Installation/Python/extras | [pyproject.toml](../pyproject.toml), [installation](INSTALLATION.md) |
| Factories and resource ownership | [initializer](../WPP_Whatsapp/controllers/initializer.py), [architecture](ARCHITECTURE.md) |
| Native service names/signatures | [service definitions](../WPP_Whatsapp/core/service_registry.py), [generated inventory](API_METHODS.md) |
| User recipes | [quick start](QUICKSTART.md), [API reference](API_REFERENCE.md) |
| Optional MCP tools and transports | [server](../WPP_Whatsapp/mcp/server.py), [FastMCP guide](FASTMCP.md) |
| Timeout units and configuration | [configuration](CONFIGURATION.md) |
| Test commands and validation boundaries | [test guide](../tests/README.md) |
| Immutable release and PyPI verification | [workflow](../.github/workflows/python-publish.yml), [release verifier](../tools/verify_release.py) |
| JavaScript attribution | [provenance](../WPP_Whatsapp/js_lib/UPSTREAM.md) |

For documentation changes, validate relative links/anchors, Python snippets,
known API calls and the generated inventory with `python tools/verify_docs.py`.
This is static validation, not a live WhatsApp test. The [development guide](DEVELOPMENT.md)
lists behavioral checks. Avoid copying old test-count/coverage tables into guides;
link to an identified CI run or give a date and exact validation environment.
