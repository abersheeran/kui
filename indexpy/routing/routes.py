from __future__ import annotations

import abc
import importlib
import operator
import os
import sys
import typing
from copy import deepcopy
from dataclasses import dataclass
from functools import reduce, update_wrapper
from pathlib import Path

if sys.version_info[:2] < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from baize.routing import compile_path

from indexpy.parameters import auto_params
from indexpy.utils import F
from indexpy.views import required_method

from .tree import RadixTree, RouteType

T = typing.TypeVar("T")


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

    def extend_middlewares(self, routes: typing.Iterable[BaseRoute]) -> None:
        raise NotImplementedError()

    def _extend_middlewares(
        self, middlewares: typing.Iterable[typing.Callable]
    ) -> None:
        reduce(operator.matmul, middlewares, self)

    def __matmul__(self, decorator: typing.Callable[[T], T]):
        endpoint = self.endpoint
        self.endpoint = decorator(self.endpoint)
        if not (getattr(self.endpoint, "__wrapped__", self.endpoint) is endpoint):
            self.endpoint = update_wrapper(self.endpoint, endpoint)
        return self

    def __post_init__(self) -> None:
        assert self.path.startswith("/"), "Route path must start with '/'"
        if self.name == "":
            self.name = self.endpoint.__name__
        self.endpoint = auto_params(self.endpoint)


@dataclass
class HttpRoute(BaseRoute):
    def extend_middlewares(self, routes: typing.Iterable[BaseRoute]) -> None:
        self._extend_middlewares(getattr(routes, "_http_middlewares", []))


@dataclass
class SocketRoute(BaseRoute):
    def extend_middlewares(self, routes: typing.Iterable[BaseRoute]) -> None:
        self._extend_middlewares(getattr(routes, "_socket_middlewares", []))


_RRMixinSelf = typing.TypeVar("_RRMixinSelf", bound="RouteRegisterMixin")
View = typing.TypeVar("View", bound=typing.Callable)


class HttpRegister:
    def __init__(self, routes: RouteRegisterMixin) -> None:
        self.__routes = routes

    def __call__(self, path: str, *, name: str = "") -> typing.Callable[[View], View]:
        """
        shortcut for `self << HttpRoute(path, endpoint, name)`

        example:
        ```python
            @routes.http("/path", name="endpoint-name")
            class Endpoint(HttpView): ...
        ```
        """

        def register(endpoint: View) -> View:
            self.__routes << HttpRoute(path, endpoint, name)
            return endpoint

        return register

    def get(self, path: str, *, name: str = "") -> typing.Callable[[View], View]:
        """
        shortcut for `self << HttpRoute(path, required_method("GET")(endpoint), name)`

        example:
        ```python
            @routes.http.get("/path", name="endpoint-name")
            class Endpoint(HttpView): ...
        ```
        """

        def register(endpoint: View) -> View:
            self.__routes << HttpRoute(path, required_method("GET")(endpoint), name)
            return endpoint

        return register

    def post(self, path: str, *, name: str = "") -> typing.Callable[[View], View]:
        """
        shortcut for `self << HttpRoute(path, required_method("POST")(endpoint), name)`

        example:
        ```python
            @routes.http.post("/path", name="endpoint-name")
            class Endpoint(HttpView): ...
        ```
        """

        def register(endpoint: View) -> View:
            self.__routes << HttpRoute(path, required_method("POST")(endpoint), name)
            return endpoint

        return register

    def put(self, path: str, *, name: str = "") -> typing.Callable[[View], View]:
        """
        shortcut for `self << HttpRoute(path, required_method("PUT")(endpoint), name)`

        example:
        ```python
            @routes.http.put("/path", name="endpoint-name")
            class Endpoint(HttpView): ...
        ```
        """

        def register(endpoint: View) -> View:
            self.__routes << HttpRoute(path, required_method("PUT")(endpoint), name)
            return endpoint

        return register

    def patch(self, path: str, *, name: str = "") -> typing.Callable[[View], View]:
        """
        shortcut for `self << HttpRoute(path, required_method("PATCH")(endpoint), name)`

        example:
        ```python
            @routes.http.patch("/path", name="endpoint-name")
            class Endpoint(HttpView): ...
        ```
        """

        def register(endpoint: View) -> View:
            self.__routes << HttpRoute(path, required_method("PATCH")(endpoint), name)
            return endpoint

        return register

    def delete(self, path: str, *, name: str = "") -> typing.Callable[[View], View]:
        """
        shortcut for `self << HttpRoute(path, required_method("DELETE")(endpoint), name)`

        example:
        ```python
            @routes.http.delete("/path", name="endpoint-name")
            class Endpoint(HttpView): ...
        ```
        """

        def register(endpoint: View) -> View:
            self.__routes << HttpRoute(path, required_method("DELETE")(endpoint), name)
            return endpoint

        return register


