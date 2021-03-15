from __future__ import annotations

import json
import functools
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
)

from baize.asgi import HTTPException, PlainTextResponse
from baize.typing import JSONable
from pydantic import ValidationError
from pydantic.json import pydantic_encoder

from .responses import Response


class RequestValidationError(Exception):
    def __init__(self, validation_error: ValidationError) -> None:
        self.validation_error = validation_error

    def errors(self) -> List[Dict[str, Any]]:
        return self.validation_error.errors()

    def json(self, *, indent: Union[None, int, str] = 2) -> str:
        return json.dumps(self.errors(), indent=indent, default=pydantic_encoder)

    @staticmethod
    def schema() -> Dict[str, JSONable]:
        return {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "loc": {
                        "title": "Location",
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
                        "title": "Message",
                        "description": "error message",
                        "type": "string",
                    },
                },
                "required": ["loc", "type", "msg"],
            },
        }


Error = TypeVar("Error", bound=Exception)
ErrorView = Callable[[Error], Awaitable[Response]]
View = Callable[[], Coroutine[Any, Any, Response]]


class ExceptionMiddleware:
    def __init__(
        self,
        handlers: Dict[Union[int, Type[Exception]], ErrorView] = None,
    ) -> None:
        self._status_handlers: Dict[int, ErrorView] = {}
        self._exception_handlers: Dict[Type[Exception], ErrorView] = {
            HTTPException: self.http_exception,
            RequestValidationError: self.request_validation_error,
        }
        if handlers is not None:
            for key, value in handlers.items():
                self.add_exception_handler(key, value)

    def add_exception_handler(
        self,
        exc_class_or_status_code: Union[int, Type[Exception]],
        handler: Callable,
    ) -> None:
        if isinstance(exc_class_or_status_code, int):
            self._status_handlers[exc_class_or_status_code] = handler
        else:
            assert issubclass(exc_class_or_status_code, Exception)
            self._exception_handlers[exc_class_or_status_code] = handler

    def _lookup_exception_handler(self, exc: Exception) -> Optional[Callable]:
        for cls in type(exc).__mro__:
            if cls in self._exception_handlers:
                return self._exception_handlers[cls]
        return None

    def __call__(self, endpoint: View) -> View:
        @functools.wraps(endpoint)
        async def wrapper() -> Response:
            try:
                return await endpoint()
            except Exception as exc:
                handler = None
                if isinstance(exc, HTTPException):
                    handler = self._status_handlers.get(exc.status_code)
                if handler is None:
                    handler = self._lookup_exception_handler(exc)
                if handler is None:
                    raise exc from None
                return await handler(exc)

        return wrapper

    @staticmethod
    async def http_exception(exc: HTTPException) -> Response:
        if exc.status_code in {204, 304}:
            return Response(status_code=exc.status_code, headers=exc.headers)

        return PlainTextResponse(
            content=exc.content or b"", status_code=exc.status_code, headers=exc.headers
        )

    @staticmethod
    async def request_validation_error(exc: RequestValidationError) -> Response:
        return PlainTextResponse(
            exc.json(), status_code=422, media_type="application/json"
        )
