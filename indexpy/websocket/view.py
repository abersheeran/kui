import json
import typing

from starlette import status
from starlette.types import Message

from .request import WebSocket


class SocketView:

    encoding: typing.Optional[str] = None  # May be "text", "bytes", or "json".

    def __init__(self, websocket: WebSocket) -> None:
        self.websocket = websocket

    def __await__(self):
        return self.__call__().__await__()

    async def __call__(self) -> None:
        try:
            close_code = status.WS_1000_NORMAL_CLOSURE
            await self.on_connect()
            while True:
                message = await self.websocket.receive()
                if message["type"] == "websocket.receive":
                    data = await self.decode(message)
                    await self.on_receive(data)
                elif message["type"] == "websocket.disconnect":
                    close_code = int(message.get("code", status.WS_1000_NORMAL_CLOSURE))
                    break
        except Exception as exc:
            close_code = status.WS_1011_INTERNAL_ERROR
            raise exc from None
        finally:
            await self.on_disconnect(close_code)

    async def decode(self, message: Message) -> typing.Any:

        if self.encoding == "text":
            if "text" not in message:
                await self.websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
                raise RuntimeError("Expected text websocket messages, but got bytes")
            return message["text"]

        if self.encoding == "bytes":
            if "bytes" not in message:
                await self.websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
                raise RuntimeError("Expected bytes websocket messages, but got text")
            return message["bytes"]

        if self.encoding == "json":
            if message.get("text") is not None:
                text = message["text"]
            else:
                text = message["bytes"].decode("utf-8")

            try:
                return json.loads(text)
            except json.decoder.JSONDecodeError:
                await self.websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
                raise RuntimeError("Malformed JSON data received.")

        assert (
            self.encoding is None
        ), f"Unsupported 'encoding' attribute {self.encoding}"
        return message["text"] if message.get("text") else message["bytes"]

    async def on_connect(self) -> None:
        """Override to handle an incoming websocket connection"""
        await self.websocket.accept()

    async def on_receive(self, data: typing.Any) -> None:
        """Override to handle an incoming websocket message"""

    async def on_disconnect(self, close_code: int) -> None:
        """Override to handle a disconnecting websocket"""
        await self.websocket.close(code=close_code)
