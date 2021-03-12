from __future__ import annotations

import asyncio
import json
import typing

from baize.asgi import HTTPException, Message
from pydantic import ValidationError
from pydantic.json import pydantic_encoder

if typing.TYPE_CHECKING:
    from .requests import Request

from .responses import Response


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
    def __init__(
        self,
        view: typing.Callable[[Request], typing.Awaitable[None]],
        handlers: dict = None,
    ) -> None:
        self.view = view
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

    async def __call__(self, request: Request) -> None:
        response_started = False
        send = request._send

        async def sender(message: Message) -> None:
            nonlocal response_started

            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        request._send = sender

        try:
            return await self.view(request)
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

            response = handler(request, exc)
            if asyncio.iscoroutine(response):
                response = await response
            return await response(request._send, request._receive, request._send)

    @staticmethod
    def http_exception(request: Request, exc: HTTPException) -> Response:
        if exc.status_code in {204, 304}:
            return Response(b"", status_code=exc.status_code, headers=exc.headers)

        return Response(
            content=exc.content, status_code=exc.status_code, headers=exc.headers
        )

    @staticmethod
    def request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> Response:
        return Response(exc.json(), status_code=422, media_type="application/json")
