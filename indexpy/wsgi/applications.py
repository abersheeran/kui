from __future__ import annotations

import dataclasses
import functools
from functools import reduce
from pathlib import PurePath
from types import GeneratorType
from typing import (
    Any,
    Callable,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    NoReturn,
    Optional,
    Type,
)

from baize.datastructures import URL
from baize.typing import Environ, StartResponse, WSGIApp

from .debug import DebugMiddleware
from .exceptions import ErrorView, ExceptionMiddleware, HTTPException
from .requests import HttpRequest, request_var
from .responses import (
    FileResponse,
    HttpResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    SendEventResponse,
    convert_response,
)
from .routing import BaseRoute, NoMatchFound, Router
from .templates import BaseTemplates
from .utils import F, ImmutableAttribute, State


@dataclasses.dataclass
class FactoryClass:
    http: Type[HttpRequest] = HttpRequest


class HintAPI:
    debug: ImmutableAttribute[bool] = ImmutableAttribute()
    state: ImmutableAttribute[State] = ImmutableAttribute()

    def __init__(
        self,
        *,
        debug: bool = False,
        templates: Optional[BaseTemplates] = None,
        routes: Iterable[BaseRoute] = [],
        exception_handlers: MutableMapping[int | Type[BaseException], ErrorView] = {},
        factory_class: FactoryClass = FactoryClass(),
        response_converters: Mapping[type, Callable[..., HttpResponse]] = {},
    ) -> None:
        self.debug = debug
        self.state = State()
        self._exception_handlers = exception_handlers
        self.response_converter = create_response_converter(response_converters)
        self.should_exit = False
        self.factory_class = factory_class
        self.templates = templates
        self.router = Router(routes)
        self._asgi_middlewares: List[F] = []
        self.app_with_middlewares = self.build_app_with_middlewares()

    def build_app_with_middlewares(self) -> WSGIApp:
        internal_middlewares: List[F] = []
        if self.debug:
            internal_middlewares.append(F(DebugMiddleware))

        return reduce(
            lambda a, m: m(a),
            reversed(
                [
                    *internal_middlewares,
                    *self._asgi_middlewares,
                    F(
                        ExceptionMiddleware,
                        response_convertor=self.response_converter,
                        handlers=self._exception_handlers,
                    ),
                ]
            ),
            self.app,
        )

    def add_middleware(self, middleware_class: type, **options: Any) -> None:
        """
        Add ASGI middleware
        """
        self._asgi_middlewares.append(F(middleware_class, **options))
        self.app_with_middlewares = self.build_app_with_middlewares()

    def add_exception_handler(
        self, exc_class_or_status_code: int | Type[Exception], handler: ErrorView
    ) -> None:
        self._exception_handlers[exc_class_or_status_code] = handler

    def exception_handler(
        self, exc_class_or_status_code: int | Type[Exception]
    ) -> Callable[[ErrorView], ErrorView]:
        def decorator(func: ErrorView) -> ErrorView:
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
                response = convert_response(handler())
            except NoMatchFound:
                raise HTTPException(404)
            else:
                yield from response(environ, start_response)
        finally:
            request.close()
            request_var.reset(token)

    def __call__(
        self, environ: Environ, start_response: StartResponse
    ) -> Iterable[bytes]:
        environ["app"] = self

        return self.app_with_middlewares(environ, start_response)


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
