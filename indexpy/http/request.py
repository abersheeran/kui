import asyncio
import json
import typing
from http import cookies as http_cookies

from starlette.datastructures import URL, Address, Headers, QueryParams
from starlette.formparsers import (
    FormData,
    FormParser,
    MultiPartParser,
    parse_options_header,
)
from starlette.requests import SERVER_PUSH_HEADERS_TO_COPY, ClientDisconnect

from indexpy.types import Message, Receive, Scope, Send, UPPER_HTTP_METHODS
from indexpy.utils import cached_property, State


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
        if hasattr(self, "_body"):
            yield self._body
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

    async def body(self) -> bytes:
        if not hasattr(self, "_body"):
            chunks = []
            async for chunk in self.stream():
                chunks.append(chunk)
            self._body = b"".join(chunks)
        return self._body

    async def json(self) -> typing.Any:
        if not hasattr(self, "_json"):
            body = await self.body()
            self._json = json.loads(body)
        return self._json

    async def form(self) -> FormData:
        if not hasattr(self, "_form"):
            assert (
                parse_options_header is not None
            ), "The `python-multipart` library must be installed to use form parsing."
            content_type_header = self.headers.get("Content-Type")
            content_type, options = parse_options_header(content_type_header)
            if content_type == b"multipart/form-data":
                multipart_parser = MultiPartParser(self.headers, self.stream())
                self._form = await multipart_parser.parse()
            elif content_type == b"application/x-www-form-urlencoded":
                form_parser = FormParser(self.headers, self.stream())
                self._form = await form_parser.parse()
            else:
                self._form = FormData()
        return self._form

    async def close(self) -> None:
        if hasattr(self, "_form"):
            await self._form.close()

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
