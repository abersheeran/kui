import os
import sys
import copy
import typing
import logging
import importlib

from starlette.types import Scope, Receive, Send
from starlette.routing import Lifespan
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.websockets import WebSocket, WebSocketClose
from starlette.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.exceptions import HTTPException, ExceptionMiddleware

from .config import Config
from .autoreload import MonitorFile, checkall

logger = logging.getLogger(__name__)
config = Config()

sys.path.insert(0, config.path)


class Filepath:

    def __init__(self):
        self.lifespan = Lifespan()
        self.staticfiles = StaticFiles(
            directory=os.path.join(config.path, 'statics'),
            check_dir=False,
        )

    def get_pathlist(self, uri: str) -> typing.List[str]:
        if uri.endswith("/index"):
            return RedirectResponse(f'/{uri[:-len("/index")]}', status_code=301)

        if uri.endswith("/"):
            uri += "index"

        filepath = uri[1:].strip(".")
        # Google SEO
        if not config.ALLOW_UNDERLINE:
            if "_" in uri:
                return RedirectResponse(f'/{uri.replace("_", "-")}', status_code=301)
            filepath = filepath.replace("-", "_")

        # judge python file
        abspath = os.path.join(config.path, "views", filepath + ".py")
        if not os.path.exists(abspath):
            raise HTTPException(404)

        pathlist = filepath.split("/")
        pathlist.insert(0, 'views')

        return pathlist

    async def http(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive)
        # static files
        if request.url.path.startswith("/static"):
            response = self.staticfiles
            subscope = copy.copy(scope)
            subscope['path'] = subscope['path'][len('/static'):]
            await response(subscope, receive, send)
            return

        pathlist = self.get_pathlist(request.url.path)
        # find http handler
        module_path = ".".join(pathlist)
        module = importlib.import_module(module_path)
        try:
            get_response = module.HTTP()
        except AttributeError:
            raise HTTPException(404)
        # call middleware
        for deep in range(len(pathlist), 0, -1):
            try:
                module = importlib.import_module(".".join(pathlist[:deep]))
                get_response = module.Middleware(get_response)
            except AttributeError:
                continue
        # get response
        response = await get_response(request)
        await response(scope, receive, send)

    async def websocket(self, scope: Scope, receive: Receive, send: Send) -> None:
        websocket = WebSocket(scope, receive=receive, send=send)
        try:
            pathlist = self.get_pathlist(websocket.url.path)
            # find websocket handler
            module_path = ".".join(pathlist)
            module = importlib.import_module(module_path)
            try:
                handler = module.Socket()
            except AttributeError:
                raise HTTPException(404)
        except HTTPException as exception:
            if exception.status_code == 404:
                websocket_close = WebSocketClose()
                await websocket_close(receive, send)
                return
            raise exception
        await handler(websocket)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] in ("http", "websocket", "lifespan")
        await getattr(self, scope["type"])(scope, receive, send)


class Index:
    def __init__(self, debug: bool = False) -> None:
        self._debug = debug
        self.router = Filepath()
        self.exception_middleware = ExceptionMiddleware(self.router, debug=debug)
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
        self.router.lifespan.add_event_handler(event_type, func)

    def on_event(self, event_type: str) -> typing.Callable:
        return self.router.lifespan.on_event(event_type)

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

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope["app"] = self
        await self.error_middleware(scope, receive, send)


app = Index(debug=config.DEBUG)

# middleware
app.add_middleware(
    GZipMiddleware,
    minimum_size=1024
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_SETTINGS.ALLOW_ORIGINS,
    allow_methods=config.CORS_SETTINGS.ALLOW_METHODS,
    allow_headers=config.CORS_SETTINGS.ALLOW_HEADERS,
    allow_credentials=config.CORS_SETTINGS.ALLOW_CREDENTIALS,
    allow_origin_regex=config.CORS_SETTINGS.ALLOW_ORIGIN_REGEX,
    expose_headers=config.CORS_SETTINGS.EXPOSE_HEADERS,
    max_age=config.CORS_SETTINGS.MAX_AGE,
)

if config.FORCE_SSL:
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=config.ALLOWED_HOSTS
)


monitor: MonitorFile = None


@app.on_event('startup')
async def check_on_startup():
    # check import
    for _path_ in os.listdir(config.path):
        if _path_ in ("statics", "templates"):
            continue
        checkall(_path_)

    # monitor file event
    global monitor
    monitor = MonitorFile(config.path)


@app.on_event('shutdown')
async def clear_check_on_shutdown():
    global monitor
    monitor.stop()


@app.on_event('startup')
async def create_directories():
    """
    create directories for static & template
    """
    os.makedirs(os.path.join(config.path, "statics"), exist_ok=True)
    os.makedirs(os.path.join(config.path, "templates"), exist_ok=True)
