from __future__ import annotations

import functools
import json
from http import HTTPStatus
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
)

from baize.exceptions import HTTPException
from baize.typing import Environ, StartResponse, WSGIApp
from pydantic import ValidationError
from pydantic.json import pydantic_encoder
from typing_extensions import Literal

from .responses import HttpResponse, PlainTextResponse


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
ErrorView = Callable[[Error], HttpResponse]


class ExceptionMiddleware:
    def __init__(
        self,
        app: WSGIApp,
        response_convertor: functools._SingleDispatchCallable[HttpResponse],
        handlers: Mapping[Union[int, Type[BaseException]], ErrorView] = {},
    ) -> None:
        self.app = app
        self._response_convertor = response_convertor
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

    def __call__(
        self, environ: Environ, start_response: StartResponse
    ) -> Iterable[bytes]:
        try:
            yield from self.app(environ, start_response)
        except BaseException as exc:
            handler = None
            if isinstance(exc, HTTPException):
                handler = self._status_handlers.get(exc.status_code)
            if handler is None:
                handler = self._lookup_exception_handler(exc)
            if handler is not None:
                response = handler(exc)
                yield from response(environ, start_response)
            else:
                raise exc

    def http_exception(self, exc: HTTPException) -> HttpResponse:
        if exc.status_code in {204, 304}:
            return HttpResponse(status_code=exc.status_code, headers=exc.headers)
        else:
            return self._response_convertor(
                exc.content
                if exc.content is not None
                else HTTPStatus(exc.status_code).description,
                exc.status_code,
                exc.headers,
            )

    def validation_error(self, exc: RequestValidationError) -> HttpResponse:
        if exc.in_ == "path":
            return self.http_exception(HTTPException(status_code=404))
        else:
            return PlainTextResponse(
                exc.json(), status_code=422, media_type="application/json"
            )
