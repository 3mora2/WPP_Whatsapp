"""Run after installing the source checkout with pip install -e '.[mcp]'."""

from WPP_Whatsapp.mcp import create_server

mcp = create_server(session="mybot")

if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
