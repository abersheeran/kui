import copy
import importlib
import os
import typing
from dataclasses import InitVar, asdict, dataclass
from functools import update_wrapper
from pathlib import Path

from indexpy.types import LOWER_HTTP_METHODS, ASGIApp, Literal, Receive, Scope, Send
from indexpy.concurrency import complicating
from indexpy.http.responses import convert_response
from indexpy.http.view import only_allow
from indexpy.utils import superclass

from .convertors import Convertor, compile_path
from .tree import RadixTree


def request_response(view: typing.Any) -> ASGIApp:
    async def _(scope: Scope, receive: Receive, send: Send) -> None:
        current_app = scope["app"]
        request = current_app.factory_class.http(scope, receive, send)
        response = convert_response(await view(request))
        await response(scope, receive, send)

    setattr(_, "__raw__", view)
    return _


def websocket_session(view: typing.Any) -> ASGIApp:
    async def _(scope: Scope, receive: Receive, send: Send) -> None:
        current_app = scope["app"]
        websocket = current_app.factory_class.websocket(scope, receive, send)
        await view(websocket)

    setattr(_, "__raw__", view)
    return _


def subpath_asgi(path_prefix: str, asgi: ASGIApp) -> ASGIApp:
    assert path_prefix.startswith("/"), "path_prefix must be start with '/'"
    assert not path_prefix.endswith("/"), "path_prefix can't end with '/'"

    async def _(scope: Scope, receive: Receive, send: Send) -> None:
        path = scope["path"]
        root_path = scope.get("root_path", "")

        subscope = copy.copy(scope)
        subscope["path"] = path[len(path_prefix) :]
        subscope["root_path"] = root_path + path_prefix
        await asgi(subscope, receive, send)

    setattr(_, "__raw__", asgi)
    return _


class NoMatchFound(Exception):
    """
    Raised by `.search(path)` if no matching route exists.
    """


class NoRouteFound(Exception):
    """
    Raised by `.url_for(name, **path_params)` if no matching route exists.
    """


@dataclass
class BaseRoute:
    path: str
    endpoint: typing.Any
    name: typing.Optional[str] = ""

    def extend_middlewares(self, routes: typing.List["BaseRoute"]) -> None:
        raise NotImplementedError()

    def _extend_middlewares(
        self, middlewares: typing.Iterable[typing.Callable]
    ) -> None:
        endpoint = self.endpoint
        for middleware in middlewares:
            self.endpoint = middleware(endpoint)
            if not (endpoint is self.endpoint):
                self.endpoint = update_wrapper(self.endpoint, endpoint)
            endpoint = self.endpoint

    def __post_init__(self) -> None:
        if not self.path.startswith("/"):
            raise ValueError("Route path must start with '/'")
        if self.name == "":
            self.name = self.endpoint.__name__


@dataclass
class HttpRoute(BaseRoute):
    method: InitVar[Literal["", LOWER_HTTP_METHODS]] = ""

    def __post_init__(self, method: Literal["", LOWER_HTTP_METHODS]) -> None:  # type: ignore
        super().__post_init__()
        self.endpoint = complicating(self.endpoint)

        if not (
            hasattr(self.endpoint, "__methods__")
            or hasattr(self.endpoint, "__method__")
        ):
            if method == "":
                raise ValueError("View function must be marked with method")
            self.endpoint = only_allow(method, self.endpoint)
        else:
            if hasattr(self.endpoint, "__method__") and (
                method.upper() not in (getattr(self.endpoint, "__method__"), "")
            ):
                raise ValueError("View function has been marked with method")
            if hasattr(self.endpoint, "__methods__") and method != "":
                raise ValueError("View class can't be marked with method")

    def extend_middlewares(self, routes: typing.List[BaseRoute]) -> None:
        self._extend_middlewares(getattr(routes, "_http_middlewares", []))


@dataclass
class SocketRoute(BaseRoute):
    def extend_middlewares(self, routes: typing.List[BaseRoute]) -> None:
        self._extend_middlewares(getattr(routes, "_socket_middlewares", []))


@dataclass
class ASGIRoute(BaseRoute):
    # This is mypy error
    type: typing.Container[Literal["http", "websocket"]] = ("http", "websocket")  # type: ignore
    root_path: InitVar[str] = ""

    def __post_init__(self, root_path: str) -> None:  # type: ignore
        super().__post_init__()
        if root_path:
            self.endpoint = subpath_asgi(root_path, self.endpoint)

    def extend_middlewares(self, routes: typing.List[BaseRoute]) -> None:
        self._extend_middlewares(getattr(routes, "_asgi_middlewares", []))


T = typing.TypeVar("T")


