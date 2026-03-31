from __future__ import annotations

import abc
import inspect
import operator
import typing
from copy import deepcopy
from functools import reduce

from baize.routing import compile_path
from typing_extensions import Literal, Self

from ..utils import FF, F
from .routes import BaseRoute, HttpRoute, SocketRoute
from .tree import RadixTree, RouteType
from .typing import MiddlewareType, ViewType


class NoMatchFound(Exception):
    """
    Raised by `.search(path)` if no matching route exists.
    """


class NoRouteFound(Exception):
    """
    Raised by `.url_for(name, **path_params)` if no matching route exists.
    """


class HttpRegister(typing.Generic[ViewType]):
    """
    shortcut for `self << HttpRoute(path, endpoint, name)`

    example:
    ```python
        @routes.http("/path", name="endpoint-name")
        class Endpoint(HttpViewType): ...
    ```
    """

    def __init__(self, routes: RouteRegisterMixin[ViewType]) -> None:
        self.__routes = routes

    def _register_with_method(
        self,
        method: str,
        path: str,
        *,
        name: typing.Optional[str] = "",
        middlewares: typing.Iterable[MiddlewareType] = [],
        summary: str | None = None,
        description: str | None = None,
        tags: typing.Iterable[str] | None = None,
    ) -> typing.Callable[[ViewType], ViewType]:
        """
        if method == "any", all request method would be allowed.
        """

        def register(endpoint: ViewType) -> ViewType:
            route: HttpRoute[ViewType] = self.__routes._http_route_class(
                path, endpoint, name, summary, description, tags
            )
            if method != "any":
                route = route @ self.__routes._required_method_factory(method.upper())

            reduce(operator.matmul, middlewares, route)

            self.__routes <<= route
            return endpoint

        return register

    def __call__(
        self,
        path: str,
        *,
        name: typing.Optional[str] = "",
        middlewares: typing.Iterable[MiddlewareType] = [],
        summary: str | None = None,
        description: str | None = None,
        tags: typing.Iterable[str] | None = None,
    ) -> typing.Callable[[ViewType], ViewType]:
        """
        shortcut for `self << HttpRoute(path, endpoint, name)`

        example:
        ```python
            @routes.http("/path", name="endpoint-name")
            class Endpoint(HttpViewType): ...
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
        middlewares: typing.Iterable[MiddlewareType] = [],
        summary: str | None = None,
        description: str | None = None,
        tags: typing.Iterable[str] | None = None,
    ) -> typing.Callable[[ViewType], ViewType]:
        """
        shortcut for `self << HttpRoute(path, endpoint, name) @ required_method("GET")`

        example:
        ```python
            @routes.http.get("/path", name="endpoint-name")
            class Endpoint(HttpViewType): ...
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
        middlewares: typing.Iterable[MiddlewareType] = [],
        summary: str | None = None,
        description: str | None = None,
        tags: typing.Iterable[str] | None = None,
    ) -> typing.Callable[[ViewType], ViewType]:
        """
        shortcut for `self << HttpRoute(path, endpoint, name) @ required_method("POST")`

        example:
        ```python
            @routes.http.post("/path", name="endpoint-name")
            class Endpoint(HttpViewType): ...
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
        middlewares: typing.Iterable[MiddlewareType] = [],
        summary: str | None = None,
        description: str | None = None,
        tags: typing.Iterable[str] | None = None,
    ) -> typing.Callable[[ViewType], ViewType]:
        """
        shortcut for `self << HttpRoute(path, endpoint, name) @ required_method("PUT")`

        example:
        ```python
            @routes.http.put("/path", name="endpoint-name")
            class Endpoint(HttpViewType): ...
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
        middlewares: typing.Iterable[MiddlewareType] = [],
        summary: str | None = None,
        description: str | None = None,
        tags: typing.Iterable[str] | None = None,
    ) -> typing.Callable[[ViewType], ViewType]:
        """
        shortcut for `self << HttpRoute(path, endpoint, name) @ required_method("PATCH")`

        example:
        ```python
            @routes.http.patch("/path", name="endpoint-name")
            class Endpoint(HttpViewType): ...
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
        middlewares: typing.Iterable[MiddlewareType] = [],
        summary: str | None = None,
        description: str | None = None,
        tags: typing.Iterable[str] | None = None,
    ) -> typing.Callable[[ViewType], ViewType]:
        """
        shortcut for `self << HttpRoute(path, endpoint, name) @ required_method("DELETE")`

        example:
        ```python
            @routes.http.delete("/path", name="endpoint-name")
            class Endpoint(HttpViewType): ...
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


class RouteRegisterMixin(abc.ABC, typing.Generic[ViewType]):
    _required_method_factory: typing.ClassVar
    _http_route_class: typing.ClassVar

    @abc.abstractmethod
    def append(self: Self, route: BaseRoute) -> Self:
        raise NotImplementedError

    def __lshift__(
        self: Self,
        other: typing.Union[BaseRoute, typing.Iterable[BaseRoute]],
    ) -> Self:
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
                _ = self << route
            return self
        else:
            return NotImplemented

    @property
    def http(self) -> HttpRegister[ViewType]:
        return HttpRegister(self)

    def websocket(
        self,
        path: str,
        *,
        name: typing.Optional[str] = "",
        middlewares: typing.Iterable[MiddlewareType] = [],
    ) -> typing.Callable[[ViewType], ViewType]:
        """
        shortcut for `self << SocketRoute(path, endpoint, name)`

        example:
        ```python
            @routes.websocket("/path", name="endpoint-name")
            class Endpoint(SocketViewType): ...
        ```
        """

        def register(endpoint: ViewType) -> ViewType:
            from ..asgi import SocketRoute

            _ = self << reduce(  # type: ignore
                operator.matmul, middlewares, SocketRoute(path, endpoint, name)
            )
            return endpoint

        return register


