from __future__ import annotations

import asyncio
import json
import typing
from http import HTTPStatus
from http import cookies as http_cookies

from starlette.datastructures import URL, Address, Headers, QueryParams
from starlette.formparsers import (
    FormData,
    FormParser,
    MultiPartParser,
    parse_options_header,
)
from starlette.requests import SERVER_PUSH_HEADERS_TO_COPY, ClientDisconnect

from indexpy.types import UPPER_HTTP_METHODS, Message, Receive, Scope, Send
from indexpy.utils import State, cached_property

if typing.TYPE_CHECKING:
    from indexpy.applications import Index

from .exceptions import HTTPException


def cookie_parser(cookie_string: str) -> typing.Dict[str, str]:
    """
    This function parses a ``Cookie`` HTTP header into a dict of key/value pairs.

    It attempts to mimic browser cookie parsing behavior: browsers and web servers
    frequently disregard the spec (RFC 6265) when setting and reading cookies,
    so we attempt to suit the common scenarios here.

    This function has been adapted from Django 3.1.0.
    Note: we are explicitly _NOT_ using `SimpleCookie.load` because it is based
    on an outdated spec and will fail on lots of input we want to support
    """
    cookie_dict: typing.Dict[str, str] = {}
    for chunk in cookie_string.split(";"):
        if "=" in chunk:
            key, val = chunk.split("=", 1)
        else:
            # Assume an empty name per
            # https://bugzilla.mozilla.org/show_bug.cgi?id=169091
            key, val = "", chunk
        key, val = key.strip(), val.strip()
        if key or val:
            # unquote using Python's algorithm.
            cookie_dict[key] = http_cookies._unquote(val)  # type: ignore
    return cookie_dict


class MediaType:
    params: typing.Dict[bytes, bytes]
    main_type: str
    sub_type: str

    def __init__(self, media_type_raw_line: str) -> None:
        full_type, self.params = parse_options_header(media_type_raw_line)
        self.main_type, _, self.sub_type = full_type.decode("ascii").partition("/")

    def __str__(self) -> str:
        params_str = "".join(
            f"; {k.decode('ascii')}={v.decode('ascii')}" for k, v in self.params.items()
        )
        return (
            str(self.main_type)
            + ((f"/{self.sub_type}") if self.sub_type else "")
            + str(params_str)
        )

    def __repr__(self) -> str:
        return "<%s: %s>" % (self.__class__.__qualname__, self)

    @property
    def is_all_types(self) -> bool:
        return self.main_type == "*" and self.sub_type == "*"

    def match(self, other: str) -> bool:
        if self.is_all_types:
            return True
        other_media_type = MediaType(other)
        return self.main_type == other_media_type.main_type and (
            self.sub_type in {"*", other_media_type.sub_type}
        )


class ContentType:
    def __init__(self, content_type: str, options: typing.Dict[str, str]) -> None:
        self.type = content_type
        self.options = options

    def __str__(self) -> str:
        return self.type

    def __repr__(self) -> str:
        return self.type + "".join(f"; {k}={v}" for k, v in self.options.items())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, str):
            return NotImplemented
        return self.type == other