class RouteRegisterMixin:
    __slots__ = ()

    def append(self, route: BaseRoute) -> None:
        raise NotImplementedError()

    def extend(self, routes: typing.List[BaseRoute]) -> None:
        for route in routes:  # type: BaseRoute
            if isinstance(routes, Routes):
                route.extend_middlewares(routes)

            if isinstance(routes, SubRoutes):
                data = asdict(route)
                data["path"] = routes.prefix + data["path"]
                route = route.__class__(**data)

            if getattr(routes, "namespace", None) and route.name:
                route.name = getattr(routes, "namespace") + ":" + route.name

            self.append(route)

    def http(
        self,
        path: str,
        *,
        name: str = "",
        method: Literal["", LOWER_HTTP_METHODS] = "",
    ) -> typing.Callable[[T], T]:
        """
        shortcut for `self.append(HttpRoute(path, endpoint, name, method))`

        example:
            @routes.http("/path", name="endpoint-name")
            class Endpoint(HTTPView): ...
        """

        def register(endpoint: T) -> T:
            self.append(HttpRoute(path, endpoint, name, method))
            return endpoint

        return register

    def websocket(self, path: str, *, name: str = "") -> typing.Callable[[T], T]:
        """
        shortcut for `self.append(SocketRoute(path, endpoint, name))`

        example:
            @routes.websocket("/path", name="endpoint-name")
            async def endpoint(websocket): ...
        """

        def register(endpoint: T) -> T:
            self.append(SocketRoute(path, endpoint, name))
            return endpoint

        return register

    def asgi(
        self,
        path: str,
        *,
        name: str = "",
        type: typing.Container[Literal["http", "websocket"]] = ("http", "websocket"),  # type: ignore
        root_path: str = "",
    ) -> typing.Callable[[T], T]:
        """
        shortcut for `self.append(ASGIRoute(path, endpoint, name, type))`

        example:
            @routes.asgi("/path", name="endpoint-name")
            class Endpoint(HTTPView): ...
        """

        def register(endpoint: T) -> T:
            self.append(ASGIRoute(path, endpoint, name, type, root_path))
            return endpoint

        return register


class Routes(typing.List[BaseRoute], RouteRegisterMixin):
    def __init__(
        self,
        *iterable: typing.Union[BaseRoute, typing.List[BaseRoute]],
        namespace: str = "",
        http_middlewares: typing.List[typing.Any] = [],
        socket_middlewares: typing.List[typing.Any] = [],
        asgi_middlewares: typing.List[typing.Any] = [],
    ) -> None:
        super().__init__()
        self.namespace = namespace
        self._http_middlewares = copy.copy(http_middlewares)
        self._socket_middlewares = copy.copy(socket_middlewares)
        self._asgi_middlewares = copy.copy(asgi_middlewares)
        for route in iterable:
            if not isinstance(route, typing.List):
                self.append(route)
            else:
                self.extend(route)

    def extend(self, routes: typing.List[BaseRoute]) -> None:  # type: ignore
        """
        Extend routes in routes

        example:
            routes.extend(Routes(...))
        or
            routes.extend([...])
        """
        return superclass(RouteRegisterMixin, self).extend(routes)

    def http_middleware(self, middleware: T) -> T:
        """
        append middleware in routes

        example:
            @routes.http_middleware
            def middleware(endpoint):
                async def wrapper(request):
                    response = await endpoint(request)
                    return response
                return wrapper
        """
        self._http_middlewares.append(middleware)
        return middleware

    def socket_middleware(self, middleware: T) -> T:
        """
        append middleware in routes

        example:
            @routes.socket_middleware
            def middleware(endpoint):
                async def wrapper(websocket):
                    await endpoint(websocket)
                return wrapper
        """
        self._socket_middlewares.append(middleware)
        return middleware

    def asgi_middleware(self, middleware: T) -> T:
        """
        append middleware in routes

        example:
            @routes.asgi_middleware
            def middleware(endpoint):
                async def wrapper(scope, receive, send):
                    await endpoint(scope, receive, send)
                return wrapper
        """
        self._asgi_middlewares.append(middleware)
        return middleware


class SubRoutes(Routes):
    def __init__(
        self,
        prefix: str,
        routes: typing.List[BaseRoute] = [],
        *,
        namespace: str = "",
        http_middlewares: typing.List[typing.Any] = [],
        socket_middlewares: typing.List[typing.Any] = [],
        asgi_middlewares: typing.List[typing.Any] = [],
    ) -> None:
        if not prefix.startswith("/") or prefix.endswith("/"):
            raise ValueError("Mount prefix cannot end with '/' and must start with '/'")
        self.prefix = prefix
        super().__init__(
            *routes,
            namespace=namespace,
            http_middlewares=http_middlewares,
            socket_middlewares=socket_middlewares,
            asgi_middlewares=asgi_middlewares,
        )


