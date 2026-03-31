import httpx
import pytest
from httpx_ws import WebSocketDisconnect, aconnect_ws
from httpx_ws.transport import ASGIWebSocketTransport

from kui.asgi import Kui, SocketView, websocket


@pytest.mark.asyncio
async def test_socket_view_text_encoding_receives_text_message():
    app = Kui()

    @app.router.websocket("/")
    class TextSocket(SocketView):
        encoding = "text"

        async def on_receive(self, data):
            await websocket.send_text(data.upper())

    async with httpx.AsyncClient(transport=ASGIWebSocketTransport(app=app)) as client:
        async with aconnect_ws("http://testserver/", client=client) as ws:
            await ws.send_text("ping")

            assert await ws.receive_text() == "PING"


@pytest.mark.asyncio
async def test_socket_view_bytes_encoding_receives_bytes_message():
    app = Kui()

    @app.router.websocket("/")
    class BytesSocket(SocketView):
        encoding = "bytes"

        async def on_receive(self, data):
            await websocket.send_bytes(data.upper())

    async with httpx.AsyncClient(transport=ASGIWebSocketTransport(app=app)) as client:
        async with aconnect_ws("http://testserver/", client=client) as ws:
            await ws.send_bytes(b"ping")

            assert await ws.receive_bytes() == b"PING"


@pytest.mark.asyncio
async def test_socket_view_json_encoding_receives_json_message():
    app = Kui()

    @app.router.websocket("/")
    class JsonSocket(SocketView):
        encoding = "json"

        async def on_receive(self, data):
            await websocket.send_json({"received": data})

    async with httpx.AsyncClient(transport=ASGIWebSocketTransport(app=app)) as client:
        async with aconnect_ws("http://testserver/", client=client) as ws:
            await ws.send_json({"message": "ping"})

            assert await ws.receive_json() == {"received": {"message": "ping"}}


@pytest.mark.asyncio
async def test_socket_view_text_encoding_rejects_bytes_message():
    app = Kui()

    @app.router.websocket("/")
    class TextSocket(SocketView):
        encoding = "text"

        async def on_receive(self, data):
            await websocket.send_text(data.upper())

    async with httpx.AsyncClient(transport=ASGIWebSocketTransport(app=app)) as client:
        async with aconnect_ws("http://testserver/", client=client) as ws:
            await ws.send_bytes(b"ping")

            with pytest.raises(WebSocketDisconnect) as exc_info:
                await ws.receive()

    assert exc_info.value.code == 1003


@pytest.mark.asyncio
async def test_socket_view_bytes_encoding_rejects_text_message():
    app = Kui()

    @app.router.websocket("/")
    class BytesSocket(SocketView):
        encoding = "bytes"

        async def on_receive(self, data):
            await websocket.send_bytes(data.upper())

    async with httpx.AsyncClient(transport=ASGIWebSocketTransport(app=app)) as client:
        async with aconnect_ws("http://testserver/", client=client) as ws:
            await ws.send_text("ping")

            with pytest.raises(WebSocketDisconnect) as exc_info:
                await ws.receive()

    assert exc_info.value.code == 1003


@pytest.mark.asyncio
async def test_socket_view_json_encoding_rejects_invalid_json():
    app = Kui()

    @app.router.websocket("/")
    class JsonSocket(SocketView):
        encoding = "json"

        async def on_receive(self, data):
            await websocket.send_json({"received": data})

    async with httpx.AsyncClient(transport=ASGIWebSocketTransport(app=app)) as client:
        async with aconnect_ws("http://testserver/", client=client) as ws:
            await ws.send_text("{")

            with pytest.raises(WebSocketDisconnect) as exc_info:
                await ws.receive()

    assert exc_info.value.code == 1003


@pytest.mark.asyncio
async def test_socket_view_json_encoding_receives_json_bytes_message():
    app = Kui()

    @app.router.websocket("/")
    class JsonSocket(SocketView):
        encoding = "json"

        async def on_receive(self, data):
            await websocket.send_json({"received": data})

    async with httpx.AsyncClient(transport=ASGIWebSocketTransport(app=app)) as client:
        async with aconnect_ws("http://testserver/", client=client) as ws:
            await ws.send_bytes(b'{"message":"ping"}')

            assert await ws.receive_json() == {"received": {"message": "ping"}}


@pytest.mark.asyncio
async def test_socket_view_on_connect_exception_closes_with_1011():
    app = Kui()

    @app.router.websocket("/")
    class BrokenSocket(SocketView):
        async def on_connect(self) -> None:
            raise ValueError("boom")

    async with httpx.AsyncClient(transport=ASGIWebSocketTransport(app=app)) as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            async with aconnect_ws("http://testserver/", client=client):
                pass

    assert exc_info.value.code == 1011
