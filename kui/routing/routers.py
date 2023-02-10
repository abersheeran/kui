from __future__ import annotations

import abc
import operator
import typing
from copy import deepcopy
from functools import reduce

from baize.routing import compile_path
from baize.utils import cached_property
from typing_extensions import Literal, Self, get_args, get_origin

from ..utils import FF, F, safe_issubclass
from .routes import BaseRoute, HttpRoute, SocketRoute
from .tree import RadixTree, RouteType
from .typing import AsyncViewType, MiddlewareType, SyncViewType, ViewType


class NoMatchFound(Exception):
    """
    Raised by `.search(path)` if no matching route exists.
    """


class NoRouteFound(Exception):
    """
    Raised by `.url_for(name, **path_params)` if no matching route exists.
    """


class HttpRegister(typing.Generic[ViewType]):
    def __init__(self, routes: RouteRegisterMixin[ViewType]) -> None:
        self.__routes = routes

    @cached_property
    def _required_method(self) -> typing.Callable[[str], MiddlewareType[ViewType]]:
        for origin_base in self.__orig_bases__:  # type: ignore
            if safe_issubclass(get_origin(origin_base), HttpRegister):
                generic_type = get_args(origin_base)[0]
                if generic_type == AsyncViewType:
                    from ..asgi.views import required_method
                elif generic_type == SyncViewType:
                    from ..wsgi.views import required_method
                else:
                    raise RuntimeError
                return required_method  # type: ignore
        raise RuntimeError(f"{self.__class__.__name__} must be used with ViewType")

    @cached_property
    def _http_route(self) -> typing.Type[HttpRoute[ViewType]]:
        for origin_base in self.__orig_bases__:  # type: ignore
            if safe_issubclass(get_origin(origin_base), HttpRegister):
                generic_type = get_args(origin_base)[0]
                if generic_type == AsyncViewType:
                    from ..asgi.routing import HttpRoute  # type: ignore
                elif generic_type == SyncViewType:
                    from ..wsgi.routing import HttpRoute  # type: ignore
                else:
                    raise RuntimeError
                return HttpRoute  # type: ignore
        raise RuntimeError(f"{self.__class__.__name__} must be used with ViewType")

    def _register_with_method(
        self,
        method: str,
        path: str,
        *,
        name: typing.Optional[str] = "",
        middlewares: typing.Iterable[typing.Callable[[ViewType], ViewType]] = [],
        summary: str | None = None,
        description: str | None = None,
        tags: typing.Iterable[str] | None = None,
    ) -> typing.Callable[[ViewType], ViewType]:
        """
        if method == "any", all request method would be allowed.
        """

        def register(endpoint: ViewType) -> ViewType:
            route: HttpRoute[ViewType] = reduce(
                operator.matmul,
                middlewares,
                self._http_route(path, endpoint, name, summary, description, tags),
            )
            if method != "any":
                route = route @ self._required_method(method.upper())

            _ = self.__routes << route
            return endpoint

        return register

    def __call__(
        self,
        path: str,
        *,
        name: typing.Optional[str] = "",
        middlewares: typing.Iterable[typing.Callable[[ViewType], ViewType]] = [],
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
        middlewares: typing.Iterable[typing.Callable[[ViewType], ViewType]] = [],
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
        middlewares: typing.Iterable[typing.Callable[[ViewType], ViewType]] = [],
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
        middlewares: typing.Iterable[typing.Callable[[ViewType], ViewType]] = [],
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
        middlewares: typing.Iterable[typing.Callable[[ViewType], ViewType]] = [],
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
        middlewares: typing.Iterable[typing.Callable[[ViewType], ViewType]] = [],
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
    @abc.abstractmethod
    def append(self: Self, route: BaseRoute[ViewType]) -> Self:
        raise NotImplementedError

    def __lshift__(
        self: Self,
        other: typing.Union[BaseRoute[ViewType], typing.Iterable[BaseRoute[ViewType]]],
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
        for origin_base in self.__orig_bases__:  # type: ignore
            if safe_issubclass(get_origin(origin_base), RouteRegisterMixin):
                view_type = get_args(origin_base)[0]

                class _HttpRegister(HttpRegister[view_type]):  # type: ignore
                    pass

                return _HttpRegister(self)
        raise RuntimeError

    def websocket(
        self,
        path: str,
        *,
        name: typing.Optional[str] = "",
        middlewares: typing.Iterable[typing.Callable[[ViewType], ViewType]] = [],
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


class Routes(
    typing.Sequence[BaseRoute[ViewType]],
    RouteRegisterMixin[ViewType],
    typing.Generic[ViewType],
):
    def __init__(
        self,
        *iterable: typing.Union[
            BaseRoute[ViewType], typing.Iterable[BaseRoute[ViewType]]
        ],
        namespace: str = "",
        tags: typing.Iterable[str] | None = None,
        http_middlewares: typing.Sequence[MiddlewareType[ViewType]] = [],
        socket_middlewares: typing.Sequence[typing.Any] = [],
    ) -> None:
        self.namespace = namespace
        self._list: typing.List[BaseRoute[ViewType]] = []
        self._http_middlewares = list(http_middlewares)
        self._http_middlewares.append(
            lambda endpoint: (
                setattr(  # type: ignore
                    endpoint,
                    "__docs_tags__",
                    list(getattr(endpoint, "__docs_tags__", [])) + list(tags or []),
                )
                or endpoint
            )
        )
        self._socket_middlewares = list(socket_middlewares)
        for route in iterable:
            _ = self << route

    @typing.overload
    def __getitem__(self, index: int) -> BaseRoute[ViewType]:
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

    def append(self: Self, route: BaseRoute[ViewType]) -> Self:
        self._list.append(route)
        return self

    def __rfloordiv__(self: Self, other: str) -> Self:
        """
        other // self
        """
        if not isinstance(other, str):
            return NotImplemented

        return Prefix(other) // self

    def __add__(self, routes: typing.Iterable[BaseRoute[ViewType]]) -> Routes:
        """
        self + routes
        """
        return Routes[ViewType]() << self << routes

    def __radd__(self, routes: typing.Iterable[BaseRoute[ViewType]]) -> Routes:
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


class Router(RouteRegisterMixin[ViewType], typing.Generic[ViewType]):
    def __init__(
        self,
        routes: typing.Iterable[BaseRoute[ViewType]],
        http_middlewares: typing.Sequence[MiddlewareType[ViewType]] = [],
        socket_middlewares: typing.Sequence[MiddlewareType[ViewType]] = [],
    ) -> None:
        self.http_tree = RadixTree[ViewType]()
        self.websocket_tree = RadixTree[ViewType]()

        self.routes_mapping: typing.Dict[str, RouteType] = {}

        self._http_middlewares = list(http_middlewares)
        self._socket_middlewares = list(socket_middlewares)
        self.__lshift__(routes)

    def append(self: Self, route: BaseRoute[ViewType]) -> Self:
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