class FileRoutes(typing.List[BaseRoute]):
    def __init__(
        self,
        module_name: str,
        *,
        namespace: str = "",
        allow_underline: bool = False,
        suffix: str = "",
    ) -> None:
        dirpath = Path(
            os.path.abspath(importlib.import_module(module_name).__file__)
        ).parent
        assert dirpath.name == module_name

        for pypath in dirpath.glob("**/*.py"):
            relpath = str(pypath.relative_to(dirpath)).replace("\\", "/")[:-3]

            path_list = relpath.split("/")
            path_list.insert(0, module_name)

            url_path = "/" + relpath
            if not allow_underline:
                url_path = url_path.replace("_", "-")
            if url_path.endswith("/index"):
                url_path = url_path[: -len("index")]
            else:
                url_path = url_path + suffix

            module = importlib.import_module(".".join(path_list))
            url_name = getattr(module, "name", None)
            get_response = getattr(module, "HTTP", None)
            serve_socket = getattr(module, "Socket", None)
            if get_response:
                _get_response = get_response
                for deep in range(len(path_list), 0, -1):
                    _module = importlib.import_module(".".join(path_list[:deep]))
                    if not hasattr(_module, "HTTPMiddleware"):
                        continue
                    get_response = getattr(_module, "HTTPMiddleware")(get_response)
                update_wrapper(get_response, _get_response)
                self.append(HttpRoute(url_path, get_response, url_name))
            if serve_socket:
                _serve_socket = serve_socket
                for deep in range(len(path_list), 0, -1):
                    _module = importlib.import_module(".".join(path_list[:deep]))
                    if not hasattr(_module, "SocketMiddleware"):
                        continue
                    serve_socket = getattr(_module, "SocketMiddleware")(serve_socket)
                update_wrapper(serve_socket, _serve_socket)
                self.append(SocketRoute(url_path, serve_socket, url_name))

        self.namespace = namespace


class Router(RouteRegisterMixin):
    def __init__(self, routes: typing.List[BaseRoute] = list()) -> None:
        self.http_tree = RadixTree()
        self.websocket_tree = RadixTree()

        self.http_routes: typing.Dict[
            str, typing.Tuple[str, typing.Dict[str, Convertor], ASGIApp]
        ] = {}
        self.websocket_routes: typing.Dict[
            str, typing.Tuple[str, typing.Dict[str, Convertor], ASGIApp]
        ] = {}

        self.extend(routes)

    def _append(
        self,
        path: str,
        endpoint: ASGIApp,
        name: typing.Optional[str],
        radix_tree: RadixTree,
        routes: typing.Dict,
    ) -> None:
        if name in routes:
            raise ValueError(f"Duplicate route name: {name}")

        radix_tree.append(path, endpoint)
        path_format, path_convertors = compile_path(path)

        if name:  # name not in ("", None)
            routes[name] = (path_format, path_convertors, endpoint)

    def append(self, route: BaseRoute) -> None:
        if isinstance(route, HttpRoute):
            self._append(
                route.path,
                request_response(route.endpoint),
                route.name,
                self.http_tree,
                self.http_routes,
            )
        elif isinstance(route, SocketRoute):
            self._append(
                route.path,
                websocket_session(route.endpoint),
                route.name,
                self.websocket_tree,
                self.websocket_routes,
            )
        elif isinstance(route, ASGIRoute):
            if "http" in route.type:
                self._append(
                    route.path,
                    route.endpoint,
                    route.name,
                    self.http_tree,
                    self.http_routes,
                )
            if "websocket" in route.type:
                self._append(
                    route.path,
                    route.endpoint,
                    route.name,
                    self.websocket_tree,
                    self.websocket_routes,
                )
        else:
            raise TypeError(
                "Need type: `ASGIRoute`, `HttpRoute` or `SocketRoute`,"
                + f" but got type: {type(route)}"
            )

    def search(
        self, protocol: Literal["http", "websocket"], path: str
    ) -> typing.Tuple[typing.Dict[str, typing.Any], ASGIApp]:
        if protocol == "http":
            radix_tree = self.http_tree
        elif protocol == "websocket":
            radix_tree = self.websocket_tree
        else:
            raise ValueError("`protocol` must be in ('http', 'websocket')")

        params, endpoint = radix_tree.search(path)

        if params is None or endpoint is None:
            raise NoMatchFound(path)

        return params, endpoint

    def extend(self, routes: typing.List[BaseRoute]) -> None:
        """
        Add routes in router

        example:
            router.extend(Routes(...))
        or
            router.extend([...])
        """
        return superclass(RouteRegisterMixin, self).extend(routes)

    def url_for(
        self,
        name: str,
        path_params: typing.Dict[str, typing.Any] = {},
        protocol: Literal["http", "websocket"] = "http",
    ) -> str:
        if protocol == "http":
            routes = self.http_routes
        elif protocol == "websocket":
            routes = self.websocket_routes
        else:
            raise ValueError("`protocol` must be in ('http', 'websocket')")

        if name not in routes:
            raise NoRouteFound(f"No route with name '{name}' exists")

        path_format, path_convertors, _ = routes[name]

        return path_format.format_map(
            {
                name: path_convertors[name].to_string(value)
                for name, value in path_params.items()
            }
        )
