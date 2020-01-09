import os
import copy
import typing
import asyncio
import traceback
import importlib
from types import ModuleType
from inspect import signature

from starlette.types import Scope, Receive, Send, Message, ASGIApp
from starlette.requests import HTTPConnection, Request
from starlette.websockets import WebSocket, WebSocketClose
from starlette.responses import RedirectResponse
from starlette.background import BackgroundTasks
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.wsgi import WSGIMiddleware
from starlette.exceptions import HTTPException, ExceptionMiddleware

from .types import WSGIApp
from .config import config
from .responses import FileResponse, automatic
from .background import background_tasks_var


async def favicon(scope: Scope, receive: Receive, send: Send) -> None:
    """
    favicon.ico
    """
    if scope["type"] == "http" and os.path.exists(os.path.normpath("favicon.ico")):
        response = FileResponse("favicon.ico")
        await response(scope, receive, send)
        return
    raise HTTPException(404)


class Lifespan:
    def __init__(
        self,
        on_startup: typing.List[typing.Callable] = None,
        on_shutdown: typing.List[typing.Callable] = None,
    ) -> None:
        self.on_startup = [] if on_startup is None else list(on_startup)
        self.on_shutdown = [] if on_shutdown is None else list(on_shutdown)

    def on_event(self, event_type: str) -> typing.Callable:
        """Wrapper add_event_type"""

        def add_event_handler(func: typing.Callable) -> typing.Callable:
            self.add_event_handler(event_type, func)
            return func

        return add_event_handler

    def add_event_handler(self, event_type: str, func: typing.Callable) -> None:
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
            if asyncio.iscoroutinefunction(handler):
                await handler()
            else:
                handler()

    async def shutdown(self) -> None:
        """
        Run any `.on_shutdown` event handlers.
        """
        for handler in self.on_shutdown:
            if asyncio.iscoroutinefunction(handler):
                await handler()
            else:
                handler()

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
        await self.shutdown()
        await send({"type": "lifespan.shutdown.complete"})

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "lifespan"
        await self.lifespan(scope, receive, send)


class Mount:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.apps: typing.Dict[
            str, typing.Tuple[typing.Union[ASGIApp, WSGIApp], str]
        ] = {}

    def append(
        self, route: str, app: typing.Union[ASGIApp, WSGIApp], app_type: str
    ) -> None:
        assert app_type in ("asgi", "wsgi")
        assert route.startswith("/"), "prefix must be start with '/'"
        assert not route.endswith("/"), "prefix can't end with '/'"
        self.apps.update({route: (app, app_type)})

    class DontFoundRoute(Exception):
        pass

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] in ("http", "websocket", "lifespan")

        async def subsend(message: Message) -> None:
            if message["type"] == "http.response.start" and message["status"] == 404:
                raise self.DontFoundRoute()
            return await send(message)

        async def callapp(
            app: typing.Tuple[typing.Union[ASGIApp, WSGIApp], str],
            scope: Scope,
            receive: Receive,
            send: Send,
        ) -> None:
            if app[1] == "asgi":
                await app[0](scope, receive, send)
                return
            elif app[1] == "wsgi":
                if scope["type"] != "http":
                    raise self.DontFoundRoute()

                wsgi_app = WSGIMiddleware(app[0])
                await wsgi_app(scope, receive, send)
                return

        if scope["type"] in ("http", "websocket"):
            path = scope["path"]
            root_path = scope.get("root_path", "")

            # Call into a submounted app, if one exists.
            for path_prefix, app in self.apps.items():
                if path.startswith(path_prefix):
                    subscope = copy.deepcopy(scope)
                    subscope["path"] = path[len(path_prefix) :]
                    subscope["root_path"] = root_path + path_prefix
                    try:
                        await callapp(app, subscope, receive, subsend)
                        return
                    except self.DontFoundRoute:
                        pass

        await self.app(scope, receive, send)


