from __future__ import annotations

import copy
import dataclasses
import inspect
import traceback
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from baize.asgi import ASGIApp, Receive, Scope, Send
from baize.typing import Literal
from baize.utils import cached_property
from pydantic.dataclasses import dataclass

from .debug import ServerErrorMiddleware
from .exceptions import ExceptionMiddleware, HTTPException
from .requests import Request, WebSocket, request, request_var, websocket, websocket_var
from .responses import convert_response
from .routing.routes import BaseRoute, NoMatchFound, Router
from .templates import BaseTemplates
from .utils import State


@dataclasses.dataclass
class Lifespan:
    on_startup: List[Callable[[], Any]] = dataclasses.field(default_factory=list)
    on_shutdown: List[Callable[[], Any]] = dataclasses.field(default_factory=list)

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


CallableObject = TypeVar("CallableObject", bound=Callable)


class Index:
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
        self.factory_class = factory_class
        self.templates = templates
        self.router = Router(routes)
        self.lifespan = Lifespan(copy.copy(on_startup), copy.copy(on_shutdown))
        self.exception_handlers = copy.copy(exception_handlers)
        self.asgiapp = self.build_app()

    @property
    def debug(self) -> bool:
        return self.__dict__.get("debug", False)

    @debug.setter
    def debug(self, value: bool) -> None:
        self.__dict__["debug"] = bool(value)
        self.rebuild_app()

    def rebuild_app(self) -> None:
        self.asgiapp = self.build_app()

    def build_app(self) -> ASGIApp:
        error_handler = None
        exception_handlers = {}

        for key, value in self.exception_handlers.items():
            if key in (500, Exception):
                error_handler = value
            else:
                exception_handlers[key] = value

        if not hasattr(self, "_http"):
            self._http = self.http
        self.http = ExceptionMiddleware(self._http, handlers=exception_handlers)

        return ServerErrorMiddleware(
            app=self.app, handler=error_handler, debug=self.debug
        )

    def add_exception_handler(
        self,
        exc_class_or_status_code: Union[int, Type[Exception]],
        handler: Callable,
    ) -> None:
        self.exception_handlers[exc_class_or_status_code] = handler
        self.rebuild_app()

    def exception_handler(
        self, exc_class_or_status_code: Union[int, Type[Exception]]
    ) -> Callable[[CallableObject], CallableObject]:
        def decorator(func: CallableObject) -> CallableObject:
            self.add_exception_handler(exc_class_or_status_code, func)
            return func

        return decorator

    def on_startup(self, func: CallableObject) -> CallableObject:
        self.lifespan.on_startup.append(func)
        return func

    def on_shutdown(self, func: CallableObject) -> CallableObject:
        self.lifespan.on_shutdown.append(func)
        return func

    @cached_property
    def state(self) -> State:
        return State()

    async def app(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope_type: Literal["lifespan", "http", "websocket"] = scope["type"]

        if scope_type == "lifespan":
            return await self.lifespan(scope, receive, send)

        if scope_type == "http":
            connection = self.factory_class.http(scope, receive, send)
            contextvar = request_var
        elif scope_type == "websocket":
            connection = self.factory_class.websocket(scope, receive, send)
            contextvar = websocket_var

        try:
            token = contextvar.set(connection)
            return await getattr(self, scope_type)(connection)
        finally:
            contextvar.reset(token)

    async def http(self) -> None:
        try:
            path_params, handler = self.router.search("http", request["path"])
            request._scope["path_params"] = path_params
        except NoMatchFound:
            raise HTTPException(404)
        else:
            response = convert_response(await handler())
            return await response(request._scope, request._receive, request._send)

    async def websocket(self) -> None:
        try:
            path_params, handler = self.router.search("websocket", websocket["path"])
            websocket._scope["path_params"] = path_params
        except NoMatchFound:
            return await websocket.close(1001)
        else:
            return await handler()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope["app"] = self

        await self.asgiapp(scope, receive, send)
