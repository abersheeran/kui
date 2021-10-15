from __future__ import annotations

import abc
import operator
import sys
import typing
from copy import deepcopy
from functools import reduce

if sys.version_info[:2] < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from baize.routing import compile_path

from ..utils import FF, F
from ..views import required_method
from .routes import BaseRoute, HttpRoute, SocketRoute
from .tree import RadixTree, RouteType


class NoMatchFound(Exception):
    """
    Raised by `.search(path)` if no matching route exists.
    """


class NoRouteFound(Exception):
    """
    Raised by `.url_for(name, **path_params)` if no matching route exists.
    """


T = typing.TypeVar("T")

_RRMixinSelf = typing.TypeVar("_RRMixinSelf", bound="RouteRegisterMixin")
View = typing.TypeVar("View", bound=typing.Callable)


class HttpRegister:
    def __init__(self, routes: RouteRegisterMixin) -> None:
        self.__routes = routes

    def _register_with_method(
        self,
        method: str,
        path: str,
        *,
        name: typing.Optional[str] = "",
        middlewares: typing.Iterable[typing.Callable[[View], View]] = [],
        summary: str = None,
        description: str = None,
        tags: typing.Iterable[str] = None,
    ) -> typing.Callable[[View], View]:
        """
        if method == "any", all request method would be allowed.
        """

        def register(endpoint: View) -> View:
            route: HttpRoute = reduce(
                operator.matmul,
                middlewares,
                HttpRoute(path, endpoint, name, summary, description, tags),
            )
            if method != "any":
                route = route @ required_method(method.upper())

            self.__routes << route
            return endpoint

        return register

    def __call__(
        self,
        path: str,
        *,
        name: typing.Optional[str] = "",
        middlewares: typing.Iterable[typing.Callable[[View], View]] = [],
        summary: str = None,
        description: str = None,
        tags: typing.Iterable[str] = None,
    ) -> typing.Callable[[View], View]:
        """
        shortcut for `self << HttpRoute(path, endpoint, name)`

        example:
        ```python
            @routes.http("/path", name="endpoint-name")
            class Endpoint(HttpView): ...
        ```
        """
        return self._register_with_method(
            "any",
            path,
            name=name,
            middlewares=middlewares,
            summary=summary,
            description=description,
            tags=tags,
        )

    def get(
        self,
        path: str,
        *,
        name: typing.Optional[str] = "",
        middlewares: typing.Iterable[typing.Callable[[View], View]] = [],
        summary: str = None,
        description: str = None,
        tags: typing.Iterable[str] = None,
    ) -> typing.Callable[[View], View]:
        """
        shortcut for `self << HttpRoute(path, endpoint, name) @ required_method("GET")`

        example:
        ```python
            @routes.http.get("/path", name="endpoint-name")
            class Endpoint(HttpView): ...
        ```
        """
        return self._register_with_method(
            "get",
            path,
            name=name,
            middlewares=middlewares,
            summary=summary,
            description=description,
            tags=tags,
        )

    def post(
        self,
        path: str,
        *,
        name: typing.Optional[str] = "",
        middlewares: typing.Iterable[typing.Callable[[View], View]] = [],
        summary: str = None,
        description: str = None,
        tags: typing.Iterable[str] = None,
    ) -> typing.Callable[[View], View]:
        """
        shortcut for `self << HttpRoute(path, endpoint, name) @ required_method("POST")`

        example:
        ```python
            @routes.http.post("/path", name="endpoint-name")
            class Endpoint(HttpView): ...
        ```
        """
        return self._register_with_method(
            "post",
            path,
            name=name,
            middlewares=middlewares,
            summary=summary,
            description=description,
            tags=tags,
        )

    def put(
        self,
        path: str,
        *,
        name: typing.Optional[str] = "",
        middlewares: typing.Iterable[typing.Callable[[View], View]] = [],
        summary: str = None,
        description: str = None,
        tags: typing.Iterable[str] = None,
    ) -> typing.Callable[[View], View]:
        """
        shortcut for `self << HttpRoute(path, endpoint, name) @ required_method("PUT")`

        example:
        ```python
            @routes.http.put("/path", name="endpoint-name")
            class Endpoint(HttpView): ...
        ```
        """
        return self._register_with_method(
            "put",
            path,
            name=name,
            middlewares=middlewares,
            summary=summary,
            description=description,
            tags=tags,
        )

    def patch(
        self,
        path: str,
        *,
        name: typing.Optional[str] = "",
        middlewares: typing.Iterable[typing.Callable[[View], View]] = [],
        summary: str = None,
        description: str = None,
        tags: typing.Iterable[str] = None,
    ) -> typing.Callable[[View], View]:
        """
        shortcut for `self << HttpRoute(path, endpoint, name) @ required_method("PATCH")`

        example:
        ```python
            @routes.http.patch("/path", name="endpoint-name")
            class Endpoint(HttpView): ...
        ```
        """
        return self._register_with_method(
            "patch",
            path,
            name=name,
            middlewares=middlewares,
            summary=summary,
            description=description,
            tags=tags,
        )

    def delete(
        self,
        path: str,
        *,
        name: typing.Optional[str] = "",
        middlewares: typing.Iterable[typing.Callable[[View], View]] = [],
        summary: str = None,
        description: str = None,
        tags: typing.Iterable[str] = None,
    ) -> typing.Callable[[View], View]:
        """
        shortcut for `self << HttpRoute(path, endpoint, name) @ required_method("DELETE")`

        example:
        ```python
            @routes.http.delete("/path", name="endpoint-name")
            class Endpoint(HttpView): ...
        ```
        """
        return self._register_with_method(
            "delete",
            path,
            name=name,
            middlewares=middlewares,
            summary=summary,
            description=description,
            tags=tags,
        )


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
                    if getattr(other, "namespace", "") and route.name:
                        route.name = getattr(other, "namespace") + ":" + route.name
                    route.extend_middlewares(other)
                self << route
            return self
        else:
            return NotImplemented

    @property
    def http(self) -> HttpRegister:
        return HttpRegister(self)

    def websocket(
        self,
        path: str,
        *,
        name: typing.Optional[str] = "",
        middlewares: typing.Iterable[typing.Callable[[View], View]] = [],
    ) -> typing.Callable[[View], View]:
        """
        shortcut for `self << SocketRoute(path, endpoint, name)`

        example:
        ```python
            @routes.websocket("/path", name="endpoint-name")
            class Endpoint(SocketView): ...
        ```
        """

        def register(endpoint: View) -> View:
            self << reduce(
                operator.matmul, middlewares, SocketRoute(path, endpoint, name)
            )
            return endpoint

        return register


