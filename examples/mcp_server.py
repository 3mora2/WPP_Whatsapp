"""Run with WPP_Whatsapp[mcp] (2.1+) or a source install: pip install -e '.[mcp]'."""

from WPP_Whatsapp.mcp import create_server

mcp = create_server(session="mybot")

if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
