import json
import typing
import logging
from inspect import signature

from starlette import status
from starlette.types import Message
from starlette.responses import Response
from starlette.websockets import WebSocket
from starlette.requests import Request

from .concurrency import keepasync
from .openapi.models import Model, Query
from .openapi.utils import currying

logger = logging.getLogger(__name__)

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


class View(metaclass=keepasync(*HTTP_METHOD_NAMES)):
    async def __call__(self, request: Request) -> Response:
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.
        self.request = request

        if self.request.method.lower() in HTTP_METHOD_NAMES:
            handler = getattr(
                self, self.request.method.lower(), self.http_method_not_allowed
            )
        else:
            handler = self.http_method_not_allowed

        handler = currying(handler)

        sig = signature(handler)
        query = sig.parameters.get("query")
        if query and issubclass(query.annotation, Query):
            _query = query.annotation(self.request.query_params)
            query_error = await _query.clean()
            if query_error:
                return {"error": {"query": query_error}}, 400
            handler = handler(query=_query)

        body = sig.parameters.get("body")
        if body and issubclass(body.annotation, Model):
            if body.annotation.get_content_type() == "application/json":
                _body_data = await self.request.json()
            else:
                _body_data = await self.request.form()
            _body = body.annotation(_body_data)
            body_error = await _body.clean()
            if body_error:
                return {"error": {"body": body_error}}, 400
            handler = handler(body=_body)

        return await handler()

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

    def allowed_methods(self) -> typing.List[str]:
        return [m.upper() for m in HTTP_METHOD_NAMES if hasattr(self, m)]


class SocketView:

    encoding = None  # May be "text", "bytes", or "json".

    async def __call__(self, websocket: WebSocket) -> None:
        await self.on_connect(websocket)

        close_code = status.WS_1000_NORMAL_CLOSURE

        try:
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.receive":
                    data = await self.decode(websocket, message)
                    await self.on_receive(websocket, data)
                elif message["type"] == "websocket.disconnect":
                    close_code = int(message.get("code", status.WS_1000_NORMAL_CLOSURE))
                    break
        except Exception as exc:
            close_code = status.WS_1011_INTERNAL_ERROR
            raise exc from None
        finally:
            await self.on_disconnect(websocket, close_code)

    async def decode(self, websocket: WebSocket, message: Message) -> typing.Any:

        if self.encoding == "text":
            if "text" not in message:
                await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
                raise RuntimeError("Expected text websocket messages, but got bytes")
            return message["text"]

        if self.encoding == "bytes":
            if "bytes" not in message:
                await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
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
                await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
                raise RuntimeError("Malformed JSON data received.")

        assert (
            self.encoding is None
        ), f"Unsupported 'encoding' attribute {self.encoding}"
        return message["text"] if message.get("text") else message["bytes"]

    async def on_connect(self, websocket: WebSocket) -> None:
        """Override to handle an incoming websocket connection"""
        await websocket.accept()

    async def on_receive(self, websocket: WebSocket, data: typing.Any) -> None:
        """Override to handle an incoming websocket message"""

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        """Override to handle a disconnecting websocket"""
        await websocket.close(code=close_code)
