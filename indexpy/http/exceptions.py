import asyncio
import http
import typing

from ..types import ASGIApp, Message, Receive, Scope, Send
from .view import ParamsValidationError
from .request import Request
from .responses import Response, PlainTextResponse, JSONResponse


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str = None) -> None:
        if detail is None:
            detail = http.HTTPStatus(status_code).phrase
        self.status_code = status_code
        self.detail = detail

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(status_code={self.status_code!r}, detail={self.detail!r})"


class ExceptionMiddleware:
    def __init__(self, app: ASGIApp, handlers: dict = None) -> None:
        self.app = app
        self._status_handlers: typing.Dict[int, typing.Callable] = {}
        self._exception_handlers: typing.Dict[
            typing.Type[Exception], typing.Callable
        ] = {
            HTTPException: self.http_exception,
            ParamsValidationError: self.params_validation_error,
        }
        if handlers is not None:
            for key, value in handlers.items():
                self.add_exception_handler(key, value)

    def add_exception_handler(
        self,
        exc_class_or_status_code: typing.Union[int, typing.Type[Exception]],
        handler: typing.Callable,
    ) -> None:
        if isinstance(exc_class_or_status_code, int):
            self._status_handlers[exc_class_or_status_code] = handler
        else:
            assert issubclass(exc_class_or_status_code, Exception)
            self._exception_handlers[exc_class_or_status_code] = handler

    def _lookup_exception_handler(
        self, exc: Exception
    ) -> typing.Optional[typing.Callable]:
        for cls in type(exc).__mro__:
            if cls in self._exception_handlers:
                return self._exception_handlers[cls]
        return None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def sender(message: Message) -> None:
            nonlocal response_started

            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, sender)
        except Exception as exc:
            handler = None
            request_class = scope["app"].factory_class["http"]

            if isinstance(exc, HTTPException):
                handler = self._status_handlers.get(exc.status_code)

            if handler is None:
                handler = self._lookup_exception_handler(exc)

            if handler is None:
                raise exc from None

            if response_started:
                msg = "Caught handled exception, but response already started."
                raise RuntimeError(msg) from exc

            request = request_class(scope, receive, send)
            if asyncio.iscoroutinefunction(handler):
                response = await handler(request, exc)
            else:
                response = handler(request, exc)
            await response(scope, receive, sender)

    def http_exception(self, request: Request, exc: HTTPException) -> Response:
        if exc.status_code in {204, 304}:
            return Response(b"", status_code=exc.status_code)
        return PlainTextResponse(exc.detail, status_code=exc.status_code)

    def params_validation_error(
        self, request: Request, exc: ParamsValidationError
    ) -> Response:
        return JSONResponse(exc.ve.errors(), status_code=400)
