from __future__ import annotations

import operator
import typing
from dataclasses import dataclass
from functools import reduce

from ..parameters import auto_params, update_wrapper

T_Endpoint = typing.Callable[..., typing.Awaitable[typing.Any]]
_RouteSelf = typing.TypeVar("_RouteSelf", bound="BaseRoute")


@dataclass
class BaseRoute:
    path: str
    endpoint: typing.Callable[..., typing.Awaitable[typing.Any]]
    name: typing.Optional[str] = ""

    def extend_middlewares(self, routes: typing.Iterable[BaseRoute]) -> None:
        raise NotImplementedError()

    def _extend_middlewares(
        self, middlewares: typing.Iterable[typing.Callable[[T_Endpoint], T_Endpoint]]
    ) -> None:
        reduce(operator.matmul, middlewares, self)

    def __matmul__(
        self: _RouteSelf, decorator: typing.Callable[[T_Endpoint], T_Endpoint]
    ) -> _RouteSelf:
        endpoint = self.endpoint
        if hasattr(endpoint, "__methods__"):
            for method in map(str.lower, endpoint.__methods__):  # type: ignore
                old_callback = getattr(endpoint, method)
                new_callback = decorator(old_callback)
                if new_callback is not old_callback:
                    update_wrapper(new_callback, old_callback)
                    new_callback = auto_params(new_callback)
                setattr(endpoint, method, new_callback)
        else:
            old_callback = endpoint
            new_callback = decorator(old_callback)
            if new_callback is not old_callback:
                update_wrapper(new_callback, old_callback)
                new_callback = auto_params(new_callback)
            self.endpoint = new_callback
        return self

    def __post_init__(self) -> None:
        assert (
            self.path.startswith("/") or self.path == ""
        ), "Route path must start with '/'"
        if self.name == "":
            self.name = self.endpoint.__name__
        self.endpoint = auto_params(self.endpoint)


@dataclass
class HttpRoute(BaseRoute):
    summary: typing.Optional[str] = None
    description: typing.Optional[str] = None
    tags: typing.Optional[typing.Iterable[str]] = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.summary:
            setattr(self.endpoint, "__summary__", self.summary)

        if self.description:
            setattr(self.endpoint, "__description__", self.description)

        if self.tags:
            setattr(self.endpoint, "__tags__", list(self.tags))

    def extend_middlewares(self, routes: typing.Iterable[BaseRoute]) -> None:
        self._extend_middlewares(getattr(routes, "_http_middlewares", []))


@dataclass
class SocketRoute(BaseRoute):
    def extend_middlewares(self, routes: typing.Iterable[BaseRoute]) -> None:
        self._extend_middlewares(getattr(routes, "_socket_middlewares", []))
