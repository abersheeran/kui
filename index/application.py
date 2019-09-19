import os
import copy
import typing
import importlib

from starlette.types import Scope, Receive, Send
from starlette.routing import Lifespan
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.websockets import WebSocket, WebSocketClose
from starlette.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.exceptions import HTTPException, ExceptionMiddleware

from .responses import FileResponse
from .config import config


class Filepath:

    def __init__(self) -> None:
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
        # favicon.ico
        if request.url.path == "/favicon.ico":
            if not os.path.exists(os.path.normpath('favicon.ico')):
                raise HTTPException(404)
            response = FileResponse('favicon.ico')
            await response(scope, receive, send)
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
