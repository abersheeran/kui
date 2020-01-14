import json
import typing
import logging

from starlette import status
from starlette.types import Message
from starlette.responses import Response
from starlette.websockets import WebSocket
from starlette.requests import Request
from pydantic import ValidationError

from .concurrency import keepasync
from .openapi.functions import partial, ParseError
from .values import HTTP_METHOD_NAMES

logger = logging.getLogger(__name__)


class View(metaclass=keepasync(*HTTP_METHOD_NAMES)):
    def __init__(self, request: Request) -> None:
        self.request = request

    def __await__(self):
        return self.__call__().__await__()

    async def __call__(self) -> typing.Union[Response, typing.Tuple]:
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.

        if self.request.method.lower() in HTTP_METHOD_NAMES:
            handler = getattr(
                self, self.request.method.lower(), self.http_method_not_allowed
            )
        else:
            handler = self.http_method_not_allowed

        try:
            handler = await partial(handler, self.request)
        except ValidationError as e:
            return {"error": e.errors()}, 400

        resp = await handler()
        return resp

    async def http_method_not_allowed(self) -> Response:
        logger.warning(
            f"Method Not Allowed ({self.request.method}): {self.request.url.path}"
        )
        return Response(
            status_code=405,
            headers={"Allow": ", ".join(self.allowed_methods()), "Content-Length": "0"},
        )

    async def options(self) -> Response:
        """Handle responding to requests for the OPTIONS HTTP verb."""
        return Response(
            headers={"Allow": ", ".join(self.allowed_methods()), "Content-Length": "0"}
        )

    @classmethod
    def allowed_methods(cls) -> typing.List[str]:
        return [m.upper() for m in HTTP_METHOD_NAMES if hasattr(cls, m)]


class SocketView:

    encoding: typing.Optional[str] = None  # May be "text", "bytes", or "json".

    def __init__(self, websocket: WebSocket) -> None:
        self.websocket = websocket

    def __await__(self):
        return self.__call__().__await__()

    async def __call__(self) -> None:
        await self.on_connect()

        close_code = status.WS_1000_NORMAL_CLOSURE

        try:
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
