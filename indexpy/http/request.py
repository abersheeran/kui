from __future__ import annotations

import typing
from http import HTTPStatus

from baize.asgi import Receive
from baize.asgi import Request as BaiZeRequest, HTTPConnection as BaiZeHTTPConnection
from baize.asgi import Scope, Send, empty_receive, empty_send
from baize.utils import cached_property

from indexpy.utils import State

if typing.TYPE_CHECKING:
    from indexpy.applications import Index

from .exceptions import HTTPException


class HTTPConnection(BaiZeHTTPConnection):
    @cached_property
    def state(self) -> State:
        # Ensure 'state' has an empty dict if it's not already populated.
        self._scope.setdefault("state", {})
        # Create a state instance with a reference to the dict in which it should store info
        return State(self._scope["state"])

    def app(self) -> Index:
        return self["app"]


class Request(BaiZeRequest, HTTPConnection):
    def __init__(
        self, scope: Scope, receive: Receive = empty_receive, send: Send = empty_send
    ):
        super().__init__(scope)
        assert scope["type"] == "http"
        self._receive = receive
        self._send = send
        self._stream_consumed = False
        self._is_disconnected = False

    async def data(self) -> typing.Any:
        content_type = self.content_type
        if content_type == "application/json":
            return await self.json
        elif str(content_type) in (
            "multipart/form-data",
            "application/x-www-form-urlencoded",
        ):
            return await self.form

        # We can inherit this method in subclasses
        # and catch this exception for custom processing
        raise HTTPException(HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
