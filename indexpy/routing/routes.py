import typing
import copy
from functools import update_wrapper, wraps
from dataclasses import dataclass, InitVar

from indexpy.types import Literal, ASGIApp, Scope, Receive, Send
from indexpy.utils import superclass
from indexpy.concurrency import complicating
from indexpy.http.view import parse_params, bound_params, only_allow
from indexpy.http.responses import convert

from .convertors import Convertor, compile_path
from .tree import RadixTree

__all__ = [
    "Routes",
    "SubRoutes",
    "HttpRoute",
    "SocketRoute",
    "NoMatchFound",
    "NoRouteFound",
]


def request_response(view: typing.Any) -> ASGIApp:
    @wraps(view)
    async def _(scope: Scope, receive: Receive, send: Send) -> None:
        current_app = scope["app"]
        request = current_app.factory_class.http(scope, receive, send)
        response = convert(await (await bound_params(view, request))(request))
        await response(scope, receive, send)

    return _


def websocket_session(view: typing.Any) -> ASGIApp:
    @wraps(view)
    async def _(scope: Scope, receive: Receive, send: Send) -> None:
        current_app = scope["app"]
        websocket = current_app.factory_class.websocket(scope, receive, send)
        await view(websocket)(scope, receive, send)

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

    def __post_init__(self) -> None:
        if not self.path.startswith("/"):
            raise ValueError("Route path must start with '/'")
        if self.name == "":
            self.name = self.endpoint.__name__


@dataclass
class HttpRoute(BaseRoute):
    method: InitVar[str] = ""

    def __post_init__(self, method: str) -> None:  # type: ignore
        super().__post_init__()

        self.endpoint = complicating(self.endpoint)

        if not (
            hasattr(self.endpoint, "__methods__")
            or hasattr(self.endpoint, "__method__")
        ):
            if method == "":
                raise ValueError("View function must be marked with method")
            self.endpoint = only_allow(method, parse_params(self.endpoint))
        else:
            if hasattr(self.endpoint, "__method__") and (
                method.upper() not in (getattr(self.endpoint, "__method__"), "")
            ):
                raise ValueError("View function has been marked with method")
            if hasattr(self.endpoint, "__methods__") and method != "":
                raise ValueError("View class can't be marked with method")

    def extend_middlewares(self, routes: typing.List[BaseRoute]) -> None:
        if hasattr(routes, "_http_middlewares"):
            endpoint = self.endpoint
            for middleware in getattr(routes, "_http_middlewares"):
                endpoint = middleware(endpoint)
            self.endpoint = update_wrapper(endpoint, self.endpoint)


@dataclass
class SocketRoute(BaseRoute):
    def extend_middlewares(self, routes: typing.List[BaseRoute]) -> None:
        if hasattr(routes, "_socket_middlewares"):
            endpoint = self.endpoint
            for middleware in getattr(routes, "_socket_middlewares"):
                endpoint = middleware(endpoint)
            self.endpoint = update_wrapper(endpoint, self.endpoint)


@dataclass
class ASGIRoute(BaseRoute):
    # This is mypy error
    type: typing.Container[Literal["http", "websocket"]] = ("http", "websocket")  # type: ignore

    def extend_middlewares(self, routes: typing.List[BaseRoute]) -> None:
        if hasattr(routes, "_asgi_middlewares"):
            endpoint = self.endpoint
            for middleware in getattr(routes, "_asgi_middlewares"):
                endpoint = middleware(endpoint)
            self.endpoint = update_wrapper(endpoint, self.endpoint)


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
                self.append(
                    route.__class__(
                        path=routes.prefix + route.path,
                        endpoint=route.endpoint,
                        name=route.name,
                    )
                )
            else:
                self.append(route)

    def http(
        self, path: str, *, name: str = "", method: str = ""
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
    ) -> typing.Callable[[T], T]:
        """
        shortcut for `self.append(ASGIRoute(path, endpoint, name, type))`

        example:
            @routes.asgi("/path", name="endpoint-name")
            class Endpoint(HTTPView): ...
        """

        def register(endpoint: T) -> T:
            self.append(ASGIRoute(path, endpoint, name, type))
            return endpoint

        return register


class Routes(typing.List[BaseRoute], RouteRegisterMixin):
    def __init__(
        self,
        *iterable: typing.Union["BaseRoute", "Routes"],
        http_middlewares: typing.List[typing.Any] = [],
        socket_middlewares: typing.List[typing.Any] = [],
        asgi_middlewares: typing.List[typing.Any] = [],
    ) -> None:
        super().__init__()
        self._http_middlewares = copy.copy(http_middlewares)
        self._socket_middlewares = copy.copy(socket_middlewares)
        self._asgi_middlewares = copy.copy(asgi_middlewares)
        for route in iterable:
            if not isinstance(route, Routes):
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
        or
            def middleware(endpoint):
                async def wrapper(request):
                    response = await endpoint(request)
                    return response
                return wrapper

            routes.http_middleware(middleware)
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
        or
            def middleware(endpoint):
                async def wrapper(websocket):
                    await endpoint(websocket)
                return wrapper

            routes.socket_middleware(middleware)
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
        or
            def middleware(endpoint):
                async def wrapper(scope, receive, send):
                    await endpoint(scope, receive, send)
                return wrapper

            routes.asgi_middleware(middleware)
        """
        self._asgi_middlewares.append(middleware)
        return middleware


class SubRoutes(Routes):
    def __init__(
        self,
        prefix: str,
        routes: typing.List[BaseRoute] = [],
        *,
        http_middlewares: typing.List[typing.Any] = [],
        socket_middlewares: typing.List[typing.Any] = [],
        asgi_middlewares: typing.List[typing.Any] = [],
    ) -> None:
        if not prefix.startswith("/") or prefix.endswith("/"):
            raise ValueError("Mount prefix cannot end with '/' and must start with '/'")
        self.prefix = prefix
        super().__init__(
            *routes,
            http_middlewares=http_middlewares,
            socket_middlewares=socket_middlewares,
            asgi_middlewares=asgi_middlewares,
        )


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

        if name:  # name in ("", None)
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
