from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, Any, Generator, List

if sys.version_info[:2] < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from baize.asgi import Message

if TYPE_CHECKING:
    from .requests import WebSocket

from .requests import request
from .responses import Response


class HttpView:
    HTTP_METHOD_NAMES = [
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "head",
        "options",
        "trace",
    ]

    if TYPE_CHECKING:
        __methods__: List[str]

    def __init_subclass__(cls) -> None:
        cls.__methods__ = [m.upper() for m in cls.HTTP_METHOD_NAMES if hasattr(cls, m)]

    def __await__(self) -> Generator[None, None, Any]:
        return self.__impl__().__await__()

    async def __impl__(self) -> Any:
        handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        return await handler()

    async def http_method_not_allowed(self) -> Response:
        return Response(status_code=405, headers={"Allow": ", ".join(self.__methods__)})

    async def options(self) -> Response:
        """Handle responding to requests for the OPTIONS HTTP verb."""
        return Response(headers={"Allow": ", ".join(self.__methods__)})


class SocketView:
    encoding: Literal["anystr", "text", "bytes", "json"] = "anystr"

    def __init__(self, websocket: WebSocket) -> None:
        self.websocket = websocket

    def __await__(self):
        return self.__impl__().__await__()

    async def __impl__(self) -> None:
        try:
            close_code = 1000
            await self.on_connect()
            while True:
                message = await self.websocket.receive()
                if message["type"] == "websocket.receive":
                    data = await self.decode(message)
                    await self.on_receive(data)
                elif message["type"] == "websocket.disconnect":
                    close_code = int(message.get("code", 1000))
                    break
        except Exception as exc:
            close_code = 1011
            raise exc from None
        finally:
            await self.on_disconnect(close_code)

    async def decode(self, message: Message) -> Any:
        if self.encoding == "text":
            if "text" not in message:
                await self.websocket.close(code=1003)
                raise RuntimeError("Expected text websocket messages, but got bytes")
            return message["text"]

        if self.encoding == "bytes":
            if "bytes" not in message:
                await self.websocket.close(code=1003)
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
                await self.websocket.close(code=1003)
                raise RuntimeError("Malformed JSON data received.")

        return message["text"] if message.get("text") else message["bytes"]

    async def on_connect(self) -> None:
        """Override to handle an incoming websocket connection"""
        await self.websocket.accept()

    async def on_receive(self, data: Any) -> None:
        """Override to handle an incoming websocket message"""

    async def on_disconnect(self, close_code: int) -> None:
        """Override to handle a disconnecting websocket"""
        await self.websocket.close(code=close_code)
