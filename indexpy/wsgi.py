import asyncio
import sys
import typing
from tempfile import SpooledTemporaryFile

from starlette.concurrency import run_in_threadpool
from starlette.types import Message, Receive, Scope, Send


class Body:
    def __init__(self, recv_event: asyncio.Event) -> None:
        self.file = SpooledTemporaryFile(1024 * 1024)
        self.recv_event = recv_event
        self.has_more = True

    def feed_eof(self) -> None:
        self.has_more = False

    async def write(self, data: bytes) -> None:
        await run_in_threadpool(self.file.write, data)

    def close(self) -> None:
        self.file.close()

    def read(self, size: int) -> bytes:
        self.recv_event.set()
        data = self.file.read(size)
        while len(data) < size and self.has_more:
            data += self.file.read()
        return data

    def readline(self, limit: int = -1) -> bytes:
        self.recv_event.set()
        data = self.file.readline(limit)
        while (not data or not data.endswith(b"\n")) and self.has_more:
            data += self.file.readline(limit - len(data))
        return data

    def readlines(self, hint: int = -1) -> typing.List[bytes]:
        self.recv_event.set()
        data = self.file.readlines(hint)
        _hint = data.count(b"\n")
        while _hint < hint and self.has_more:
            data += self.file.readlines(hint - _hint)
            _hint = data.count(b"\n")
        return data

    def __iter__(self) -> typing.Generator:
        self.recv_event.set()
        while self.has_more:
            yield self.readline()


def build_environ(scope: Scope, body: Body) -> dict:
    """
    Builds a scope and request body into a WSGI environ object.
    """
    environ = {
        "REQUEST_METHOD": scope["method"],
        "SCRIPT_NAME": scope.get("root_path", ""),
        "PATH_INFO": scope["path"],
        "QUERY_STRING": scope["query_string"].decode("ascii"),
        "SERVER_PROTOCOL": f"HTTP/{scope['http_version']}",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": scope.get("scheme", "http"),
        "wsgi.input": body,
        "wsgi.errors": sys.stdout,
        "wsgi.multithread": True,
        "wsgi.multiprocess": True,
        "wsgi.run_once": False,
    }

    # Get server name and port - required in WSGI, not in ASGI
    server = scope.get("server") or ("localhost", 80)
    environ["SERVER_NAME"] = server[0]
    environ["SERVER_PORT"] = server[1]

    # Get client IP address
    if scope.get("client"):
        environ["REMOTE_ADDR"] = scope["client"][0]

    # Go through headers and make them into environ entries
    for name, value in scope.get("headers", []):
        name = name.decode("latin1")
        if name == "content-length":
            corrected_name = "CONTENT_LENGTH"
        elif name == "content-type":
            corrected_name = "CONTENT_TYPE"
        else:
            corrected_name = f"HTTP_{name}".upper().replace("-", "_")
        # HTTPbis say only ASCII chars are allowed in headers, but we latin1 just in case
        value = value.decode("latin1")
        if corrected_name in environ:
            value = environ[corrected_name] + "," + value
        environ[corrected_name] = value
    return environ


class WSGIMiddleware:
    def __init__(self, app: typing.Callable, workers: int = 10) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "http"
        responder = WSGIResponder(self.app, scope)
        await responder(receive, send)


class WSGIResponder:
    def __init__(self, app: typing.Callable, scope: Scope) -> None:
        self.app = app
        self.scope = scope
        self.recv_event = asyncio.Event()
        self.send_event = asyncio.Event()
        self.send_queue = []  # type: typing.List[typing.Optional[Message]]
        self.loop = asyncio.get_event_loop()
        self.response_started = False
        self.exc_info = None  # type: typing.Any

    async def __call__(self, receive: Receive, send: Send) -> None:
        body = Body(self.recv_event)
        environ = build_environ(self.scope, body)
        sender = None
        receiver = None
        try:
            sender = self.loop.create_task(self.sender(send))
            receiver = self.loop.create_task(self.recevier(receive, body))
            await run_in_threadpool(self.wsgi, environ, self.start_response)
            self.send_queue.append(None)
            self.send_event.set()
            await asyncio.wait_for(sender, None)
            if self.exc_info is not None:
                raise self.exc_info[0].with_traceback(
                    self.exc_info[1], self.exc_info[2]
                )
        finally:
            if sender and not sender.done():
                sender.cancel()  # pragma: no cover
            if receiver and not receiver.done():
                receiver.cancel()  # pragma: no cover
            body.close()

    async def recevier(self, receive: Receive, body: Body) -> None:
        more_body = True
        await self.recv_event.wait()
        while more_body:
            message = await receive()
            await body.write(message.get("body", b""))
            more_body = message.get("more_body", False)
        body.feed_eof()

    async def sender(self, send: Send) -> None:
        while True:
            if self.send_queue:
                message = self.send_queue.pop(0)
                if message is None:
                    return
                await send(message)
            else:
                await self.send_event.wait()
                self.send_event.clear()

    def start_response(
        self,
        status: str,
        response_headers: typing.List[typing.Tuple[str, str]],
        exc_info: typing.Any = None,
    ) -> None:
        self.exc_info = exc_info
        if not self.response_started:
            self.response_started = True
            status_code_string, _ = status.split(" ", 1)
            status_code = int(status_code_string)
            headers = [
                (name.strip().encode("ascii").lower(), value.strip().encode("ascii"))
                for name, value in response_headers
            ]
            self.send_queue.append(
                {
                    "type": "http.response.start",
                    "status": status_code,
                    "headers": headers,
                }
            )
            self.loop.call_soon_threadsafe(self.send_event.set)

    def wsgi(self, environ: dict, start_response: typing.Callable) -> None:
        for chunk in self.app(environ, start_response):
            self.send_queue.append(
                {"type": "http.response.body", "body": chunk, "more_body": True}
            )
            self.loop.call_soon_threadsafe(self.send_event.set)

        self.send_queue.append({"type": "http.response.body", "body": b""})
        self.loop.call_soon_threadsafe(self.send_event.set)
