import os
import copy
import typing
import asyncio
import traceback
import importlib
import warnings
from types import ModuleType

from starlette.types import Scope, Receive, Send, ASGIApp
from starlette.status import WS_1001_GOING_AWAY
from starlette.requests import URL, Request
from starlette.websockets import WebSocket, WebSocketClose
from starlette.responses import RedirectResponse
from starlette.middleware import Middleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.wsgi import WSGIMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.exceptions import HTTPException, ExceptionMiddleware

from .types import WSGIApp
from .utils import Singleton
from .config import here, Config
from .responses import FileResponse, automatic
from .background import (
    BackgroundTasks,
    after_response_tasks_var,
    finished_response_tasks_var,
)


class Lifespan:
    def __init__(self) -> None:
        self.on_startup: typing.Dict[str, typing.Callable] = {}
        self.on_shutdown: typing.Dict[str, typing.Callable] = {}

    def on_event(self, event_type: str) -> typing.Callable:
        """Wrapper add_event_type"""

        def add_event_handler(func: typing.Callable) -> typing.Callable:
            self.add_event_handler(event_type, func)
            return func

        return add_event_handler

    def add_event_handler(self, event_type: str, func: typing.Callable) -> None:
        if event_type == "startup":
            self.on_startup[func.__qualname__] = func
        elif event_type == "shutdown":
            self.on_shutdown[func.__qualname__] = func
        else:
            raise ValueError("event_type must be in ('startup', 'shutdown')")

    async def startup(self) -> None:
        """
        Run any `.on_startup` event handlers.
        """
        for handler in self.on_startup.values():
            if asyncio.iscoroutinefunction(handler):
                await handler()
            else:
                handler()

    async def shutdown(self) -> None:
        """
        Run any `.on_shutdown` event handlers.
        """
        for handler in self.on_shutdown.values():
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


class IndexFile:
    def __init__(self, module_name: str, basepath: str) -> None:
        self.module_name = module_name
        self.basepath = basepath

    def split_uri(self, uri: str) -> typing.List[str]:
        """
        convert uri to file string corresponding to index.py
        """
        if uri.endswith("/"):
            uri += "index"

        filepath = uri.strip("./")
        filepath = filepath.replace("-", "_")

        pathlist = filepath.split("/")
        pathlist.insert(0, self.module_name)
        return pathlist

    def get_path(
        self, uri: str
    ) -> typing.Tuple[typing.Optional[str], typing.Optional[str]]:
        """
        translate uri to module name and file abspath

        if file not found, return None
        """
        pathlist = self.split_uri(uri)
        abspath = os.path.join(self.basepath, *pathlist) + ".py"
        if not os.path.exists(abspath):
            return None, None
        return ".".join(pathlist), abspath

    def get_uri(self, filepath: str) -> typing.Optional[str]:
        """
        translate file abspath to uri
        """
        assert filepath.endswith(".py")

        relpath = os.path.relpath(
            filepath, os.path.join(self.basepath, self.module_name)
        )
        if relpath.startswith("."):
            return None

        uri = "/" + relpath.replace("\\", "/")[:-3]

        if uri.endswith("/index"):
            uri = uri[:-5]

        return uri

    def get_views(self) -> typing.Iterator[typing.Tuple[ModuleType, str]]:
        """
        return all (Module, uri)
        """
        views_path = os.path.join(self.basepath, self.module_name)

        for root, _, files in os.walk(views_path):
            try:
                files.remove("index.py")
                files.insert(0, "index.py")
            except ValueError:  # file not exists
                pass

            for file in filter(
                lambda file: file.endswith(".py") and file != "__init__.py", files
            ):
                abspath = os.path.join(root, file)
                uri = self.get_uri(abspath)
                if uri is None:
                    continue
                module = self.get_view(uri)
                if module is None:
                    continue
                yield module, uri

    def get_view(self, uri: str) -> typing.Optional[ModuleType]:
        module_name, filepath = self.get_path(uri)
        if module_name is None or filepath is None:
            return None
        # # Not thread-safe, temporarily commented
        # spec = importlib.util.spec_from_file_location(module_name, filepath)
        # module = importlib.util.module_from_spec(spec)
        # sys.modules[module_name] = module
        # spec.loader.exec_module(module)  # type: ignore
        # return module
        return importlib.import_module(module_name)

    async def http(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive)
        pathlist = self.split_uri(request.url.path)

        module = self.get_view(request.url.path)
        if module is None or not hasattr(module, "HTTP"):
            raise HTTPException(404)

        get_response = getattr(module, "HTTP")

        try:
            # set background tasks contextvar
            after_response_tasks_token = after_response_tasks_var.set(BackgroundTasks())
            finished_response_tasks_token = finished_response_tasks_var.set(
                BackgroundTasks()
            )
            # call middleware
            for deep in range(len(pathlist), 0, -1):
                module = importlib.import_module(".".join(pathlist[:deep]))
                if not hasattr(module, "Middleware"):
                    continue
                get_response = getattr(module, "Middleware")(get_response)

            # get response
            response = await get_response(request)
            if isinstance(response, tuple):
                response = automatic(*response)
            else:
                response = automatic(response)
            response.background = after_response_tasks_var.get()
            await response(scope, receive, send)
        finally:
            after_response_tasks_var.reset(after_response_tasks_token)

            run_finished_response_tasks = finished_response_tasks_var.get()
            finished_response_tasks_var.reset(finished_response_tasks_token)
            await run_finished_response_tasks()

    async def websocket(self, scope: Scope, receive: Receive, send: Send) -> None:
        websocket = WebSocket(scope, receive=receive, send=send)

        module = self.get_view(websocket.url.path)
        if module is None or not hasattr(module, "Socket"):
            await WebSocketClose(WS_1001_GOING_AWAY)(scope, receive, send)
            return

        await getattr(module, "Socket")(websocket)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        handler = getattr(self, scope["type"])

        if scope["type"] in ("http", "websocket"):
            url = URL(scope=scope)
            path = url.path
            if path.endswith("/index"):
                handler = RedirectResponse(
                    url.replace(path=f'{path[:-len("/index")]}'), status_code=301,
                )
            elif "_" in path and not Config().ALLOW_UNDERLINE:
                handler = RedirectResponse(
                    url.replace(path=f'{path.replace("_", "-")}'), status_code=301,
                )
            elif path == "/favicon.ico":
                if os.path.exists(os.path.normpath("favicon.ico")):
                    handler = FileResponse("favicon.ico")

        await handler(scope, receive, send)


