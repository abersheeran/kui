from __future__ import annotations

import json
import sys
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

if sys.version_info[:2] < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from baize.asgi import HTTPException, PlainTextResponse
from pydantic import ValidationError
from pydantic.json import pydantic_encoder

from .requests import request
from .responses import HttpResponse


class RequestValidationError(Exception):
    def __init__(
        self,
        validation_error: ValidationError,
        in_: Literal["path", "query", "header", "cookie", "body"],
    ) -> None:
        self.validation_error = validation_error
        self.in_ = in_

    def errors(self) -> List[Dict[str, Any]]:
        errors = self.validation_error.errors()
        for error in errors:
            error["in"] = self.in_
        return errors

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
                    "ctx": {
                        "title": "Context",
                        "description": "error context",
                        "type": "string",
                    },
                    "in": {
                        "title": "In",
                        "type": "string",
                        "enum": ["path", "query", "header", "cookie", "body"],
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
        else:
            return request.app.response_converter(
                exc.content
                if exc.content is not None
                else HTTPStatus(exc.status_code).description,
                exc.status_code,
                exc.headers,
            )

    @staticmethod
    async def request_validation_error(exc: RequestValidationError) -> HttpResponse:
        return PlainTextResponse(
            exc.json(), status_code=422, media_type="application/json"
        )
