from __future__ import annotations

import typing
from http import HTTPStatus

from baize.asgi import Request as BaiZeRequest
from baize.asgi import Scope, Receive, Send, empty_receive, empty_send
from baize.utils import cached_property

from indexpy.utils import State

if typing.TYPE_CHECKING:
    from indexpy.applications import Index

from .exceptions import HTTPException


class Request(BaiZeRequest):
    def __init__(
        self, scope: Scope, receive: Receive = empty_receive, send: Send = empty_send
    ):
        super().__init__(scope)
        assert scope["type"] == "http"
        self._receive = receive
        self._send = send
        self._stream_consumed = False
        self._is_disconnected = False

    @cached_property
    def state(self) -> State:
        return self.get("state", {})

    def app(self) -> Index:
        return self["app"]

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

    async def send_push_promise(self, path: str) -> None:
        if "http.response.push" in self.scope.get("extensions", {}):
            raw_headers = []
            for name in SERVER_PUSH_HEADERS_TO_COPY:
                for value in self.headers.getlist(name):
                    raw_headers.append(
                        (name.encode("latin-1"), value.encode("latin-1"))
                    )
            await self._send(
                {"type": "http.response.push", "path": path, "headers": raw_headers}
            )
