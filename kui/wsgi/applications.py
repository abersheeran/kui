from __future__ import annotations

import dataclasses
import functools
from pathlib import PurePath
from types import GeneratorType
from typing import Any, Callable, Iterable, List, Mapping, NoReturn, Optional, Type

from baize.datastructures import URL
from baize.typing import Environ, StartResponse

from ..routing import BaseRoute, MiddlewareType, NoMatchFound, SyncViewType
from ..utils import ImmutableAttribute, State
from .exceptions import ErrorHandlerType, ExceptionMiddleware, HTTPException
from .requests import HttpRequest, request_var
from .responses import (
    FileResponse,
    HttpResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    SendEventResponse,
)
from .routing import Router
from .templates import BaseTemplates


@dataclasses.dataclass
class FactoryClass:
    http: Type[HttpRequest] = HttpRequest


class Kui:
    state: ImmutableAttribute[State] = ImmutableAttribute()

    def __init__(
        self,
        *,
        templates: Optional[BaseTemplates] = None,
        routes: Iterable[BaseRoute] = [],
        http_middlewares: List[MiddlewareType[SyncViewType]] = [],
        socket_middlewares: List[MiddlewareType[SyncViewType]] = [],
        exception_handlers: Mapping[int | Type[BaseException], ErrorHandlerType] = {},
        factory_class: FactoryClass = FactoryClass(),
        response_converters: Mapping[type, Callable[..., HttpResponse]] = {},
    ) -> None:
        self.should_exit = False

        self.state = State()
        self.response_converter = create_response_converter(response_converters)
        self.should_exit = False
        self.factory_class = factory_class
        self.templates = templates
        self.exception_middleware = ExceptionMiddleware(exception_handlers)
        self.router = Router(
            routes, [*http_middlewares, self.exception_middleware], socket_middlewares
        )

    def add_exception_handler(
        self, exc_class_or_status_code: int | Type[Exception], handler: ErrorHandlerType
    ) -> None:
        self.exception_middleware.add_exception_handler(
            exc_class_or_status_code, handler
        )

    def exception_handler(
        self, exc_class_or_status_code: int | Type[Exception]
    ) -> Callable[[ErrorHandlerType], ErrorHandlerType]:
        def decorator(func: ErrorHandlerType) -> ErrorHandlerType:
            self.add_exception_handler(exc_class_or_status_code, func)
            return func

        return decorator

    def app(self, environ: Environ, start_response: StartResponse) -> Iterable[bytes]:
        request = self.factory_class.http(environ)
        token = request_var.set(request)
        try:
            try:
                path_params, handler = self.router.search(
                    "http", request.get("PATH_INFO", "")
                )
                request["PATH_PARAMS"] = path_params
                response = handler()
            except NoMatchFound:
                http_exception: HTTPException[None] = HTTPException(404)
                error_handler = self.exception_middleware.lookup_handler(http_exception)
                if error_handler is None:
                    raise RuntimeError(
                        "No exception handler found for HTTPException(404)"
                    )
                response = error_handler(http_exception)

            if isinstance(response, tuple):
                response = self.response_converter(*response)
            else:
                response = self.response_converter(response)

            yield from response(environ, start_response)
        finally:
            request.close()
            request_var.reset(token)

    def __call__(
        self, environ: Environ, start_response: StartResponse
    ) -> Iterable[bytes]:
        environ["app"] = self

        return self.app(environ, start_response)


def create_response_converter(
    converters: Mapping[type, Callable[..., HttpResponse]]
) -> functools._SingleDispatchCallable[HttpResponse]:
    """
    Create a converter for convert response.
    """

    @functools.singledispatch
    def response_converter(*args: Any) -> HttpResponse:
        raise TypeError(
            f"Cannot find response_converter handler for this type: {type(args[0])}"
        )

    def _none(ret: Type[None]) -> NoReturn:
        raise TypeError(
            "Get 'None'. Maybe you need to add a return statement to the function."
        )

    response_converter.register(type(None), _none)
    response_converter.register(HttpResponse, lambda x: x)
    response_converter.register(dict, JSONResponse)
    response_converter.register(list, JSONResponse)
    response_converter.register(tuple, JSONResponse)
    response_converter.register(bytes, PlainTextResponse)
    response_converter.register(str, PlainTextResponse)
    response_converter.register(GeneratorType, SendEventResponse)
    response_converter.register(
        PurePath,
        lambda filepath, download_name=None: FileResponse(
            str(filepath), download_name=download_name
        ),
    )
    response_converter.register(URL, RedirectResponse)

    for type_, converter in converters.items():
        response_converter.register(type_, converter)

    return response_converter
