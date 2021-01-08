from __future__ import annotations

import asyncio
import http
import json
import typing

from pydantic import ValidationError
from pydantic.json import pydantic_encoder

from indexpy.types import ASGIApp, Message, Receive, Scope, Send

if typing.TYPE_CHECKING:
    from .request import Request

from .responses import Response


class HTTPException(Exception):
    def __init__(
        self,
        status_code: int,
        content: typing.Any = None,
        headers: dict = None,
        media_type: str = None,
    ) -> None:
        self.status_code = status_code
        self.content = content or http.HTTPStatus(status_code).description
        self.headers = headers
        self.media_type = media_type

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(status_code={self.status_code!r})"


class RequestValidationError(Exception):
    def __init__(self, validation_error: ValidationError) -> None:
        self.validation_error = validation_error

    def errors(self) -> typing.List[typing.Dict[str, typing.Any]]:
        return self.validation_error.errors()

    def json(self, *, indent: typing.Union[None, int, str] = 2) -> str:
        return json.dumps(self.errors(), indent=indent, default=pydantic_encoder)

    @staticmethod
    def schema() -> dict:
        return {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "loc": {
                        "title": "Loc",
                        "description": "error field",
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "type": {
                        "title": "Type",
                        "description": "error type",
                        "type": "string",
                    },
                    "msg": {
                        "title": "Msg",
                        "description": "error message",
                        "type": "string",
                    },
                },
                "required": ["loc", "type", "msg"],
            },
        }


class ExceptionMiddleware:
    def __init__(self, app: ASGIApp, handlers: dict = None) -> None:
        self.app = app
        self._status_handlers: typing.Dict[int, typing.Callable] = {}
        self._exception_handlers: typing.Dict[
            typing.Type[Exception], typing.Callable
        ] = {
            HTTPException: self.http_exception,
            RequestValidationError: self.request_validation_error,
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

            if isinstance(exc, HTTPException):
                handler = self._status_handlers.get(exc.status_code)

            if handler is None:
                handler = self._lookup_exception_handler(exc)

            if handler is None:
                raise exc from None

            if response_started:
                msg = "Caught handled exception, but response already started."
                raise RuntimeError(msg) from exc

            request = scope["app"].factory_class.http(scope, receive, send)
            if asyncio.iscoroutinefunction(handler):
                response = await handler(request, exc)
            else:
                response = handler(request, exc)
            await response(scope, receive, sender)

    @staticmethod
    def http_exception(request: Request, exc: HTTPException) -> Response:
        if exc.status_code in {204, 304}:
            return Response(b"", status_code=exc.status_code, headers=exc.headers)

        return Response(
            content=exc.content,
            status_code=exc.status_code,
            headers=exc.headers,
            media_type=exc.media_type,
        )

    @staticmethod
    def request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> Response:
        return Response(exc.json(), status_code=422, media_type="application/json")
