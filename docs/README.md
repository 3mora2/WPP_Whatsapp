# Documentation

These guides cover version 2.4.0 and earlier compatible releases. The core supports Python 3.9+;
FastMCP requires Python 3.10+. Use installed distribution metadata for the
exact version: `python -m pip show WPP_Whatsapp`.
Features introduced in 2.2.0 are marked in their guides.
The [2.3.0 reliability guide](RELIABILITY.md) covers request identity, durable
events, bounded recovery, ACK evidence, admission and migration.

## Start here

| Task | Guide |
| --- | --- |
| Install the package and browser | [Installation](INSTALLATION.md) |
| Open a session and receive/read messages | [Quick start](QUICKSTART.md) |
| Choose actual API methods and arguments | [API reference](API_REFERENCE.md) |
| Browse every composed-service signature | [Generated service API](API_METHODS.md) |
| Configure profiles, runtime and timeouts | [Configuration](CONFIGURATION.md) |
| Connect an MCP client | [FastMCP](FASTMCP.md) |
| Recover operations, acknowledge events and inspect metrics | [Operations (2.4)](OPERATIONS.md) |
| Use typed results, support reports or bounded media | [Typed reads and media](TYPED_MEDIA.md) |
| Migrate legacy/async code and track delivery | [Architecture and migration](ARCHITECTURE.md) |
| Diagnose failures | [Troubleshooting](TROUBLESHOOTING.md), [FAQ](FAQ.md) |
| Plan ownership, callbacks and pacing | [Usage practices](BEST_PRACTICES.md), [Performance](PERFORMANCE.md) |
| Run examples or application templates | [Examples](../examples/README.md), [Scripts](../scripts/README.md) |
| Extend and validate the library | [Development](DEVELOPMENT.md), [Tests](../tests/README.md) |
| Review release changes | [Changelog](../CHANGELOG.md) |
| Review local validation evidence and test boundaries | [2.4.0 validation](VALIDATION_2.4.0.md) |

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
