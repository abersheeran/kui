import asyncio
import json
from typing import (
    cast,
    Any,
    Dict,
    Union,
    List,
    Iterator,
    Mapping,
    AsyncGenerator,
)

from starlette.types import Scope, Send, Receive
from starlette.datastructures import (
    Address,
    URL,
    Headers,
    QueryParams,
    State,
)
from starlette.formparsers import (
    FormData,
    MultiPartParser,
    FormParser,
    parse_options_header,
)
from starlette.requests import (
    cookie_parser,
    SERVER_PUSH_HEADERS_TO_COPY,
    empty_receive,
    empty_send,
    ClientDisconnect,
)


class HTTPConnection(Mapping):
    """
    A base class for incoming HTTP connections, that is used to provide
    any functionality that is common to both `Request` and `WebSocket`.
    """

    def __init__(self, scope: Scope, receive: Receive = None) -> None:
        assert scope["type"] in ("http", "websocket")
        self.scope = scope

    def __getitem__(self, key: str) -> str:
        return self.scope[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.scope)

    def __len__(self) -> int:
        return len(self.scope)

    @property
    def url(self) -> URL:
        if not hasattr(self, "_url"):
            self._url = URL(scope=self.scope)
        return self._url

    @property
    def base_url(self) -> URL:
        if not hasattr(self, "_base_url"):
            base_url_scope = dict(self.scope)
            base_url_scope["path"] = "/"
            base_url_scope["query_string"] = b""
            base_url_scope["root_path"] = base_url_scope.get(
                "app_root_path", base_url_scope.get("root_path", "")
            )
            self._base_url = URL(scope=base_url_scope)
        return self._base_url

    @property
    def headers(self) -> Headers:
        if not hasattr(self, "_headers"):
            self._headers = Headers(scope=self.scope)
        return self._headers

    @property
    def query_params(self) -> QueryParams:
        if not hasattr(self, "_query_params"):
            self._query_params = QueryParams(self.scope["query_string"])
        return self._query_params

    @property
    def cookies(self) -> Dict[str, str]:
        if not hasattr(self, "_cookies"):
            cookies: Dict[str, str] = {}
            cookie_header = self.headers.get("cookie")

            if cookie_header:
                cookies = cookie_parser(cookie_header)
            self._cookies = cookies
        return self._cookies

    @property
    def client(self) -> Address:
        host, port = self.scope.get("client") or (None, None)
        return Address(host=host, port=port)

    @property
    def state(self) -> State:
        if not hasattr(self, "_state"):
            # Ensure 'state' has an empty dict if it's not already populated.
            self.scope.setdefault("state", {})
            # Create a state instance with a reference to the dict in which it should store info
            self._state = State(self.scope["state"])
        return self._state


class Request(HTTPConnection):
    def __init__(
        self, scope: Scope, receive: Receive = empty_receive, send: Send = empty_send, params: dict = Dict
    ):
        super().__init__(scope)
        assert scope["type"] == "http"
        self._receive = receive
        self._send = send
        self._stream_consumed = False
        self._is_disconnected = False
        self._params = params

    @property
    def params(self) -> dict:
        return self._params

    def set_params(self, params: dict):
        self._params = params

    @property
    def method(self) -> str:
        return self.scope["method"]

    @property
    def receive(self) -> Receive:
        return self._receive

    async def stream(self) -> AsyncGenerator[bytes, None]:
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

    async def json(self) -> Any:
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
