"""Local MCP application with durable events, paced sends and bounded recovery."""

from WPP_Whatsapp.mcp import create_server


def main():
    create_server(
        session="reliable-mcp",
        read_only=True,
        options={
            "eventStore": "tokens/.events/reliable-mcp.sqlite3",
            "eventBufferSize": 1000,
            "eventRetentionSeconds": 86400,
            "reconnectAttempts": 3,
            "maxConcurrentOperations": 4,
            "maxPendingOperations": 32,
            "sendRateCalls": 10,
            "sendRatePeriod": 60,
        },
    ).run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
