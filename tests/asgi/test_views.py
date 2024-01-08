import pytest
from async_asgi_testclient import TestClient

from kui.asgi import HttpView, Kui, SocketView, websocket


@pytest.mark.asyncio
async def test_http_view():
    app = Kui()

    @app.router.http("/")
    class Home(HttpView):
        @classmethod
        async def get(cls):
            return "OK"

    async with TestClient(app) as client:
        assert (await client.get("/")).content == b"OK"

        assert (await client.post("/")).status_code == 405

        assert (await client.options("/")).headers["Allow"] == "GET, OPTIONS"


@pytest.mark.asyncio
async def test_socket_view():
    app = Kui()

    @app.router.websocket("/text")
    class Text(SocketView):
        encoding = "anystr"

        async def on_receive(self, data):
            await websocket.send_text(data)

    @app.router.websocket("/json")
    class Json(SocketView):
        encoding = "json"

        async def on_receive(self, data):
            await websocket.send_json(data)

    async with TestClient(app) as client:
        async with client.websocket_connect("/text") as ws:
            await ws.send_text("OK")
            assert (await ws.receive_text()) == "OK"

        async with client.websocket_connect("/json") as ws:
            await ws.send_json("OK")
            assert (await ws.receive_json()) == "OK"
