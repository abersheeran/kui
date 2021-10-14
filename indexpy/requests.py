from __future__ import annotations

import asyncio
import json
import typing
from contextvars import ContextVar
from http import HTTPStatus

from baize.asgi import HTTPConnection as BaiZeHTTPConnection
from baize.asgi import Request as BaiZeRequest
from baize.asgi import WebSocket as BaiZeWebSocket
from baize.asgi import WebSocketDisconnect, WebSocketState
from baize.datastructures import ContentType
from baize.exceptions import HTTPException
from baize.utils import cached_property
from typing_extensions import Annotated

if typing.TYPE_CHECKING:
    from .applications import Index

from .utils import State, bind_contextvar


class HTTPConnection(BaiZeHTTPConnection, typing.MutableMapping[str, typing.Any]):
    def __setitem__(self, name: str, value: typing.Any) -> None:
        self._scope[name] = value

    def __delitem__(self, name: str) -> None:
        del self._scope[name]

    @cached_property
    def state(self) -> State:
        self._scope.setdefault("state", {})
        return State(self._scope["state"])

    @cached_property
    def app(self) -> Index:
        return self["app"]  # type: ignore


class HttpRequest(BaiZeRequest, HTTPConnection):
    async def data(
        self,
    ) -> Annotated[
        typing.Any,
        ContentType("application/json"),
        ContentType("application/x-www-form-urlencoded"),
        ContentType("multipart/form-data"),
    ]:
        content_type = self.content_type
        if content_type == "application/json":
            return await self.json
        elif content_type in (
            "multipart/form-data",
            "application/x-www-form-urlencoded",
        ):
            return await self.form

        raise HTTPException(HTTPStatus.UNSUPPORTED_MEDIA_TYPE)


request_var: ContextVar[HttpRequest] = ContextVar("request")

request = bind_contextvar(request_var)


class WebSocket(BaiZeWebSocket, HTTPConnection):
    async def is_disconnected(self) -> bool:
        """
        The method used to determine whether the connection is interrupted.

        NOTE: The call may discard the information sent by the client.
        """
        if not hasattr(self, "_is_disconnected"):
            self._is_disconnected = False

        if not self._is_disconnected:
            try:
                message = await asyncio.wait_for(self._receive(), timeout=0.0000001)
                self._is_disconnected = message.get("type") == "websocket.disconnect"
            except asyncio.TimeoutError:
                pass
        return self._is_disconnected

    async def receive_json(self, mode: str = "text") -> typing.Any:
        assert mode in ("text", "binary")
        assert self.application_state == WebSocketState.CONNECTED
        message = await self.receive()
        self._raise_on_disconnect(message)

        if mode == "text":
            text = message["text"]
        else:
            text = message["bytes"].decode("utf-8")
        return json.loads(text)

    async def send_json(self, data: typing.Any, mode: str = "text") -> None:
        assert mode in ("text", "binary")
        text = json.dumps(data)
        if mode == "text":
            await self.send({"type": "websocket.send", "text": text})
        else:
            await self.send({"type": "websocket.send", "bytes": text.encode("utf-8")})

    async def iter_json(self) -> typing.AsyncIterator[typing.Any]:
        try:
            while True:
                yield await self.receive_json()
        except WebSocketDisconnect:
            pass


websocket_var: ContextVar[WebSocket] = ContextVar("websocket")

websocket = bind_contextvar(websocket_var)
