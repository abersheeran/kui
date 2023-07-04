from __future__ import annotations

import typing

from typing_extensions import Self

from ...routing import BaseRoute, HttpRoute, Routes
from ..typing import ViewType


class MultimethodRoutes(Routes[ViewType], typing.Generic[ViewType]):
    def __init__(
        self,
        *iterable: typing.Union[
            BaseRoute[ViewType], typing.Iterable[BaseRoute[ViewType]]
        ],
        base_class: type,
        namespace: str = "",
        tags: typing.Iterable[str] | None = None,
        http_middlewares: typing.Sequence[typing.Any] = [],
        socket_middlewares: typing.Sequence[typing.Any] = [],
    ) -> None:
        self.base_class = base_class
        super().__init__(
            *iterable,
            namespace=namespace,
            tags=tags,
            http_middlewares=http_middlewares,
            socket_middlewares=socket_middlewares,
        )

    def append(self: Self, route: BaseRoute[ViewType]) -> Self:
        if hasattr(route.endpoint, "__methods__"):
            raise TypeError("MultimethodRoutes not allow use class-base view.")

        if not isinstance(route, HttpRoute):
            self._list.append(route)
            return self

        try:
            r = next(
                filter(
                    lambda r: isinstance(r, HttpRoute) and r.path == route.path,
                    self._list,
                )
            )
            if not hasattr(route.endpoint, "__method__") or not (
                hasattr(r.endpoint, "__method__") or hasattr(r.endpoint, "__methods__")
            ):
                raise RuntimeError(
                    f"Routing '{route.path}' conflict, can be resolved by restricting the request method."
                )
        except StopIteration:
            self._list.append(route)
        else:
            if hasattr(r.endpoint, "__methods__"):
                endpoint = type(
                    r.endpoint.__name__,
                    (self.base_class,),
                    {
                        **{
                            method.lower(): getattr(r.endpoint, method.lower())
                            for method in r.endpoint.__methods__
                        },
                        route.endpoint.__method__.lower(): staticmethod(route.endpoint),
                    },
                )
            else:
                endpoint = type(
                    "_MultimethodEndpoint",
                    (self.base_class, _MultiMethodView),
                    {
                        r.endpoint.__method__.lower(): staticmethod(r.endpoint),  # type: ignore
                        route.endpoint.__method__.lower(): staticmethod(route.endpoint),
                    },
                )
            # replacing route inplace
            r.endpoint = typing.cast(ViewType, endpoint)
        return self


class _MultiMethodView:
    """
    Just as a mark
    """


def is_multimethod_view(cls: type) -> bool:
    return isinstance(cls, type) and issubclass(cls, _MultiMethodView)