class HTTPConnection(typing.Mapping):
    """
    A base class for incoming HTTP connections, that is used to provide
    any functionality that is common to both `Request` and `WebSocket`.
    """

    def __init__(self, scope: Scope) -> None:
        assert scope["type"] in ("http", "websocket")
        self.scope = scope

    def __getitem__(self, key: str) -> str:
        return self.scope[key]

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self.scope)

    def __len__(self) -> int:
        return len(self.scope)

    @property
    def app(self) -> Index:
        return self.scope["app"]

    @cached_property
    def client(self) -> Address:
        host, port = self.scope.get("client") or (None, None)
        return Address(host=host, port=port)

    @cached_property
    def url(self) -> URL:
        return URL(scope=self.scope)

    @cached_property
    def base_url(self) -> URL:
        base_url_scope = dict(self.scope)
        base_url_scope["path"] = "/"
        base_url_scope["query_string"] = b""
        base_url_scope["root_path"] = base_url_scope.get(
            "app_root_path", base_url_scope.get("root_path", "")
        )
        return URL(scope=base_url_scope)

    @cached_property
    def path_params(self) -> typing.Dict[str, typing.Any]:
        return self.scope.get("path_params", {})

    @cached_property
    def headers(self) -> Headers:
        return Headers(scope=self.scope)

    @cached_property
    def content_type(self) -> ContentType:
        """
        return content-type and options
        """
        full_type, options = parse_options_header(self.headers.get("Content-Type"))
        return ContentType(
            full_type.decode("ascii"),
            {k.decode("ascii"): v.decode("ascii") for k, v in options.items()},
        )

    @cached_property
    def accepted_types(self) -> typing.List[MediaType]:
        return [
            MediaType(token)
            for token in self.headers.get("Accept", "*/*").split(",")
            if token.strip()
        ]

    def accepts(self, media_type: str) -> bool:
        return any(
            accepted_type.match(media_type) for accepted_type in self.accepted_types
        )

    @cached_property
    def query_params(self) -> QueryParams:
        return QueryParams(self.scope["query_string"])

    @cached_property
    def cookies(self) -> typing.Dict[str, str]:
        cookies: typing.Dict[str, str] = {}
        cookie_header = self.headers.get("cookie")

        if cookie_header:
            cookies = cookie_parser(cookie_header)
        return cookies

    @cached_property
    def session(self) -> typing.Dict[str, typing.Any]:
        assert (
            "session" in self.scope
        ), "`starlette.middleware.sessions.SessionMiddleware` must be installed to access request.session"
        return self.scope["session"]

    @cached_property
    def state(self) -> State:
        # Ensure 'state' has an empty dict if it's not already populated.
        self.scope.setdefault("state", {})
        # Create a state instance with a reference to the dict in which it should store info
        return State(self.scope["state"])


async def empty_receive() -> Message:
    raise RuntimeError("Receive channel has not been made available")


async def empty_send(message: Message) -> None:
    raise RuntimeError("Send channel has not been made available")


class Request(HTTPConnection):
    def __init__(
        self, scope: Scope, receive: Receive = empty_receive, send: Send = empty_send
    ):
        super().__init__(scope)
        assert scope["type"] == "http"
        self._receive = receive
        self._send = send
        self._stream_consumed = False
        self._is_disconnected = False

    @property
    def method(self) -> UPPER_HTTP_METHODS:
        return self.scope["method"]

    async def stream(self) -> typing.AsyncGenerator[bytes, None]:
        if "body" in self.__dict__ and self.__dict__["body"].done():
            yield await self.body
            yield b""
            return

        if self._stream_consumed:
            raise RuntimeError("Stream consumed")

        self._stream_consumed = True
        while True:
            message = await self._receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                if body:
                    yield body
                if not message.get("more_body", False):
                    break
            elif message["type"] == "http.disconnect":
                self._is_disconnected = True
                raise ClientDisconnect()
        yield b""

    @cached_property
    async def body(self) -> bytes:
        chunks = []
        async for chunk in self.stream():
            chunks.append(chunk)
        return b"".join(chunks)

    @cached_property
    async def json(self) -> typing.Any:
        body = await self.body
        return json.loads(body)

    @cached_property
    async def form(self) -> FormData:
        if self.content_type == "multipart/form-data":
            multipart_parser = MultiPartParser(self.headers, self.stream())
            return await multipart_parser.parse()
        if self.content_type == "application/x-www-form-urlencoded":
            form_parser = FormParser(self.headers, self.stream())
            return await form_parser.parse()
        return FormData()

    async def data(self) -> typing.Any:
        content_type = self.content_type
        if content_type == b"application/json":
            return await self.json
        elif str(content_type) in (
            "multipart/form-data",
            "application/x-www-form-urlencoded",
        ):
            return await self.form

        # We can inherit this method in subclasses
        # and catch this exception for custom processing
        raise HTTPException(HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    async def close(self) -> None:
        if "form" in self.__dict__ and self.__dict__["form"].done():
            await (await self.form).close()

    async def is_disconnected(self) -> bool:
        if not self._is_disconnected:
            try:
                message = await asyncio.wait_for(self._receive(), timeout=0.0000001)
            except asyncio.TimeoutError:
                message = {}

            if message.get("type") == "http.disconnect":
                self._is_disconnected = True

        return self._is_disconnected

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
