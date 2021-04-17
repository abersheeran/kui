from __future__ import annotations

import json
from http import HTTPStatus
from types import TracebackType
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
    overload,
)

from baize.asgi import HTTPException, PlainTextResponse
from pydantic import ValidationError
from pydantic.json import pydantic_encoder

from .requests import request
from .responses import HttpResponse


class RequestValidationError(Exception):
    def __init__(self, validation_error: ValidationError) -> None:
        self.validation_error = validation_error

    def errors(self) -> List[Dict[str, Any]]:
        return self.validation_error.errors()

    def json(self, *, indent: Union[None, int, str] = 2) -> str:
        return json.dumps(self.errors(), indent=indent, default=pydantic_encoder)

    @staticmethod
    def schema() -> Dict[str, Any]:
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
ErrorView = Callable[[Error], Awaitable[HttpResponse]]
View = Callable[[], Coroutine[None, None, HttpResponse]]


class ExceptionContextManager:
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

    async def __aenter__(self) -> ExceptionContextManager:
        return self

    @overload
    async def __aexit__(self, exc_type: None, exc: None, tb: None) -> None:
        pass

    @overload
    async def __aexit__(
        self, exc_type: Type[BaseException], exc: BaseException, tb: TracebackType
    ) -> bool:
        pass

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is None:
            return None
        else:
            handler = None
            if isinstance(exc, HTTPException):
                handler = self._status_handlers.get(exc.status_code)
            if handler is None:
                handler = self._lookup_exception_handler(exc)
            if handler is None:
                return False
            response = await handler(exc)
            await response(request._scope, request._receive, request._send)
            return True

    @staticmethod
    async def http_exception(exc: HTTPException) -> HttpResponse:
        if exc.status_code in {204, 304}:
            return HttpResponse(status_code=exc.status_code, headers=exc.headers)

        return PlainTextResponse(
            content=(
                exc.content
                if isinstance(exc.content, (bytes, str))
                else HTTPStatus(exc.status_code).description
            ),
            status_code=exc.status_code,
            headers=exc.headers,
        )

    @staticmethod
    async def request_validation_error(exc: RequestValidationError) -> HttpResponse:
        return PlainTextResponse(
            exc.json(), status_code=422, media_type="application/json"
        )
