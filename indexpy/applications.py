from __future__ import annotations

import copy
import dataclasses
import inspect
import traceback
from functools import reduce
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from baize.asgi import Scope, Receive, Send, ASGIApp
from pydantic.dataclasses import dataclass

from .debug import ServerErrorMiddleware
from .exceptions import ExceptionMiddleware, HTTPException
from .templates import BaseTemplates
from .routing.routes import BaseRoute, NoMatchFound, Router
from .requests import Request, WebSocket
from .responses import convert_response
from .utils import State, cached_property


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
        if scope["type"] == "lifespan":
            raise NotImplementedError(
                "Maybe you want to use `Index` replace `Application`"
            )

        connection = getattr(self.factory_class, scope["type"])(scope, receive, send)
        path_params, handler = self.router.search(scope["type"], scope["path"])
        scope["path_params"] = path_params
        response = convert_response(await handler(connection))
        return await response(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope["app"] = self

        await self.app(scope, receive, send)


C = TypeVar("C", bound=Callable)


class Index(Application):
    def __init__(
        self,
        *,
        debug: bool = False,
        templates: Optional[BaseTemplates] = None,
        on_startup: List[Callable] = [],
        on_shutdown: List[Callable] = [],
        routes: List[BaseRoute] = [],
        exception_handlers: Dict[Union[int, Type[Exception]], Callable] = {},
        factory_class: FactoryClass = FactoryClass(),
    ) -> None:
        self.debug = debug
        super().__init__(
            templates=templates, routes=routes, factory_class=factory_class
        )
        self.lifespan = Lifespan(
            on_startup=copy.copy(on_startup),
            on_shutdown=copy.copy(on_shutdown),
        )
        self.exception_handlers = copy.copy(exception_handlers)

    def add_exception_handler(
        self,
        exc_class_or_status_code: Union[int, Type[Exception]],
        handler: Callable,
    ) -> None:
        self.exception_handlers[exc_class_or_status_code] = handler
        self.rebuild_asgiapp()

    def exception_handler(
        self, exc_class_or_status_code: Union[int, Type[Exception]]
    ) -> Callable[[C], C]:
        def decorator(func: C) -> C:
            self.add_exception_handler(exc_class_or_status_code, func)
            return func

        return decorator

    def on_startup(self, func: C) -> C:
        self.lifespan.on_startup.append(func)
        return func

    def on_shutdown(self, func: C) -> C:
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