class RouteRegisterMixin(abc.ABC):
    @abc.abstractmethod
    def append(self: _RRMixinSelf, route: BaseRoute) -> _RRMixinSelf:
        raise NotImplementedError

    def __lshift__(
        self: _RRMixinSelf, other: typing.Union[BaseRoute, typing.Iterable[BaseRoute]]
    ) -> _RRMixinSelf:
        """
        self << routes
        """
        if isinstance(other, BaseRoute):
            return self.append(other)
        elif isinstance(other, typing.Iterable):
            for route in other:
                if isinstance(route, BaseRoute):
                    if getattr(other, "namespace", None) is not None and route.name:
                        route.name = getattr(other, "namespace") + ":" + route.name
                    route.extend_middlewares(other)
                self << route
            return self
        else:
            return NotImplemented

    @property
    def http(self) -> HttpRegister:
        """
        shortcut for `self << HttpRoute(path, endpoint, name)`

        example:
        ```python
            @routes.http("/path", name="endpoint-name")
            class Endpoint(HttpView): ...
        ```
        """
        return HttpRegister(self)

    def websocket(self, path: str, *, name: str = "") -> typing.Callable[[View], View]:
        """
        shortcut for `self << SocketRoute(path, endpoint, name)`

        example:
        ```python
            @routes.websocket("/path", name="endpoint-name")
            class Endpoint(SocketView): ...
        ```
        """

        def register(endpoint: View) -> View:
            self << SocketRoute(path, endpoint, name)
            return endpoint

        return register


_RoutesSelf = typing.TypeVar("_RoutesSelf", bound="Routes")


class Routes(typing.Iterable[BaseRoute], RouteRegisterMixin):
    def __init__(
        self,
        *iterable: typing.Union[BaseRoute, typing.Iterable[BaseRoute]],
        namespace: str = "",
        http_middlewares: typing.Sequence[typing.Any] = [],
        socket_middlewares: typing.Sequence[typing.Any] = [],
    ) -> None:
        self.namespace = namespace
        self._list: typing.List[BaseRoute] = []
        self._http_middlewares = list(http_middlewares)
        self._socket_middlewares = list(socket_middlewares)
        for route in iterable:
            self << route

    def __iter__(self) -> typing.Iterator[BaseRoute]:
        return iter(self._list)

    def append(self: _RoutesSelf, route: BaseRoute) -> _RoutesSelf:
        self._list.append(route)
        return self

    def __rfloordiv__(self: _RoutesSelf, other: str) -> _RoutesSelf:
        """
        other // self
        """
        if not isinstance(other, str):
            return NotImplemented

        return Prefix(other) // self

    def __add__(self, routes: typing.Iterable[BaseRoute]) -> Routes:
        """
        self + routes
        """
        return Routes(*self, *routes)

    def __radd__(self, routes: typing.Iterable[BaseRoute]) -> Routes:
        """
        routes + self
        """
        return Routes(*routes, *self)

    def http_middleware(self, middleware: T) -> T:
        """
        append middleware in routes

        example:
        ```
            @routes.http_middleware
            def middleware(endpoint):
                async def wrapper():
                    return await endpoint()
                return wrapper
        ```
        """
        self._http_middlewares.append(middleware)
        return middleware

    def socket_middleware(self, middleware: T) -> T:
        """
        append middleware in routes

        example:
        ```
            @routes.socket_middleware
            def middleware(endpoint):
                async def wrapper():
                    await endpoint()
                return wrapper
        ```
        """
        self._socket_middlewares.append(middleware)
        return middleware