def _set_tags(tags: typing.Iterable[str] | None = None):
    def _set_tags_middleware(endpoint: ViewType) -> ViewType:
        handler = endpoint
        w: typing.Any
        if inspect.ismethod(handler):
            w = handler.__func__
        else:
            w = endpoint
        all_tags = list(getattr(w, "__docs_tags__", [])) + list(tags or [])
        setattr(w, "__docs_tags__", all_tags)
        return endpoint

    return _set_tags_middleware


class Routes(
    typing.Sequence[BaseRoute[ViewType]],
    RouteRegisterMixin[ViewType],
):
    def __init__(
        self,
        *iterable: typing.Union[BaseRoute, typing.Iterable[BaseRoute]],
        namespace: str = "",
        tags: typing.Iterable[str] | None = None,
        http_middlewares: typing.Sequence[MiddlewareType] = [],
        socket_middlewares: typing.Sequence[typing.Any] = [],
    ) -> None:
        self.namespace = namespace
        self._list: typing.List[BaseRoute[ViewType]] = []
        self._http_middlewares = list(http_middlewares)
        self._http_middlewares.append(_set_tags(tags))
        self._socket_middlewares = list(socket_middlewares)
        for route in iterable:
            _ = self << route

    @typing.overload
    def __getitem__(self, index: int) -> BaseRoute[ViewType]: ...

    @typing.overload
    def __getitem__(self, index: slice) -> typing.List[BaseRoute[ViewType]]: ...

    def __getitem__(self, index):
        return self._list[index]

    def __len__(self) -> int:
        return len(self._list)

    def append(self: Self, route: BaseRoute) -> Self:
        self._list.append(route)
        return self

    def __rfloordiv__(self: Self, other: str) -> Self:
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
        return Routes[ViewType]() << self << routes

    def __radd__(self, routes: typing.Iterable[BaseRoute]) -> Routes:
        """
        routes + self
        """
        return Routes[ViewType]() << routes << self

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, typing.Sequence):
            return NotImplemented
        return len(o) == len(self) and all(
            zip(self, o) | F(map, FF(lambda r, r_: r == r_))
        )

    def http_middleware(self, middleware: MiddlewareType) -> MiddlewareType:
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
        if len(self) > 0:
            raise RuntimeError("Can not append middleware after route")

        self._http_middlewares.append(middleware)
        return middleware

    def socket_middleware(self, middleware: MiddlewareType) -> MiddlewareType:
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
        if len(self) > 0:
            raise RuntimeError("Can not append middleware after route")

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


class Router(RouteRegisterMixin[ViewType]):
    def __init__(
        self,
        routes: typing.Iterable[BaseRoute],
        http_middlewares: typing.Sequence[MiddlewareType] = [],
        socket_middlewares: typing.Sequence[MiddlewareType] = [],
    ) -> None:
        self.http_tree = RadixTree[ViewType]()
        self.websocket_tree = RadixTree[ViewType]()

        self.routes_mapping: typing.Dict[str, RouteType] = {}

        self._http_middlewares = list(http_middlewares)
        self._socket_middlewares = list(socket_middlewares)
        self.__lshift__(routes)

    def append(self: Self, route: BaseRoute) -> Self:
        if isinstance(route, HttpRoute):
            route._extend_middlewares(self._http_middlewares)
            radix_tree = self.http_tree
        elif isinstance(route, SocketRoute):
            route._extend_middlewares(self._socket_middlewares)
            radix_tree = self.websocket_tree
        else:
            raise TypeError(
                f"Need type: `HttpRoute` or `SocketRoute`, but got type: {type(route)}"
            )

        if route.path == "":
            route.path = "/"

        if route.name in self.routes_mapping:
            raise ValueError(f"Duplicate route name: {route.name}")

        radix_tree.append(route.path, route.endpoint)
        path_format, path_convertors = compile_path(route.path)

        if route.name:  # name not in ("", None)
            self.routes_mapping[route.name] = (
                path_format,
                path_convertors,
                route.endpoint,
            )

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

        route, params = radix_tree.search(path)

        if route is None or params is None:
            raise NoMatchFound(path)

        _, param_convertors, endpoint = route

        return {
            name: param_convertors[name].to_python(value)
            for name, value in params.items()
            if name in param_convertors
        }, endpoint

    def url_for(
        self,
        name: str,
        path_params: typing.Mapping[str, typing.Any] = {},
    ) -> str:
        if name not in self.routes_mapping:
            raise NoRouteFound(f"No route with name '{name}' exists")

        path_format, path_convertors, _ = self.routes_mapping[name]

        return path_format.format_map(
            {
                name: path_convertors[name].to_string(value)
                for name, value in path_params.items()
            }
        )