class Index(metaclass=Singleton):
    def __init__(self) -> None:
        self.indexfile = IndexFile("views", here)
        self.lifespan = Lifespan()
        self.mount_apps: typing.Dict[str, ASGIApp] = {}
        self.user_middlewares: typing.List[Middleware] = []
        self.exception_handlers: typing.Dict[
            typing.Union[int, typing.Type[Exception]], typing.Callable
        ] = {}

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

        middlewares = [
            Middleware(GZipMiddleware),
            Middleware(
                CORSMiddleware,
                allow_origins=config.CORS_ALLOW_ORIGINS,
                allow_methods=config.CORS_ALLOW_METHODS,
                allow_headers=config.CORS_ALLOW_HEADERS,
                allow_credentials=config.CORS_ALLOW_CREDENTIALS,
                allow_origin_regex=config.CORS_ALLOW_ORIGIN_REGEX,
                expose_headers=config.CORS_EXPOSE_HEADERS,
                max_age=config.CORS_MAX_AGE,
            ),
            Middleware(
                ServerErrorMiddleware, handler=error_handler, debug=config.DEBUG
            ),
        ] + self.user_middlewares

        if config.FORCE_SSL:
            middlewares.append(Middleware(HTTPSRedirectMiddleware))

        middlewares += [
            Middleware(TrustedHostMiddleware, allowed_hosts=config.ALLOWED_HOSTS),
            Middleware(
                ExceptionMiddleware, handlers=exception_handlers, debug=config.DEBUG
            ),
        ]

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

    def add_event_handler(self, event_type: str, func: typing.Callable) -> None:
        # TODO delete this on 0.9
        warnings.warn(
            "`add_event_handler` has been deprecated, will be remove on 0.9, please use on_startup/on_shutdown."
        )
        self.lifespan.add_event_handler(event_type, func)

    def on_event(self, event_type: str) -> typing.Callable:
        # TODO delete this on 0.9
        warnings.warn(
            "`on_event` has been deprecated, will be remove on 0.9, please use on_startup/on_shutdown."
        )
        return self.lifespan.on_event(event_type)

    def mount(
        self, route: str, app: typing.Union[ASGIApp, WSGIApp], app_type: str
    ) -> None:
        assert app_type in ("asgi", "wsgi")
        if route != "":  # allow use "" to mount app
            assert route.startswith("/"), "prefix must be start with '/'"
            assert not route.endswith("/"), "prefix can't end with '/'"
        if app_type == "wsgi":
            app = WSGIMiddleware(app)
        app = typing.cast(ASGIApp, app)
        self.mount_apps.update({route: app})

    async def app(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            path = scope["path"]
            root_path = scope.get("root_path", "")

            # Call into a submounted app, if one exists.
            for path_prefix, app in self.mount_apps.items():
                if not path.startswith(path_prefix + "/"):
                    continue
                if isinstance(app, WSGIMiddleware):
                    if scope["type"] != "http":
                        continue
                subscope = copy.deepcopy(scope)
                subscope["path"] = path[len(path_prefix) :]
                subscope["root_path"] = root_path + path_prefix
                await app(subscope, receive, send)
                return

            await self.indexfile(scope, receive, send)

        elif scope["type"] == "lifespan":
            await self.lifespan(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self.asgiapp(scope, receive, send)
