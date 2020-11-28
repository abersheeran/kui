import copy
import inspect
import traceback
import typing

from pydantic.dataclasses import dataclass
from starlette.middleware import Middleware
from starlette.status import WS_1001_GOING_AWAY
from starlette.websockets import WebSocketClose

from .types import ASGIApp, Literal, Message, Receive, Scope, Send
from .utils import State, cached_property
from .routing.routes import BaseRoute, NoMatchFound, Router
from .http.debug import ServerErrorMiddleware
from .http.exceptions import ExceptionMiddleware, HTTPException
from .http.request import Request
from .http.responses import Response
from .http.templates import BaseTemplates, Jinja2Templates
from .http.view import only_allow
from .websocket.request import WebSocket


class Lifespan:
    def __init__(
        self,
        on_startup: typing.List[typing.Callable] = None,
        on_shutdown: typing.List[typing.Callable] = None,
    ) -> None:
        self.on_startup = on_startup or []
        self.on_shutdown = on_shutdown or []

    def add_event_handler(
        self, event_type: Literal["startup", "shutdown"], func: typing.Callable
    ) -> None:
        if event_type == "startup":
            self.on_startup.append(func)
        elif event_type == "shutdown":
            self.on_shutdown.append(func)
        else:
            raise ValueError("event_type must be in ('startup', 'shutdown')")

    async def startup(self) -> None:
        """
        Run any `.on_startup` event handlers.
        """
        for handler in self.on_startup:
            result = handler()
            if inspect.isawaitable(result):
                await result

    async def shutdown(self) -> None:
        """
        Run any `.on_shutdown` event handlers.
        """
        for handler in self.on_shutdown:
            result = handler()
            if inspect.isawaitable(result):
                await result

    async def lifespan(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Handle ASGI lifespan messages, which allows us to manage application
        startup and shutdown events.
        """
        message = await receive()
        assert message["type"] == "lifespan.startup"
        try:
            await self.startup()
        except BaseException:
            msg = traceback.format_exc()
            await send({"type": "lifespan.startup.failed", "message": msg})
            raise
        await send({"type": "lifespan.startup.complete"})

        message = await receive()
        assert message["type"] == "lifespan.shutdown"
        try:
            await self.shutdown()
        except BaseException:
            msg = traceback.format_exc()
            await send({"type": "lifespan.shutdown.failed", "message": msg})
            raise
        await send({"type": "lifespan.shutdown.complete"})

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "lifespan"
        await self.lifespan(scope, receive, send)


@dataclass
class FactoryClass:
    http: typing.Type[Request] = Request
    websocket: typing.Type[WebSocket] = WebSocket


class Index:
    def __init__(
        self,
        *,
        debug: bool = False,
        templates: BaseTemplates = Jinja2Templates("templates"),
        on_startup: typing.List[typing.Callable] = [],
        on_shutdown: typing.List[typing.Callable] = [],
        routes: typing.List[BaseRoute] = [],
        middlewares: typing.List[Middleware] = [],
        exception_handlers: typing.Dict[
            typing.Union[int, typing.Type[Exception]], typing.Callable
        ] = {},
        factory_class: FactoryClass = FactoryClass(),
    ) -> None:
        self.__debug = debug
        self.factory_class = factory_class
        self.router = Router(routes)
        self.templates = templates

        # Shallow copy list to prevent memory leak.
        self.lifespan = Lifespan(
            on_startup=copy.copy(on_startup) + [only_allow.clear],
            on_shutdown=copy.copy(on_shutdown),
        )

        self.user_middlewares = copy.copy(middlewares)
        self.exception_handlers = copy.copy(exception_handlers)

        self.asgiapp: ASGIApp = self.build_app()

    @property
    def debug(self) -> bool:
        return self.__debug

    @cached_property
    def state(self) -> State:
        return State()

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

        middlewares = []

        middlewares.append(
            Middleware(ServerErrorMiddleware, handler=error_handler, debug=self.debug)
        )
        middlewares += self.user_middlewares
        middlewares.append(Middleware(ExceptionMiddleware, handlers=exception_handlers))

        app = self.app

        for cls, options in reversed(middlewares):
            app = cls(app=app, **options)
        return app

    def add_middleware(self, middleware_class: type, **options: typing.Any) -> None:
        self.user_middlewares.insert(0, Middleware(middleware_class, **options))
        self.rebuild_app()

    def add_exception_handler(
        self,
        exc_class_or_status_code: typing.Union[int, typing.Type[Exception]],
        handler: typing.Callable,
    ) -> None:
        self.exception_handlers[exc_class_or_status_code] = handler
        self.rebuild_app()

    def exception_handler(
        self, exc_class_or_status_code: typing.Union[int, typing.Type[Exception]]
    ) -> typing.Callable:
        def decorator(func: typing.Callable) -> typing.Callable:
            self.add_exception_handler(exc_class_or_status_code, func)
            return func

        return decorator

    def on_startup(self, func: typing.Callable) -> typing.Callable:
        self.lifespan.add_event_handler("startup", func)
        return func

    def on_shutdown(self, func: typing.Callable) -> typing.Callable:
        self.lifespan.add_event_handler("shutdown", func)
        return func

    async def app(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        App without ASGI middleware.
        """
        if scope["type"] == "lifespan":
            return await self.lifespan(scope, receive, send)

        handler: typing.Optional[ASGIApp] = None

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

        await self.asgiapp(scope, receive, send)


@dataclass
class MountApp:
    prefix: str
    app: ASGIApp
    host: typing.Optional[str] = None


class Dispatcher:
    def __init__(
        self,
        default_app: ASGIApp,
        *apps: MountApp,
        handle404: ASGIApp = Response(b"", 404),
    ) -> None:
        self.default_app = default_app
        for mounted in apps:
            assert mounted.prefix.startswith("/"), "prefix must be start with '/'"
            assert not mounted.prefix.endswith("/"), "prefix can't end with '/'"
        self.apps = apps
        self.handle404 = handle404

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            raw_host: bytes = [kv[1] for kv in scope["headers"] if kv[0] == b"host"][0]
            host = raw_host.decode("latin1")
            path = scope["path"]
            root_path = scope.get("root_path", "")
            has_received = False

            async def subreceive() -> Message:
                nonlocal has_received
                has_received = True
                return await receive()

            async def subsend(message: Message) -> None:
                if (
                    message["type"] == "http.response.start"
                    and message["status"] == 404
                ):
                    raise NoMatchFound()
                await send(message)

            # Call into a mounted app, if one exists.
            for mounted in filter(
                lambda item: (
                    path.startswith(item.prefix + "/")
                    and (item.host is None or item.host == host)
                ),
                self.apps,
            ):
                # This is a bug for mypy, so ignore it.
                application: ASGIApp = mounted.app  # type: ignore
                subscope = copy.copy(scope)
                subscope["path"] = path[len(mounted.prefix) :]
                subscope["root_path"] = root_path + mounted.prefix
                try:
                    return await application(subscope, subreceive, subsend)
                except NoMatchFound:
                    if has_received:
                        return await self.handle404(scope, receive, send)

        await self.default_app(scope, receive, send)
