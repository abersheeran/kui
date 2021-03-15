from __future__ import annotations

import abc
import copy
import importlib
import os
import sys
import typing
from dataclasses import asdict, dataclass
from functools import reduce, update_wrapper
from pathlib import Path

if sys.version_info[:2] < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from baize.routing import compile_path

from .tree import RadixTree, RouteType


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
    def extend_middlewares(self, routes: typing.List[BaseRoute]) -> None:
        self._extend_middlewares(getattr(routes, "_http_middlewares", []))


@dataclass
class SocketRoute(BaseRoute):
    def extend_middlewares(self, routes: typing.List[BaseRoute]) -> None:
        self._extend_middlewares(getattr(routes, "_socket_middlewares", []))


T = typing.TypeVar("T")


class RouteRegisterMixin(abc.ABC):
    @abc.abstractmethod
    def append(self, route: BaseRoute) -> None:
        raise NotImplementedError

    def __lshift__(self, routes: typing.List[BaseRoute]) -> None:
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

    def http(self, path: str, *, name: str = "") -> typing.Callable[[T], T]:
        """
        shortcut for `self.append(HttpRoute(path, endpoint, name, method))`

        example:
            @routes.http("/path", name="endpoint-name")
            class Endpoint(HttpView): ...
        """

        def register(endpoint: T) -> T:
            self.append(HttpRoute(path, endpoint, name))
            return endpoint

        return register

    def websocket(self, path: str, *, name: str = "") -> typing.Callable[[T], T]:
        """
        shortcut for `self.append(SocketRoute(path, endpoint, name))`

        example:
            @routes.websocket("/path", name="endpoint-name")
            class Endpoint(SocketView): ...
        """

        def register(endpoint: T) -> T:
            self.append(SocketRoute(path, endpoint, name))
            return endpoint

        return register


class Routes(typing.List[BaseRoute], RouteRegisterMixin):
    def __init__(
        self,
        *iterable: typing.Union[BaseRoute, typing.List[BaseRoute]],
        namespace: str = "",
        http_middlewares: typing.List[typing.Any] = [],
        socket_middlewares: typing.List[typing.Any] = [],
    ) -> None:
        super().__init__()
        self.namespace = namespace
        self._http_middlewares = copy.copy(http_middlewares)
        self._socket_middlewares = copy.copy(socket_middlewares)
        for route in iterable:
            if not isinstance(route, list):
                self.append(route)
            else:
                self << route

    def http_middleware(self, middleware: T) -> T:
        """
        append middleware in routes

        example:
        ```
            @routes.http_middleware
            def middleware(endpoint):
                async def wrapper():
                    response = await endpoint(request)
                    return response
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
                    await endpoint(websocket)
                return wrapper
        ```
        """
        self._socket_middlewares.append(middleware)
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
    ) -> None:
        if not prefix.startswith("/") or prefix.endswith("/"):
            raise ValueError("Mount prefix cannot end with '/' and must start with '/'")
        self.prefix = prefix
        super().__init__(
            *routes,
            namespace=namespace,
            http_middlewares=http_middlewares,
            socket_middlewares=socket_middlewares,
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
                get_response = reduce(
                    lambda handler, middleware: update_wrapper(
                        middleware(handler), handler
                    ),
                    (
                        middleware
                        for middleware in (
                            getattr(module, "HTTPMiddleware", None)
                            for module in (
                                importlib.import_module(".".join(path_list[:deep]))
                                for deep in range(len(path_list), 0, -1)
                            )
                        )
                        if middleware is not None
                    ),
                    get_response,
                )
                self.append(HttpRoute(url_path, get_response, url_name))

            if serve_socket:
                serve_socket = reduce(
                    lambda handler, middleware: update_wrapper(
                        middleware(handler), handler
                    ),
                    (
                        middleware
                        for middleware in (
                            getattr(module, "HTTPMiddleware", None)
                            for module in (
                                importlib.import_module(".".join(path_list[:deep]))
                                for deep in range(len(path_list), 0, -1)
                            )
                        )
                        if middleware is not None
                    ),
                    serve_socket,
                )
                self.append(SocketRoute(url_path, serve_socket, url_name))


class Router(RouteRegisterMixin):
    def __init__(self, routes: typing.List[BaseRoute] = []) -> None:
        self.http_tree = RadixTree()
        self.websocket_tree = RadixTree()

        self.http_routes: typing.Dict[str, RouteType] = {}
        self.websocket_routes: typing.Dict[str, RouteType] = {}

        self << routes

    def _append(
        self,
        path: str,
        endpoint: typing.Callable[[], typing.Any],
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
                route.endpoint,
                route.name,
                self.http_tree,
                self.http_routes,
            )
        elif isinstance(route, SocketRoute):
            self._append(
                route.path,
                route.endpoint,
                route.name,
                self.websocket_tree,
                self.websocket_routes,
            )
        else:
            raise TypeError(
                f"Need type: `HttpRoute` or `SocketRoute`, but got type: {type(route)}"
            )

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
