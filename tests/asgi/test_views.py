import httpx
import pytest

from kui.asgi import HttpView, Kui, SocketView, websocket


@pytest.mark.asyncio
async def test_http_view():
    app = Kui()

    @app.router.http("/")
    class Home(HttpView):
        @classmethod
        async def get(cls):
            return "OK"

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/")
        assert response.content == b"OK"

        response = await client.post("/")
        assert response.status_code == 405

        response = await client.options("/")
        assert response.headers["Allow"] == "GET, OPTIONS"


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
