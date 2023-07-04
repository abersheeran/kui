from __future__ import annotations

import typing
from http import HTTPStatus

from typing_extensions import Annotated

from ..exceptions import ExceptionMiddlewareBase, HTTPException, RequestValidationError
from ..routing import SyncViewType
from .requests import request
from .responses import HttpResponse, JSONResponse, PlainTextResponse

__all__ = [
    "ExceptionMiddleware",
    "ErrorHandlerType",
    "HTTPException",
    "RequestValidationError",
]

ErrorHandlerType = typing.Callable[[typing.Any], typing.Any]


class ExceptionMiddleware(ExceptionMiddlewareBase[ErrorHandlerType]):
    def __call__(self, endpoint: SyncViewType) -> SyncViewType:
        def wrapper() -> typing.Any:
            try:
                return endpoint()
            except BaseException as exc:
                handler = self.lookup_handler(exc)
                if handler is None:
                    raise
                else:
                    return handler(exc)

        return wrapper  # type: ignore

    def _init_internal_handlers(self) -> None:
        self.add_exception_handler(HTTPException, self.http_exception)
        self.add_exception_handler(RequestValidationError, self.validation_error)

    @staticmethod
    def http_exception(exc: HTTPException) -> HttpResponse:
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

    def validation_error(
        self, exc: RequestValidationError
    ) -> Annotated[
        HttpResponse, JSONResponse[422, {}, RequestValidationError.schema()]
    ]:
        if exc.in_ == "path":
            http_exception: HTTPException[None] = HTTPException(status_code=404)
            handler = self.lookup_handler(http_exception)
            if handler is None:
                raise RuntimeError("No exception handler found for HTTPException(404)")
            return handler(http_exception)
        else:
            return PlainTextResponse(
                exc.json(), status_code=422, media_type="application/json"
            )
