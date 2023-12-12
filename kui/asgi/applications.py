from __future__ import annotations

import copy
import dataclasses
import functools
from pathlib import PurePath
from types import AsyncGeneratorType
from typing import (
    Any,
    Callable,
    Iterable,
    List,
    Mapping,
    NoReturn,
    Optional,
    Type,
    TypeVar,
)

from baize.asgi import Files, Hosts, Pages, Subpaths
from baize.asgi import Router as BaizeRouter
from baize.datastructures import URL
from baize.typing import Receive, Scope, Send
from pydantic import BaseModel
from typing_extensions import Literal

from ..cors import CORSConfig
from ..routing import AsyncViewType, BaseRoute, MiddlewareType, NoMatchFound
from ..utils import ImmutableAttribute, State
from .cors import allow_cors
from .exceptions import ErrorHandlerType, ExceptionMiddleware, HTTPException
from .lifespan import Lifespan, LifespanCallback
from .requests import HttpRequest, WebSocket, request_var, websocket_var
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

LifespanCallbackTypeVar = TypeVar("LifespanCallbackTypeVar", bound=LifespanCallback)


@dataclasses.dataclass
class FactoryClass:
    http: Type[HttpRequest] = HttpRequest
    websocket: Type[WebSocket] = WebSocket


class Kui:
    state: ImmutableAttribute[State] = ImmutableAttribute()

    def __init__(
        self,
        *,
        templates: Optional[BaseTemplates] = None,
        on_startup: List[LifespanCallback] = [],
        on_shutdown: List[LifespanCallback] = [],
        routes: Iterable[BaseRoute] = [],
        http_middlewares: List[MiddlewareType[AsyncViewType]] = [],
        socket_middlewares: List[MiddlewareType[AsyncViewType]] = [],
        exception_handlers: Mapping[int | Type[BaseException], ErrorHandlerType] = {},
        cors_config: Optional[CORSConfig] = None,
        factory_class: FactoryClass = FactoryClass(),
        response_converters: Mapping[type, Callable[..., HttpResponse]] = {},
    ) -> None:
        self.should_exit = False

        self.state = State()
        self.response_converter = create_response_converter(response_converters)
        self.factory_class = factory_class
        self.templates = templates
        self.lifespan = Lifespan(copy.copy(on_startup), copy.copy(on_shutdown))

        http_middlewares = [*http_middlewares]

        self.exception_middleware = ExceptionMiddleware(exception_handlers)
        http_middlewares.append(self.exception_middleware)

        if cors_config is not None:
            http_middlewares.append(allow_cors(**cors_config))

        self.router = Router(routes, http_middlewares, socket_middlewares)

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

    def on_startup(self, func: LifespanCallbackTypeVar) -> LifespanCallbackTypeVar:
        self.lifespan.on_startup.append(func)
        return func

    def on_shutdown(self, func: LifespanCallbackTypeVar) -> LifespanCallbackTypeVar:
        self.lifespan.on_shutdown.append(func)
        return func

    async def app(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope_type: Literal["lifespan", "http", "websocket"] = scope["type"]
        return await getattr(self, scope_type)(scope, receive, send)

    async def http(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = self.factory_class.http(scope, receive, send)
        token = request_var.set(request)
        try:
            try:
                path_params, handler = self.router.search("http", request["path"])
                request["path_params"] = path_params
                response = await handler()
            except NoMatchFound:
                http_exception: HTTPException[None] = HTTPException(404)
                error_handler = self.exception_middleware.lookup_handler(http_exception)
                if error_handler is None:
                    raise RuntimeError(
                        "No exception handler found for HTTPException(404)"
                    )
                response = await error_handler(http_exception)

            if isinstance(response, tuple):
                response = self.response_converter(*response)
            else:
                response = self.response_converter(response)

            return await response(scope, receive, send)
        finally:
            await request.close()
            request_var.reset(token)

    async def websocket(self, scope: Scope, receive: Receive, send: Send) -> None:
        websocket = self.factory_class.websocket(scope, receive, send)
        token = websocket_var.set(websocket)
        try:
            path_params, handler = self.router.search("websocket", websocket["path"])
            websocket["path_params"] = path_params
        except NoMatchFound:
            return await websocket.close(1001)
        else:
            return await handler()
        finally:
            websocket_var.reset(token)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope["app"] = self

        await self.app(scope, receive, send)


def create_response_converter(
    converters: Mapping[type, Callable[..., HttpResponse]],
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
    response_converter.register(Files, lambda x: x)
    response_converter.register(Pages, lambda x: x)
    response_converter.register(Subpaths, lambda x: x)
    response_converter.register(BaizeRouter, lambda x: x)
    response_converter.register(Hosts, lambda x: x)
    response_converter.register(dict, JSONResponse)
    response_converter.register(list, JSONResponse)
    response_converter.register(tuple, JSONResponse)
    response_converter.register(bytes, PlainTextResponse)
    response_converter.register(str, PlainTextResponse)
    response_converter.register(AsyncGeneratorType, SendEventResponse)
    response_converter.register(
        PurePath,
        lambda filepath, download_name=None: FileResponse(
            str(filepath), download_name=download_name
        ),
    )
    response_converter.register(URL, RedirectResponse)
    response_converter.register(BaseModel, JSONResponse)

    for type_, converter in converters.items():
        response_converter.register(type_, converter)

    return response_converter