_RouteSequence = typing.TypeVar("_RouteSequence", bound=typing.Iterable[BaseRoute])


class Prefix(str):
    def __init__(self, *args, **kwargs) -> None:
        assert self.startswith("/") and not self.endswith("/")

    def __floordiv__(self, other: _RouteSequence) -> _RouteSequence:
        """
        self // other
        """
        if not isinstance(other, typing.Iterable):
            return NotImplemented
        result = deepcopy(other)
        for route in result:
            route.path = self + route.path
        return typing.cast(_RouteSequence, result)


_RouterSelf = typing.TypeVar("_RouterSelf", bound="Router")


class Router(RouteRegisterMixin):
    def __init__(self, routes: typing.Iterable[BaseRoute]) -> None:
        self.http_tree = RadixTree()
        self.websocket_tree = RadixTree()

        self.http_routes: typing.Dict[str, RouteType] = {}
        self.websocket_routes: typing.Dict[str, RouteType] = {}

        self << routes

    def append(self: _RouterSelf, route: BaseRoute) -> _RouterSelf:
        if isinstance(route, HttpRoute):
            radix_tree = self.http_tree
            routes = self.http_routes
        elif isinstance(route, SocketRoute):
            radix_tree = self.websocket_tree
            routes = self.websocket_routes
        else:
            raise TypeError(
                f"Need type: `HttpRoute` or `SocketRoute`, but got type: {type(route)}"
            )

        if route.name in routes:
            raise ValueError(f"Duplicate route name: {route.name}")

        radix_tree.append(route.path, route.endpoint)
        path_format, path_convertors = compile_path(route.path)

        if route.name:  # name not in ("", None)
            routes[route.name] = (path_format, path_convertors, route.endpoint)

        return self

    def search(
        self, protocol: Literal["http", "websocket"], path: str
    ) -> typing.Tuple[typing.Dict[str, typing.Any], typing.Callable[[], typing.Any]]:
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

    def url_for(
        self,
        name: str,
        path_params: typing.Dict[str, typing.Any] = {},
        *,
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


class FileRoutes(typing.Iterable[BaseRoute], RouteRegisterMixin):
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

        self.namespace = namespace

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
                get_response = (
                    range(len(path_list), 0, -1)
                    | F(map, lambda deep: ".".join(path_list[:deep]))
                    | F(map, lambda module_name: importlib.import_module(module_name))
                    | F(map, lambda module: getattr(module, "HTTPMiddleware", None))
                    | F(
                        reduce,
                        lambda handler, middleware: update_wrapper(
                            middleware(handler), handler
                        ),
                        ...,
                        get_response,
                    )
                )
                self << HttpRoute(url_path, get_response, url_name)

            if serve_socket:
                serve_socket = (
                    range(len(path_list), 0, -1)
                    | F(map, lambda deep: ".".join(path_list[:deep]))
                    | F(map, lambda module_name: importlib.import_module(module_name))
                    | F(map, lambda module: getattr(module, "SocketMiddleware", None))
                    | F(
                        reduce,
                        lambda handler, middleware: update_wrapper(
                            middleware(handler), handler
                        ),
                        ...,
                        serve_socket,
                    )
                )
                self << SocketRoute(url_path, serve_socket, url_name)
