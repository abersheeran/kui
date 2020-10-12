import copy
import inspect
import logging
import traceback
import typing

from jinja2 import ChoiceLoader, Environment, FileSystemLoader, PackageLoader
from pydantic.dataclasses import dataclass
from starlette.datastructures import URL
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.status import WS_1001_GOING_AWAY
from starlette.websockets import WebSocketClose

from .config import Config
from .http import responses
from .http.debug import ServerErrorMiddleware
from .http.exceptions import ExceptionMiddleware, HTTPException
from .http.request import Request
from .http.responses import RedirectResponse, Response
from .routing.routes import BaseRoute, NoMatchFound, Router
from .types import ASGIApp, Literal, Message, Receive, Scope, Send
from .websocket.request import WebSocket

logger = logging.getLogger(__name__)


def try_html(request: Request) -> typing.Optional[Response]:
    """
    try find html through TemplateResponse
    """
    try:
        return responses.TemplateResponse(
            request["path"] + ".html", {"request": request}
        )
    except LookupError:
        return None


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
        templates: typing.Iterable[str] = (),
        try_html: bool = True,
        on_startup: typing.List[typing.Callable] = [],
        on_shutdown: typing.List[typing.Callable] = [],
        routes: typing.List[BaseRoute] = [],
        middlewares: typing.List[Middleware] = [],
        exception_handlers: typing.Dict[
            typing.Union[int, typing.Type[Exception]], typing.Callable
        ] = {},
        factory_class: FactoryClass = FactoryClass(),
    ) -> None:
        self.factory_class = factory_class
        self.router = Router(routes)

        templates_loaders: typing.List[
            typing.Union[FileSystemLoader, PackageLoader]
        ] = []
        for template_path in templates:
            if ":" in template_path:  # package: "package:path"
                package_name, package_path = template_path.split(":", maxsplit=1)
                templates_loaders.append(PackageLoader(package_name, package_path))
            else:  # normal: "path"
                templates_loaders.append(FileSystemLoader(template_path))

        self.jinja_env = Environment(
            loader=ChoiceLoader(templates_loaders),
            enable_async=True,
        )
        self.try_html = try_html

        # Shallow copy list to prevent memory leak.
        self.lifespan = Lifespan(
            on_startup=copy.copy(on_startup), on_shutdown=copy.copy(on_shutdown)
        )

        self.user_middlewares = copy.copy(middlewares)
        self.exception_handlers = copy.copy(exception_handlers)

        self.asgiapp: ASGIApp = self.build_app()

    def rebuild_app(self) -> None:
        self.asgiapp = self.build_app()

    def build_app(self) -> ASGIApp:
        config = Config()
        error_handler = None
        exception_handlers = {}

        for key, value in self.exception_handlers.items():
            if key in (500, Exception):
                error_handler = value
            else:
                exception_handlers[key] = value

        middlewares = []

        if "*" in config.ALLOWED_HOSTS:
            middlewares.append(
                Middleware(TrustedHostMiddleware, allowed_hosts=config.ALLOWED_HOSTS)
            )

        middlewares.append(
            Middleware(ServerErrorMiddleware, handler=error_handler, debug=config.DEBUG)
        )

        if (
            config.CORS_ALLOW_ORIGIN_REGEX is not None
            or len(config.CORS_ALLOW_ORIGINS) > 0
        ):
            middlewares.append(
                Middleware(
                    CORSMiddleware,
                    allow_origins=config.CORS_ALLOW_ORIGINS,
                    allow_methods=config.CORS_ALLOW_METHODS,
                    allow_headers=config.CORS_ALLOW_HEADERS,
                    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
                    allow_origin_regex=config.CORS_ALLOW_ORIGIN_REGEX,
                    expose_headers=config.CORS_EXPOSE_HEADERS,
                    max_age=config.CORS_MAX_AGE,
                )
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
            if scope["type"] == "http" and self.try_html:
                # only html, no middleware/background tasks or other anything
                handler = try_html(self.factory_class.http(scope, receive, send))

        if handler is None:
            if scope["type"] == "http":
                raise HTTPException(404)
            handler = WebSocketClose(WS_1001_GOING_AWAY)

        return await handler(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope["app"] = self

        if (
            scope["type"] in ("http", "websocket")
            and Config().FORCE_SSL
            and scope["scheme"] in ("http", "ws")
        ):  # Force jump to https/wss
            url = URL(scope=scope)
            redirect_scheme = {"http": "https", "ws": "wss"}[url.scheme]
            netloc = url.hostname if url.port in (80, 443) else url.netloc
            url = url.replace(scheme=redirect_scheme, netloc=netloc)
            response = RedirectResponse(url, status_code=301)
            return await response(scope, receive, send)

        await self.asgiapp(scope, receive, send)


class Dispatcher:
    def __init__(
        self,
        default_app: ASGIApp,
        *apps: typing.Tuple[str, ASGIApp],
        handle404: ASGIApp = Response(b"", 404),
    ) -> None:
        self.default_app = default_app
        for prefix, app in apps:
            assert prefix.startswith("/"), "prefix must be start with '/'"
            assert not prefix.endswith("/"), "prefix can't end with '/'"
        self.apps = apps
        self.handle404 = handle404

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
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
            for path_prefix, app in filter(
                lambda item: path.startswith(item[0] + "/"), self.apps
            ):
                subscope = copy.copy(scope)
                subscope["path"] = path[len(path_prefix) :]
                subscope["root_path"] = root_path + path_prefix
                try:
                    return await app(subscope, subreceive, subsend)
                except NoMatchFound:
                    if has_received:  # has call received
                        return await self.handle404(scope, receive, send)

        await self.default_app(scope, receive, send)
