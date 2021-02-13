from __future__ import annotations

import copy
import dataclasses
import inspect
import traceback
from functools import reduce
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from pydantic.dataclasses import dataclass
from starlette.middleware import Middleware
from starlette.status import WS_1001_GOING_AWAY
from starlette.websockets import WebSocketClose

from .http.debug import ServerErrorMiddleware
from .http.exceptions import ExceptionMiddleware, HTTPException
from .http.request import Request
from .http.templates import BaseTemplates
from .http.view import only_allow
from .routing.routes import BaseRoute, NoMatchFound, Router
from .typing import ASGIApp, Receive, Scope, Send
from .utils import F, State, cached_property
from .websocket.request import WebSocket


@dataclasses.dataclass
class Lifespan:
    on_startup: List[Callable] = dataclasses.field(default_factory=list)
    on_shutdown: List[Callable] = dataclasses.field(default_factory=list)

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


@dataclass
class FactoryClass:
    http: Type[Request] = Request
    websocket: Type[WebSocket] = WebSocket


class Application:
    def __init__(
        self,
        *,
        templates: Optional[BaseTemplates] = None,
        routes: List[BaseRoute] = [],
        factory_class: FactoryClass = FactoryClass(),
    ) -> None:
        self.factory_class = factory_class
        self.templates = templates
        self.router = Router(routes)

    @cached_property
    def state(self) -> State:
        return State()

    async def app(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        App without ASGI middleware.
        """
        if scope["type"] == "lifespan":
            raise NotImplementedError(
                "Maybe you want to use `Index` replace `Application`"
            )

        handler: Optional[ASGIApp] = None

        try:
            path_params, handler = self.router.search(scope["type"], scope["path"])
            scope["path_params"] = path_params
        except NoMatchFound:
            pass

        if handler is None:
            if scope["type"] == "http":
                raise HTTPException(404)
            handler = WebSocketClose(WS_1001_GOING_AWAY)

        return await handler(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope["app"] = self

        await self.app(scope, receive, send)


CallableVar = TypeVar("CallableVar", bound=Callable)


class Index(Application):
    def __init__(
        self,
        *,
        debug: bool = False,
        templates: Optional[BaseTemplates] = None,
        on_startup: List[Callable] = [],
        on_shutdown: List[Callable] = [],
        routes: List[BaseRoute] = [],
        middlewares: List[Middleware] = [],
        exception_handlers: Dict[Union[int, Type[Exception]], Callable] = {},
        factory_class: FactoryClass = FactoryClass(),
    ) -> None:
        self.__debug = debug
        super().__init__(
            templates=templates, routes=routes, factory_class=factory_class
        )
        self.lifespan = Lifespan(
            on_startup=[only_allow.clear] + copy.copy(on_startup),
            on_shutdown=copy.copy(on_shutdown),
        )
        self.user_middlewares = copy.copy(middlewares)
        self.exception_handlers = copy.copy(exception_handlers)

        # Initial ASGI application
        self.asgiapp: ASGIApp = self.build_app()

    @property
    def debug(self) -> bool:
        return self.__debug

    def rebuild_asgiapp(self) -> None:
        self.asgiapp = self.build_app()

    def build_app(self) -> ASGIApp:
        error_handler = None
        exception_handlers = {}

        for key, value in self.exception_handlers.items():
            if key in (500, Exception):
                error_handler = value
            else:
                exception_handlers[key] = value

        return ServerErrorMiddleware(
            app=reduce(
                lambda app, middleware: middleware(app),
                [F(cls, **options) for cls, options in reversed(self.user_middlewares)],
                ExceptionMiddleware(app=self.app, handlers=exception_handlers),
            ),
            handler=error_handler,
            debug=self.debug,
        )

    def add_middleware(self, middleware_class: type, **options: Any) -> None:
        self.user_middlewares.insert(0, Middleware(middleware_class, **options))
        self.rebuild_asgiapp()

    def add_exception_handler(
        self,
        exc_class_or_status_code: Union[int, Type[Exception]],
        handler: Callable,
    ) -> None:
        self.exception_handlers[exc_class_or_status_code] = handler
        self.rebuild_asgiapp()

    def exception_handler(
        self, exc_class_or_status_code: Union[int, Type[Exception]]
    ) -> Callable[[CallableVar], CallableVar]:
        def decorator(func: CallableVar) -> CallableVar:
            self.add_exception_handler(exc_class_or_status_code, func)
            return func

        return decorator

    def on_startup(self, func: CallableVar) -> CallableVar:
        self.lifespan.on_startup.append(func)
        return func

    def on_shutdown(self, func: CallableVar) -> CallableVar:
        self.lifespan.on_shutdown.append(func)
        return func

    async def app(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        App without ASGI middleware.
        """
        if scope["type"] == "lifespan":
            await self.lifespan(scope, receive, send)
        else:
            await super().app(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope["app"] = self

        await self.asgiapp(scope, receive, send)