class Filepath:
    def __init__(self) -> None:
        self.lifespan = Lifespan()

    @classmethod
    def get_path(cls, uri: str) -> typing.Optional[str]:
        """
        translate uri to module path

        if file not found, return None
        """
        if uri.endswith("/"):
            uri += "index"

        filepath = uri[1:].strip(".")
        filepath = filepath.replace("-", "_")

        # judge python file
        abspath = os.path.join(config.path, "views", filepath + ".py")
        if not os.path.exists(abspath):
            return None

        pathlist = filepath.split("/")
        pathlist.insert(0, "views")
        return ".".join(pathlist)

    @classmethod
    def get_views(cls) -> typing.Iterator[typing.Tuple[ModuleType, str]]:
        """
        return all (Module, uri)
        """
        views_path = os.path.join(config.path, "views")

        for root, _, files in os.walk(views_path):
            for file in files:
                if not file.endswith(".py"):
                    continue
                if file == "__init__.py":
                    continue
                abspath = os.path.join(root, file)
                relpath = os.path.relpath(abspath, config.path).replace("\\", "/")

                module = importlib.import_module(relpath.replace("/", ".")[:-3])

                uri = relpath[len("views") : -3]

                if uri.endswith("/index"):
                    uri = uri[:-5]

                yield module, uri

    @classmethod
    def get_view(cls, uri: str) -> ModuleType:
        path = cls.get_path(uri)
        if path is None:
            raise ModuleNotFoundError(uri)
        return importlib.import_module(path)

    @classmethod
    def get_pathlist(cls, uri: str) -> typing.List[str]:
        path = cls.get_path(uri)
        if path is None:
            raise HTTPException(404)
        return path.split(".")

    async def http(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive)
        pathlist = self.get_pathlist(request.url.path)
        # find http handler
        module_path = ".".join(pathlist)
        module = importlib.import_module(module_path)

        if not hasattr(module, "HTTP"):
            raise HTTPException(404)
        get_response = module.HTTP

        try:
            # set background tasks contextvar
            token = background_tasks_var.set(BackgroundTasks())

            # call middleware
            for deep in range(len(pathlist), 0, -1):
                module = importlib.import_module(".".join(pathlist[:deep]))
                if not hasattr(module, "Middleware"):
                    continue
                get_response = module.Middleware(get_response)

            # get response
            response = await get_response(request)
            if isinstance(response, tuple):
                response = automatic(*response)
            else:
                response = automatic(response)

            await response(scope, receive, send)
        finally:
            await background_tasks_var.get()()
            background_tasks_var.reset(token)

    async def websocket(self, scope: Scope, receive: Receive, send: Send) -> None:
        websocket = WebSocket(scope, receive=receive, send=send)
        pathlist = self.get_pathlist(websocket.url.path)
        # find websocket handler
        module_path = ".".join(pathlist)
        module = importlib.import_module(module_path)
        if not hasattr(module, "Socket"):
            raise HTTPException(404)
        handler = module.Socket
        await handler(websocket)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            http_info = HTTPConnection(scope)
            uri = http_info.url.path
            if uri.endswith("/index"):
                response = RedirectResponse(
                    http_info.url.replace(path=f'{uri[:-len("/index")]}'),
                    status_code=301,
                )
            elif not config.ALLOW_UNDERLINE and "_" in uri:  # Google SEO
                response = RedirectResponse(
                    http_info.url.replace(path=f'{uri.replace("_", "-")}'),
                    status_code=301,
                )

        try:
            await response(scope, receive, send)
        except NameError:
            await getattr(self, scope["type"])(scope, receive, send)


class Index:
    def __init__(self, debug: bool = False) -> None:
        self._debug = debug
        self.app = Filepath()
        self.childapps = Mount(self.app)
        self.exception_middleware = ExceptionMiddleware(self.childapps, debug=debug)
        self.error_middleware = ServerErrorMiddleware(
            self.exception_middleware, debug=debug
        )

    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, value: bool) -> None:
        self._debug = value
        self.exception_middleware.debug = value
        self.error_middleware.debug = value

    def add_middleware(self, middleware_class: type, **kwargs: typing.Any) -> None:
        self.error_middleware.app = middleware_class(
            self.error_middleware.app, **kwargs
        )

    def add_exception_handler(
        self,
        exc_class_or_status_code: typing.Union[int, typing.Type[Exception]],
        handler: typing.Callable,
    ) -> None:
        if exc_class_or_status_code in (500, Exception):
            self.error_middleware.handler = handler
        else:
            self.exception_middleware.add_exception_handler(
                exc_class_or_status_code, handler
            )

    def add_event_handler(self, event_type: str, func: typing.Callable) -> None:
        self.app.lifespan.add_event_handler(event_type, func)

    def on_event(self, event_type: str) -> typing.Callable:
        return self.app.lifespan.on_event(event_type)

    def exception_handler(
        self, exc_class_or_status_code: typing.Union[int, typing.Type[Exception]]
    ) -> typing.Callable:
        def decorator(func: typing.Callable) -> typing.Callable:
            self.add_exception_handler(exc_class_or_status_code, func)
            return func

        return decorator

    def middleware(self, middleware_type: str) -> typing.Callable:
        assert (
            middleware_type == "http"
        ), 'Currently only middleware("http") is supported.'

        def decorator(func: typing.Callable) -> typing.Callable:
            self.add_middleware(BaseHTTPMiddleware, dispatch=func)
            return func

        return decorator

    def mount(
        self, route: str, app: typing.Union[ASGIApp, WSGIApp], app_type: str
    ) -> None:
        self.childapps.append(route, app, app_type)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope["app"] = self
        await self.error_middleware(scope, receive, send)
