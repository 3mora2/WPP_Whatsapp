"""Load the vendored WPPConnect bundle and the Python compatibility bridge."""
from pathlib import Path

_JS_DIR = Path(__file__).resolve().parents[2] / "js_lib"
WAPI = "\n".join(
    (_JS_DIR / name).read_text(encoding="utf-8")
    for name in ("wapi.js", "message_compat.js")
)
