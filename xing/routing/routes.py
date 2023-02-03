from __future__ import annotations

import operator
import typing
from dataclasses import dataclass
from functools import reduce

from typing_extensions import Self

from ..parameters import update_wrapper
from .typing import MiddlewareType, ViewType


@dataclass
class BaseRoute(typing.Generic[ViewType]):
    path: str
    endpoint: ViewType
    name: typing.Optional[str] = ""

    _auto_params: typing.ClassVar

    def extend_middlewares(self, routes: typing.Iterable[BaseRoute[ViewType]]) -> None:
        raise NotImplementedError

    def _extend_middlewares(
        self,
        middlewares: typing.Iterable[MiddlewareType[ViewType]],
    ) -> None:
        reduce(operator.matmul, middlewares, self)

    def __matmul__(self: Self, middleware: MiddlewareType[ViewType]) -> Self:
        endpoint = self.endpoint
        if hasattr(endpoint, "__methods__"):
            for method in map(str.lower, endpoint.__methods__):  # type: ignore
                old_callback = getattr(endpoint, method)
                new_callback = middleware(old_callback)
                if new_callback is not old_callback:
                    update_wrapper(new_callback, old_callback)
                    new_callback = self._auto_params(new_callback)
                setattr(endpoint, method, new_callback)
        else:
            old_callback = endpoint
            new_callback = middleware(old_callback)
            if new_callback is not old_callback:
                update_wrapper(new_callback, old_callback)
                new_callback = self._auto_params(new_callback)
            self.endpoint = new_callback
        return self

    def __post_init__(self) -> None:
        assert (
            self.path.startswith("/") or self.path == ""
        ), "Route path must start with '/'"
        if self.name == "":
            self.name = self.endpoint.__name__
        self.endpoint = self._auto_params(self.endpoint)


@dataclass
class HttpRoute(BaseRoute[ViewType], typing.Generic[ViewType]):
    summary: typing.Optional[str] = None
    description: typing.Optional[str] = None
    tags: typing.Optional[typing.Iterable[str]] = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.summary:
            setattr(self.endpoint, "__docs_summary__", self.summary)

        if self.description:
            setattr(self.endpoint, "__docs_description__", self.description)

        if self.tags:
            setattr(self.endpoint, "__docs_tags__", list(self.tags))

    def extend_middlewares(self, routes: typing.Iterable[BaseRoute[ViewType]]) -> None:
        self._extend_middlewares(getattr(routes, "_http_middlewares", []))


@dataclass
class SocketRoute(BaseRoute[ViewType], typing.Generic[ViewType]):
    def extend_middlewares(self, routes: typing.Iterable[BaseRoute[ViewType]]) -> None:
        self._extend_middlewares(getattr(routes, "_socket_middlewares", []))