_RoutesSelf = typing.TypeVar("_RoutesSelf", bound="Routes")


class Routes(typing.Sequence[BaseRoute], RouteRegisterMixin):
    def __init__(
        self,
        *iterable: typing.Union[BaseRoute, typing.Iterable[BaseRoute]],
        namespace: str = "",
        tags: typing.Iterable[str] = None,
        http_middlewares: typing.Sequence[typing.Any] = [],
        socket_middlewares: typing.Sequence[typing.Any] = [],
    ) -> None:
        self.namespace = namespace
        self._list: typing.List[BaseRoute] = []
        self._http_middlewares = list(http_middlewares)
        self._http_middlewares.append(
            lambda endpoint: (
                setattr(  # type: ignore
                    endpoint,
                    "__tags__",
                    list(getattr(endpoint, "__tags__", [])) + list(tags or []),
                )
                or endpoint
            )
        )
        self._socket_middlewares = list(socket_middlewares)
        for route in iterable:
            self << route

    @typing.overload
    def __getitem__(self, index: int) -> BaseRoute:
        ...

    @typing.overload
    def __getitem__(self, index: slice) -> typing.NoReturn:
        ...

    def __getitem__(self, index):
        if isinstance(index, int):
            return self._list[index]
        else:
            raise TypeError("Slicing syntax is not allowed")

    def __len__(self) -> int:
        return len(self._list)

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
        return Routes() << self << routes

    def __radd__(self, routes: typing.Iterable[BaseRoute]) -> Routes:
        """
        routes + self
        """
        return Routes() << routes << self

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, typing.Sequence):
            return NotImplemented
        return len(o) == len(self) and all(
            zip(self, o) | F(map, FF(lambda r, r_: r == r_))
        )

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

        if route.path == "":
            route.path = "/"

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
