# Documentation

These guides cover the 2.1 release line. The core supports Python 3.9+;
FastMCP requires Python 3.10+. Use installed distribution metadata for the
exact version: `python -m pip show WPP_Whatsapp`.

## Start here

| Task | Guide |
| --- | --- |
| Install the package and browser | [Installation](INSTALLATION.md) |
| Open a session and receive/read messages | [Quick start](QUICKSTART.md) |
| Choose actual API methods and arguments | [API reference](API_REFERENCE.md) |
| Browse every composed-service signature | [Generated service API](API_METHODS.md) |
| Configure profiles, runtime and timeouts | [Configuration](CONFIGURATION.md) |
| Connect an MCP client | [FastMCP](FASTMCP.md) |
| Migrate legacy/async code and track delivery | [Architecture and migration](ARCHITECTURE.md) |
| Diagnose failures | [Troubleshooting](TROUBLESHOOTING.md), [FAQ](FAQ.md) |
| Plan ownership, callbacks and pacing | [Usage practices](BEST_PRACTICES.md), [Performance](PERFORMANCE.md) |
| Run examples or application templates | [Examples](../examples/README.md), [Scripts](../scripts/README.md) |
| Extend and validate the library | [Development](DEVELOPMENT.md), [Tests](../tests/README.md) |
| Review release changes | [Changelog](../CHANGELOG.md) |

## Contributing

Keep examples aligned with the actual signatures and distinguish factories,
clients and services. Run `python tools/verify_docs.py` after editing guides;
regenerate the inventory with `python tools/verify_docs.py --write-api` when
the service surface changes. These checks do not launch a browser or send messages.
Run relevant behavioral tests before changing API or lifecycle behavior.

The Python project uses [MIT](../LICENSE). Bundled upstream JavaScript has
[separate licenses and provenance](../WPP_Whatsapp/js_lib/UPSTREAM.md).
For support, include a minimal reproducer and sanitized version/state details
in a [GitHub issue](https://github.com/3mora2/WPP_Whatsapp/issues).
