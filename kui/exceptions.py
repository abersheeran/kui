from __future__ import annotations

import abc
import json
from typing import Any, Callable, Dict, Generic, List, Mapping, Type, TypeVar, Union

from baize.exceptions import HTTPException
from pydantic import ValidationError
from pydantic.json import pydantic_encoder
from typing_extensions import Literal


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
            error["in"] = self.in_  # type: ignore
        return errors  # type: ignore

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


ErrorHandlerType = TypeVar("ErrorHandlerType", bound=Callable)


class ExceptionMiddlewareBase(Generic[ErrorHandlerType], abc.ABC):
    def __init__(
        self,
        handlers: Mapping[Union[int, Type[BaseException]], ErrorHandlerType] = {},
    ) -> None:
        self._status_handlers: Dict[int, ErrorHandlerType] = {}
        self._exception_handlers: Dict[Type[BaseException], ErrorHandlerType] = {}
        self._init_internal_handlers()
        for key, value in handlers.items():
            self.add_exception_handler(key, value)

    @abc.abstractmethod
    def _init_internal_handlers(self) -> None:
        raise NotImplementedError

    def add_exception_handler(
        self,
        exc_class_or_status_code: Union[int, Type[BaseException]],
        handler: ErrorHandlerType,
    ) -> None:
        if isinstance(exc_class_or_status_code, int):
            self._status_handlers[exc_class_or_status_code] = handler
        else:
            self._exception_handlers[exc_class_or_status_code] = handler

    def lookup_handler(self, exc: BaseException) -> ErrorHandlerType | None:
        handler = None
        if isinstance(exc, HTTPException):
            handler = self._status_handlers.get(exc.status_code)
        if handler is None:
            handler = self._lookup_exception_handler(exc)
        return handler

    def _lookup_exception_handler(self, exc: BaseException) -> ErrorHandlerType | None:
        for cls in type(exc).__mro__:
            if cls in self._exception_handlers:
                return self._exception_handlers[cls]
        return None
