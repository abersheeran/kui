from __future__ import annotations

import typing
from contextvars import ContextVar
from http import HTTPStatus

from baize.asgi import HTTPConnection as BaiZeHTTPConnection
from baize.asgi import Request as BaiZeRequest
from baize.asgi import WebSocket as BaiZeWebSocket
from baize.utils import cached_property

if typing.TYPE_CHECKING:
    from indexpy.applications import Index

from .exceptions import HTTPException
from .utils import State, bind_contextvar


class HTTPConnection(BaiZeHTTPConnection):
    @cached_property
    def state(self) -> State:
        self._scope.setdefault("state", {})
        return State(self._scope["state"])

    def app(self) -> Index:
        return self["app"]


class Request(BaiZeRequest, HTTPConnection):
    async def data(self) -> typing.Any:
        content_type = self.content_type
        if content_type == "application/json":
            return await self.json
        elif str(content_type) in (
            "multipart/form-data",
            "application/x-www-form-urlencoded",
        ):
            return await self.form

        raise HTTPException(HTTPStatus.UNSUPPORTED_MEDIA_TYPE)


request_var: ContextVar[Request] = ContextVar("request")

request = bind_contextvar(request_var)


class WebSocket(BaiZeWebSocket, HTTPConnection):
    pass


websocket_var: ContextVar[WebSocket] = ContextVar("websocket")

websocket = bind_contextvar(websocket_var)
