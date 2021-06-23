from __future__ import annotations

import copy
import dataclasses
import inspect
import sys
import traceback
from functools import reduce
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
)

from baize.typing import ASGIApp

if sys.version_info[:2] < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from baize.asgi import Receive, Scope, Send
from baize.utils import cached_property

from .debug import DebugMiddleware
from .exceptions import ErrorView, ExceptionContextManager, HTTPException
from .requests import HttpRequest, WebSocket, request_var, websocket_var
from .responses import convert_response
from .routing.routes import BaseRoute, NoMatchFound, Router
from .templates import BaseTemplates
from .utils import F, State

NoArgumentCallable = Union[Callable[[], Any], Callable[[], Awaitable[Any]]]


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


T_NoArgumentCallable = TypeVar("T_NoArgumentCallable", bound=NoArgumentCallable)


class Index:
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
    ) -> None:
        self.should_exit = False
        self.__dict__["debug"] = debug
        self.factory_class = factory_class
        self.templates = templates
        self.router = Router(routes)
        self.lifespan = Lifespan(copy.copy(on_startup), copy.copy(on_shutdown))
        self.exception_contextmanager = ExceptionContextManager(exception_handlers)
        self.asgi_middlewares: List[F] = []
        # We expect to be able to catch all code errors, so as an ASGI middleware.
        self.app_with_debug = DebugMiddleware(
            app=self.build_app_with_middlewares(), debug=self.debug
        )

    @property
    def debug(self) -> bool:
        return self.__dict__.get("debug", False)

    @debug.setter
    def debug(self, value: bool) -> None:
        self.__dict__["debug"] = bool(value)
        self.app_with_debug.debug = bool(value)

    def build_app_with_middlewares(self) -> ASGIApp:
        return reduce(lambda a, m: m(a), self.asgi_middlewares, self.app)

    def add_middleware(self, middleware_class: type, **options: Any) -> None:
        """
        Add ASGI middleware
        """
        self.asgi_middlewares.append(F(middleware_class, **options))
        self.app_with_debug.app = self.build_app_with_middlewares()

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

    @cached_property
    def state(self) -> State:
        return State()

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

        await self.app_with_debug(scope, receive, send)
