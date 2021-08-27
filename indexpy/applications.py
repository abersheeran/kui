from __future__ import annotations

import copy
import dataclasses
import functools
import inspect
import sys
import traceback
from functools import reduce
from pathlib import PurePath
from types import AsyncGeneratorType
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    NoReturn,
    Optional,
    Type,
    TypeVar,
    Union,
)

if sys.version_info[:2] < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from baize.asgi import Receive, Scope, Send
from baize.datastructures import URL
from baize.typing import ASGIApp

from .debug import DebugMiddleware
from .exceptions import ErrorView, ExceptionContextManager, HTTPException
from .requests import HttpRequest, WebSocket, request_var, websocket_var
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

NoArgumentCallable = Union[Callable[[], Any], Callable[[], Awaitable[Any]]]

T_NoArgumentCallable = TypeVar("T_NoArgumentCallable", bound=NoArgumentCallable)


@dataclasses.dataclass
class Lifespan:
    on_startup: List[NoArgumentCallable] = dataclasses.field(default_factory=list)
    on_shutdown: List[NoArgumentCallable] = dataclasses.field(default_factory=list)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Handle ASGI lifespan messages, which allows us to manage application
        startup and shutdown events.
        """
        message = await receive()
        assert message["type"] == "lifespan.startup"
        try:
            for handler in self.on_startup:
                result = handler()
                if inspect.isawaitable(result):
                    await result
        except BaseException:
            msg = traceback.format_exc()
            await send({"type": "lifespan.startup.failed", "message": msg})
            raise
        await send({"type": "lifespan.startup.complete"})

        message = await receive()
        assert message["type"] == "lifespan.shutdown"
        try:
            for handler in self.on_shutdown:
                result = handler()
                if inspect.isawaitable(result):
                    await result
        except BaseException:
            msg = traceback.format_exc()
            await send({"type": "lifespan.shutdown.failed", "message": msg})
            raise
        await send({"type": "lifespan.shutdown.complete"})


@dataclasses.dataclass
class FactoryClass:
    http: Type[HttpRequest] = HttpRequest
    websocket: Type[WebSocket] = WebSocket


class Index:
    debug: ImmutableAttribute[bool] = ImmutableAttribute()
    state: ImmutableAttribute[State] = ImmutableAttribute()

    def __init__(
        self,
        *,
        debug: bool = False,
        templates: Optional[BaseTemplates] = None,
        on_startup: List[NoArgumentCallable] = [],
        on_shutdown: List[NoArgumentCallable] = [],
        routes: Iterable[BaseRoute] = [],
        exception_handlers: Dict[int | Type[Exception], ErrorView] = {},
        factory_class: FactoryClass = FactoryClass(),
        response_converters: Dict[type, Callable[..., HttpResponse]] = {},
    ) -> None:
        self.debug = debug
        self.state = State()
        self.response_converter = create_response_converter(response_converters)
        self.should_exit = False
        self.factory_class = factory_class
        self.templates = templates
        self.router = Router(routes)
        self.lifespan = Lifespan(copy.copy(on_startup), copy.copy(on_shutdown))
        self.exception_contextmanager = ExceptionContextManager(exception_handlers)
        self._asgi_middlewares: List[F] = []
        self.app_with_middlewares = self.build_app_with_middlewares()

        if self.debug:
            self.add_middleware(DebugMiddleware)

    def build_app_with_middlewares(self) -> ASGIApp:
        return reduce(lambda a, m: m(a), reversed(self._asgi_middlewares), self.app)

    def add_middleware(self, middleware_class: type, **options: Any) -> None:
        """
        Add ASGI middleware
        """
        self._asgi_middlewares.append(F(middleware_class, **options))
        self.app_with_middlewares = self.build_app_with_middlewares()

    def add_exception_handler(
        self, exc_class_or_status_code: int | Type[Exception], handler: ErrorView
    ) -> None:
        self.exception_contextmanager.add_exception_handler(
            exc_class_or_status_code, handler
        )

    def exception_handler(
        self, exc_class_or_status_code: int | Type[Exception]
    ) -> Callable[[ErrorView], ErrorView]:
        def decorator(func: ErrorView) -> ErrorView:
            self.add_exception_handler(exc_class_or_status_code, func)
            return func

        return decorator

    def on_startup(self, func: T_NoArgumentCallable) -> T_NoArgumentCallable:
        self.lifespan.on_startup.append(func)
        return func

    def on_shutdown(self, func: T_NoArgumentCallable) -> T_NoArgumentCallable:
        self.lifespan.on_shutdown.append(func)
        return func

    async def app(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope_type: Literal["lifespan", "http", "websocket"] = scope["type"]
        return await getattr(self, scope_type)(scope, receive, send)

    async def http(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = self.factory_class.http(scope, receive, send)
        token = request_var.set(request)
        try:
            async with self.exception_contextmanager:
                try:
                    path_params, handler = self.router.search("http", request["path"])
                    request["path_params"] = path_params
                    response = convert_response(await handler())
                except NoMatchFound:
                    raise HTTPException(404)
                else:
                    return await response(scope, receive, send)
        finally:
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

        await self.app_with_middlewares(scope, receive, send)


def create_response_converter(
    converters: Dict[type, Callable[..., HttpResponse]]
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
    response_converter.register(
        dict,
        lambda content, status=200, headers=None: JSONResponse(
            content, status, headers
        ),
    )
    response_converter.register(
        list,
        lambda content, status=200, headers=None: JSONResponse(
            content, status, headers
        ),
    )
    response_converter.register(
        tuple,
        lambda content, status=200, headers=None: JSONResponse(
            content, status, headers
        ),
    )
    response_converter.register(
        bytes,
        lambda content, status=200, headers=None: PlainTextResponse(
            content, status, headers
        ),
    )
    response_converter.register(
        str,
        lambda content, status=200, headers=None: PlainTextResponse(
            content, status, headers
        ),
    )
    response_converter.register(
        AsyncGeneratorType,
        lambda content, status=200, headers=None: SendEventResponse(
            content, status, headers
        ),
    )
    response_converter.register(
        PurePath,
        lambda filepath, download_name=None: FileResponse(
            str(filepath), download_name=download_name
        ),
    )
    response_converter.register(
        URL,
        lambda url, status=307, headers=None: RedirectResponse(url, status, headers),
    )

    for type_, converter in converters.items():
        response_converter.register(type_, converter)

    return response_converter
