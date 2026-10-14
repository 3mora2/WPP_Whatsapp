"""The HTTP example authenticates before opening a browser or sending anything."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("fastmcp")

from fastapi.testclient import TestClient

from examples.fastapi_app import create_app
from tests.test_mcp_development import EventClient


def test_http_template_is_lazy_authenticated_and_conflict_aware():
    fake = EventClient("web-example")
    app = create_app(fake, token="synthetic-token")
    with TestClient(app) as client:
        assert client.get("/health").status_code == 401
        fake.connect.assert_not_called()
        client.headers["Authorization"] = "Bearer synthetic-token"
        assert client.get("/health").status_code == 200
        assert client.post("/session/connect").status_code == 200
        request = {"chat_id": "synthetic@c.us", "text": "test", "operation_id": "one"}
        first = client.post("/messages", json=request)
        assert first.status_code == 200
        assert client.post("/messages", json=request).json() == first.json()
        assert client.post("/messages", json={**request, "text": "changed"}).status_code == 409
        fake.context.sendText_.assert_awaited_once()
    fake.close.assert_not_called()  # Supplied clients remain caller-owned.
    with TestClient(create_app(token="synthetic-token")) as client:
        client.headers["Authorization"] = "Bearer synthetic-token"
        assert client.get("/messages", params={"chat_id": "synthetic@c.us"}).status_code == 503
