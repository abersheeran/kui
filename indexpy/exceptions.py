from __future__ import annotations

import json
from http import HTTPStatus
from types import TracebackType
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

from baize.asgi import HTTPException, PlainTextResponse
from pydantic import ValidationError
from pydantic.json import pydantic_encoder
from typing_extensions import Literal

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


Error = TypeVar("Error", bound=BaseException)
ErrorView = Callable[[Error], Awaitable[HttpResponse]]


class ExceptionContextManager:
    def __init__(
        self,
        handlers: Mapping[Union[int, Type[BaseException]], ErrorView] = {},
    ) -> None:
        self._status_handlers: Dict[int, ErrorView] = {}
        self._exception_handlers: Dict[Type[BaseException], ErrorView] = {
            HTTPException: self.http_exception,
            RequestValidationError: self.validation_error,
        }
        for key, value in handlers.items():
            self.add_exception_handler(key, value)

    def add_exception_handler(
        self,
        exc_class_or_status_code: Union[int, Type[BaseException]],
        handler: Callable,
    ) -> None:
        if isinstance(exc_class_or_status_code, int):
            self._status_handlers[exc_class_or_status_code] = handler
        else:
            self._exception_handlers[exc_class_or_status_code] = handler

    def _lookup_exception_handler(self, exc: BaseException) -> Optional[Callable]:
        for cls in type(exc).__mro__:
            if cls in self._exception_handlers:
                return self._exception_handlers[cls]
        return None

    async def __aenter__(self) -> ExceptionContextManager:
        return self

    @overload
    async def __aexit__(self, exc_type: None, exc: None, tb: None) -> None:
        ...

    @overload
    async def __aexit__(
        self, exc_type: Type[BaseException], exc: BaseException, tb: TracebackType
    ) -> bool:
        ...

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

    async def validation_error(self, exc: RequestValidationError) -> HttpResponse:
        if exc.in_ == "path":
            return await self.http_exception(HTTPException(status_code=404))
        else:
            return PlainTextResponse(
                exc.json(), status_code=422, media_type="application/json"
            )
